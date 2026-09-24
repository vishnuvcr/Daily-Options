from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from research.cost_model import OptionCostModel
from research.phase10_contracts import index_option_lot_size


SYMBOLS = ("NIFTY", "BANKNIFTY")
ENTRY_TIMES = ("09:45:00", "10:00:00")
EXPIRIES = ("WEEK", "MONTH")
THRESHOLDS = (0.75, 1.25)
WIDTHS = (1, 2)
HOLDS = (15, 30, 45, 60)
RISK_PROFILES = (
    {"stop_pct": 0.30, "target_pct": 0.60},
    {"stop_pct": 0.50, "target_pct": 1.00},
)


@dataclass(frozen=True)
class Variant:
    threshold: float
    entry_time: str
    expiry_type: str
    width_steps: int
    hold_minutes: int
    risk_id: int

    @property
    def key(self) -> str:
        return (
            f"gap{self.threshold}|{self.entry_time}|{self.expiry_type}|"
            f"w{self.width_steps}|h{self.hold_minutes}|r{self.risk_id}"
        )


def variant_grid() -> list[Variant]:
    return [
        Variant(th, entry, expiry, width, hold, risk)
        for th in THRESHOLDS
        for entry in ENTRY_TIMES
        for expiry in EXPIRIES
        for width in WIDTHS
        for hold in HOLDS
        for risk in range(len(RISK_PROFILES))
    ]


def idx_glob(root: Path) -> str:
    return (root / "index" / "*.parquet").as_posix()


def opt_glob(root: Path, symbol: str) -> str:
    return (root / "options" / symbol / "*.parquet").as_posix()


def classify_expiries(root: Path) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    con = duckdb.connect()
    for symbol in SYMBOLS:
        glob = opt_glob(root, symbol)
        rows = con.execute(
            f"""
            SELECT DISTINCT CAST(expiry AS DATE) AS expiry
            FROM read_parquet('{glob}', union_by_name=true)
            WHERE expiry IS NOT NULL
            ORDER BY expiry
            """
        ).fetchall()
        dates = [pd.Timestamp(x[0]).date() for x in rows]
        by_month: dict[tuple[int, int], list] = {}
        for d in dates:
            by_month.setdefault((d.year, d.month), []).append(d)
        mset = {max(v) for v in by_month.values()}
        out[symbol] = {
            d.isoformat(): ("MONTH" if d in mset else "WEEK")
            for d in dates
        }
    con.close()
    return out


def load_indices(root: Path) -> pd.DataFrame:
    con = duckdb.connect()
    df = con.execute(
        f"""
        SELECT CAST(timestamp AS TIMESTAMPTZ) AS timestamp,
               symbol,
               CAST(open AS DOUBLE) AS open,
               CAST(high AS DOUBLE) AS high,
               CAST(low AS DOUBLE) AS low,
               CAST(close AS DOUBLE) AS close
        FROM read_parquet('{idx_glob(root)}', union_by_name=true)
        WHERE symbol IN ('NIFTY','BANKNIFTY') AND close > 0
        ORDER BY timestamp, symbol
        """
    ).df()
    con.close()
    if df.empty:
        return df

    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df["local_ts"] = df["timestamp"].dt.tz_convert("Asia/Kolkata").dt.tz_localize(None)
    df["trade_date"] = df["local_ts"].dt.date
    pivot = (
        df.pivot_table(index="local_ts", columns="symbol", values="close", aggfunc="last")
        .dropna(subset=list(SYMBOLS))
        .sort_index()
    )
    for symbol in SYMBOLS:
        ret1 = pivot[symbol].pct_change()
        vol60 = ret1.rolling(60, min_periods=60).std()
        pivot[f"{symbol}_ret5"] = pivot[symbol].pct_change(5)
        pivot[f"{symbol}_ret15"] = pivot[symbol].pct_change(15)
        pivot[f"{symbol}_z5"] = pivot[f"{symbol}_ret5"] / (vol60 * np.sqrt(5)).replace(0, np.nan)
    gap = (pivot["NIFTY_z5"].abs() - pivot["BANKNIFTY_z5"].abs())
    pivot["leader"] = np.where(gap >= 0, "NIFTY", "BANKNIFTY")
    pivot["leader_z"] = np.where(pivot["leader"].eq("NIFTY"), pivot["NIFTY_z5"], pivot["BANKNIFTY_z5"])
    pivot["other_z"] = np.where(pivot["leader"].eq("NIFTY"), pivot["BANKNIFTY_z5"], pivot["NIFTY_z5"])
    pivot["strength_gap"] = pivot["leader_z"].abs() - pivot["other_z"].abs()
    pivot["direction"] = np.where(pivot["leader_z"] > 0, "CALL", "PUT")
    local_times = pivot.index.strftime("%H:%M:%S")
    pivot = pivot.loc[local_times between("09:30:00","12:30:00") if False else local_times]
    pivot = pivot[(pivot.index.strftime("%H:%M:%S") >= "09:30:00") & (pivot.index.strftime("%H:%M:%S") <= "12:30:00")].copy()
    pivot["trade_date"] = pivot.index.date
    return pivot.reset_index(names="local_ts")


def build_signals(indexes: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for v in variant_grid():
        x = indexes.loc[
            (indexes.local_ts.dt.strftime("%H:%M:%S") >= v.entry_time)
            & (indexes.strength_gap >= v.threshold)
            & (indexes.leader_z.abs() >= v.threshold)
        ].copy()
        if x.empty:
            continue
        x = x.sort_values(["trade_date","local_ts"]).drop_duplicates("trade_date", keep="first")
        x["entry_anchor"] = x["local_ts"] + pd.Timedelta(minutes=1)
        x["variant_id"] = v.key
        x["expiry_type_requested"] = v.expiry_type
        x["width_steps"] = v.width_steps
        x["hold_minutes"] = v.hold_minutes
        x["risk_id"] = v.risk_id
        rows.append(
            x[
                ["variant_id","trade_date","local_ts","entry_anchor","leader",
                 "leader_z","strength_gap","direction",
                 "expiry_type_requested","width_steps","hold_minutes","risk_id"]
            ]
        )
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def select_entries(
    signals: pd.DataFrame,
    root: Path,
    expiry_map: dict[str, dict[str, str]],
) -> pd.DataFrame:
    if signals.empty:
        return pd.DataFrame()

    con = duckdb.connect()
    con.register("signals_df", signals)
    out_rows = []

    for symbol in SYMBOLS:
        symbol_signals = signals[signals["leader"].eq(symbol)].copy()
        if symbol_signals.empty:
            continue
        con.unregister("signals_df")
        con.register("signals_df", symbol_signals)
        glob = opt_glob(root, symbol)

        expiry_rows = con.execute(
            f"SELECT DISTINCT CAST(expiry AS DATE) AS expiry "
            f"FROM read_parquet('{glob}', union_by_name=true) WHERE expiry IS NOT NULL ORDER BY expiry"
        ).fetchall()
        exp_dates = [pd.Timestamp(r[0]).date() for r in expiry_rows]

        allowed_expr = []
        for d in exp_dates:
            if expiry_map[symbol][d.isoformat()] in EXPIRIES:
                allowed_expr.append(d.isoformat())
        if not allowed_expr:
            continue

        # Select the first expiry of the requested classification strictly after the signal date.
        candidates = pd.DataFrame({"expiry": pd.to_datetime(allowed_expr).date})
        con.register("expiry_df", candidates)

        sql = f"""
        WITH chosen AS (
          SELECT
            s.*,
            e.expiry,
            ROW_NUMBER() OVER (
              PARTITION BY s.variant_id, s.trade_date
              ORDER BY e.expiry
            ) AS erank
          FROM signals_df s
          JOIN expiry_df e
            ON e.expiry > s.trade_date
           AND e.expiry <= s.trade_date + INTERVAL 35 DAY
           AND e.expiry IN (
             SELECT expiry FROM expiry_df
             WHERE expiry > s.trade_date
               AND expiry <= s.trade_date + INTERVAL 35 DAY
           )
        ),
        typed AS (
          SELECT * FROM chosen
        )
        SELECT * FROM typed WHERE erank=1
        """
        chosen = con.execute(sql).df()
        if chosen.empty:
            continue

        # Re-do expiry selection correctly with requested WEEK/MONTH class.
        chosen["expiry"] = pd.to_datetime(chosen["expiry"]).dt.date
        chosen["expiry_type_actual"] = [
            expiry_map[s][pd.Timestamp(e).date().isoformat()]
            for s, e in zip(chosen["leader"], chosen["expiry"])
        ]
        chosen = chosen.loc[
            chosen["expiry_type_actual"].eq(chosen["expiry_type_requested"])
        ].copy()
        if chosen.empty:
            continue

        con.unregister("chosen_df") if "chosen_df" in [x[0] for x in con.execute("SHOW TABLES").fetchall()] else None
        con.register("chosen_df", chosen)

        direction_option = "CALL" if chosen.empty else None
        # Query a tight window around the signal/entry for the required option direction.
        raw_sql = f"""
        SELECT
          CAST(date AS DATE) AS trade_date,
          CAST(expiry AS DATE) AS expiry,
          option_type,
          CAST(strike AS DOUBLE) AS strike,
          CAST(timestamp AS TIMESTAMPTZ) AS ts,
          CAST(open AS DOUBLE) AS open,
          CAST(high AS DOUBLE) AS high,
          CAST(low AS DOUBLE) AS low,
          CAST(close AS DOUBLE) AS close
        FROM read_parquet('{glob}', union_by_name=true)
        WHERE close > 0
        """
        raw = con.execute(raw_sql).df()
        if raw.empty:
            continue
        raw["ts_local"] = pd.to_datetime(raw["ts"], utc=True).dt.tz_convert("Asia/Kolkata").dt.tz_localize(None)

        rr = []
        for row in chosen.itertuples(index=False):
            q = raw.loc[
                (raw.trade_date == row.trade_date)
                & (raw.expiry == row.expiry)
                & (raw.option_type == row.direction)
                & (raw.ts_local >= row.entry_anchor - pd.Timedelta(minutes=3))
                & (raw.ts_local <= row.entry_anchor + pd.Timedelta(minutes=2))
            ].copy()
            if q.empty:
                continue
            # Candidate strikes nearest the leader spot at entry. Use the strike whose entry-window
            # row is nearest to the index's implied ATM level.
            if row.leader == "NIFTY":
                spot_val = float(indexes.loc[indexes.local_ts.eq(row.entry_anchor), "NIFTY"].iloc[0]) if not indexes.loc[indexes.local_ts.eq(row.entry_anchor), "NIFTY"].empty else np.nan
            else:
                spot_val = float(indexes.loc[indexes.local_ts.eq(row.entry_anchor), "BANKNIFTY"].iloc[0]) if not indexes.loc[indexes.local_ts.eq(row.entry_anchor), "BANKNIFTY"].empty else np.nan
            if not np.isfinite(spot_val):
                # use the closest index value before entry anchor
                ix = indexes.loc[indexes.local_ts.le(row.entry_anchor), row.leader]
                if ix.empty:
                    continue
                spot_val = float(ix.iloc[-1])
            by_strike = []
            for strike, g in q.groupby("strike"):
                g = g.sort_values("ts_local")
                if len(g) >= 2:
                    by_strike.append((abs(float(strike)-spot_val), float(strike), g))
            if not by_strike:
                continue
            by_strike.sort(key=lambda z: z[0])
            atm_strike, atm_df = by_strike[0][1], by_strike[0][2]

            signal_window = atm_df.loc[
                atm_df.ts_local.between(row.local_ts - pd.Timedelta(minutes=3), row.local_ts + pd.Timedelta(minutes=1))
            ]
            entry_window = atm_df.loc[
                atm_df.ts_local.between(row.entry_anchor, row.entry_anchor + pd.Timedelta(minutes=2))
            ]
            if signal_window.empty or entry_window.empty:
                continue
            signal_price = signal_window.sort_values("ts_local").iloc[-1].close
            prev_candidates = signal_window.loc[
                signal_window.ts_local <= row.local_ts - pd.Timedelta(minutes=3)
            ]
            if prev_candidates.empty:
                continue
            prev_price = prev_candidates.sort_values("ts_local").iloc[-1].close
            premium_ret3 = float(signal_price / prev_price - 1.0) if prev_price > 0 else np.nan
            if not np.isfinite(premium_ret3) or premium_ret3 <= 0:
                continue

            # Choose the first common executable timestamp across ATM and wing contract.
            exec_ts = entry_window.sort_values("ts_local").iloc[0].ts_local
            same_ts = q.loc[q.ts_local.eq(exec_ts)].copy()
            strikes = sorted(same_ts.strike.unique(), key=lambda s: abs(float(s)-atm_strike))
            if row.width_steps >= len(strikes):
                continue
            if row.direction == "CALL":
                wings = sorted([float(s) for s in same_ts.strike.unique() if float(s) > atm_strike])
            else:
                wings = sorted([float(s) for s in same_ts.strike.unique() if float(s) < atm_strike], reverse=True)
            if len(wings) < row.width_steps:
                continue
            wing = wings[row.width_steps-1]
            lrow = same_ts.loc[same_ts.strike.eq(atm_strike)]
            srow = same_ts.loc[same_ts.strike.eq(wing)]
            if lrow.empty or srow.empty:
                continue
            long_open = float(lrow.iloc[0].open)
            short_open = float(srow.iloc[0].open)
            debit = long_open - short_open
            if debit <= 0:
                continue
            rr.append({
                "variant_id": row.variant_id,
                "trade_date": row.trade_date,
                "leader": row.leader,
                "direction": row.direction,
                "expiry": row.expiry,
                "expiry_type": row.expiry_type_requested,
                "atm_strike": atm_strike,
                "wing_strike": wing,
                "entry_time": exec_ts,
                "long_entry": long_open,
                "short_entry": short_open,
                "debit": debit,
                "hold_minutes": row.hold_minutes,
                "risk_id": row.risk_id,
                "premium_ret3": premium_ret3,
                "signal_time": row.local_ts,
            })
        if rr:
            out_rows.extend(rr)

    if not out_rows:
        return pd.DataFrame()
    return pd.DataFrame(out_rows)


def simulate(entries: pd.DataFrame, root: Path, out_dir: Path, slippage: float) -> pd.DataFrame:
    if entries.empty:
        return pd.DataFrame()
    cm = OptionCostModel()
    results = []
    con = duckdb.connect()

    for symbol in SYMBOLS:
        es = entries.loc[entries.leader.eq(symbol)].copy()
        if es.empty:
            continue
        con.register("entries_df", es)
        glob = opt_glob(root, symbol)
        raw = con.execute(
            f"""
            SELECT CAST(date AS DATE) AS trade_date, CAST(expiry AS DATE) AS expiry,
                   option_type, CAST(strike AS DOUBLE) AS strike,
                   CAST(timestamp AS TIMESTAMPTZ) AS ts,
                   CAST(open AS DOUBLE) AS open, CAST(high AS DOUBLE) AS high,
                   CAST(low AS DOUBLE) AS low, CAST(close AS DOUBLE) AS close
            FROM read_parquet('{glob}', union_by_name=true)
            WHERE close > 0
            """
        ).df()
        raw["ts_local"] = pd.to_datetime(raw.ts, utc=True).dt.tz_convert("Asia/Kolkata").dt.tz_localize(None)

        for row in es.itertuples(index=False):
            g = raw.loc[
                (raw.trade_date == row.trade_date)
                & (raw.expiry == row.expiry)
                & (raw.option_type == row.direction)
                & raw.strike.isin([row.atm_strike, row.wing_strike])
                & raw.ts_local.between(row.entry_time, row.entry_time + pd.Timedelta(minutes=row.hold_minutes))
            ].copy()
            if g.empty:
                continue
            pivot = g.pivot_table(index="ts_local", columns="strike", values=["open","high","low","close"], aggfunc="last").sort_index()
            if row.atm_strike not in pivot["close"].columns or row.wing_strike not in pivot["close"].columns:
                continue
            er = pivot.iloc[0]
            entry_debit = float(er[("open", row.atm_strike)] - er[("open", row.wing_strike)])
            if entry_debit <= 0:
                continue
            prof = RISK_PROFILES[int(row.risk_id)]
            stop_level = entry_debit * (1-prof["stop_pct"])
            target_level = entry_debit * (1+prof["target_pct"])
            exit_debit = float(pivot[("close", row.atm_strike)].iloc[-1] - pivot[("close", row.wing_strike)].iloc[-1])
            exit_ts = pivot.index[-1]
            reason = "TIME"

            for ts, bar in pivot.iterrows():
                high = float(bar[("high", row.atm_strike)] - bar[("low", row.wing_strike)])
                low = float(bar[("low", row.atm_strike)] - bar[("high", row.wing_strike)])
                if low <= stop_level:
                    exit_debit = stop_level
                    exit_ts = ts
                    reason = "STOP"
                    break
                if high >= target_level:
                    exit_debit = target_level
                    exit_ts = ts
                    reason = "TARGET"
                    break

            lot = index_option_lot_size(row.leader, row.expiry)
            net = cm.vertical_debit_spread_net_pnl(
                float(row.long_entry), float(row.short_entry),
                float(row.atm_strike and exit_debit + 0.0),
                float(row.wing_strike and 0.0),
                lot_size=lot,
                qty=1,
                slippage_points=slippage,
            )
            # Reconstruct exit leg premiums from the path rather than the debit alone.
            last = pivot.loc[pivot.index == exit_ts]
            if last.empty:
                last = pivot.iloc[[-1]]
            long_exit = float(last[("close", row.atm_strike)].iloc[0])
            short_exit = float(last[("close", row.wing_strike)].iloc[0])
            net = cm.vertical_debit_spread_net_pnl(
                float(row.long_entry), float(row.short_entry),
                long_exit, short_exit, lot_size=lot, qty=1,
                slippage_points=slippage,
            )
            results.append({
                "variant_id": row.variant_id, "trade_date": row.trade_date,
                "leader": row.leader, "direction": row.direction,
                "entry_time": row.entry_time, "exit_time": exit_ts,
                "expiry": row.expiry, "atm_strike": row.atm_strike,
                "wing_strike": row.wing_strike, "entry_debit": entry_debit,
                "exit_debit": long_exit-short_exit, "net_pnl": net,
                "exit_reason": reason, "premium_ret3": row.premium_ret3,
            })
        con.unregister("entries_df")

    con.close()
    out = pd.DataFrame(results)
    out_dir.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_dir/"phase10_trades.csv",index=False)
    return out


def leaderboard(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame()
    rows=[]
    for variant,g in trades.groupby("variant_id",sort=False):
        daily=g.groupby("trade_date").net_pnl.sum()
        wins=g.loc[g.net_pnl>0,"net_pnl"].sum()
        losses=-g.loc[g.net_pnl<0,"net_pnl"].sum()
        rows.append({
            "variant_id":variant,"trades":len(g),"active_days":int(daily.size),
            "mean_active_day_net":float(daily.mean()),
            "win_rate":float((g.net_pnl>0).mean()),
            "positive_day_rate":float((daily>0).mean()),
            "profit_factor":float(wins/losses) if losses>0 else 999.0,
            "max_drawdown":float((daily.cumsum()-daily.cumsum().cummax()).min()),
            "total_net":float(g.net_pnl.sum())
        })
    return pd.DataFrame(rows).sort_values(["mean_active_day_net","profit_factor"],ascending=[False,False]).reset_index(drop=True)


def walk_forward(trades: pd.DataFrame) -> tuple[pd.DataFrame,dict]:
    if trades.empty: return pd.DataFrame(),{"gate":"NO_TRADES"}
    x=trades.copy(); x["trade_date"]=pd.to_datetime(x["trade_date"]).dt.date
    dates=sorted(x.trade_date.unique()); tr,va,emb,te,step=180,60,5,60,60; rows=[]; start=0
    while start+tr+va+emb+te<=len(dates):
        train=set(dates[start:start+tr]); valid=set(dates[start+tr:start+tr+va]); test=set(dates[start+tr+va+emb:start+tr+va+emb+te])
        a=x[x.trade_date.isin(train)]; b=x[x.trade_date.isin(valid)]; c=x[x.trade_date.isin(test)]
        scores=[]
        for v,g in a.groupby("variant_id"):
            if len(g)>=8: scores.append((v,float(g.groupby("trade_date").net_pnl.sum().mean())))
        scores.sort(key=lambda z:z[1],reverse=True); vs=[]
        for v,_ in scores[:12]:
            g=b[b.variant_id.eq(v)]
            if len(g)>=5: vs.append((v,float(g.groupby("trade_date").net_pnl.sum().mean())))
        if not vs: start+=step; continue
        vs.sort(key=lambda z:z[1],reverse=True); sel=vs[0][0]; g=c[c.variant_id.eq(sel)]
        if g.empty: start+=step; continue
        d=g.groupby("trade_date").net_pnl.sum()
        rows.append({"test_start":str(min(test)),"test_end":str(max(test)),"selected_variant":sel,"validation_mean":vs[0][1],"test_mean":float(d.mean()),"test_median":float(d.median()),"positive_day_rate":float((d>0).mean()),"trade_days":int(d.size)})
        start+=step
    wf=pd.DataFrame(rows)
    if wf.empty: return wf,{"walk_forward_windows":0,"positive_test_windows":0,"target_windows":0,"mean_test_window_net":None,"gate":"FAIL_PRELIMINARY"}
    return wf,{"walk_forward_windows":int(len(wf)),"positive_test_windows":int((wf.test_mean>0).sum()),"target_windows":int((wf.test_mean>=1000).sum()),"mean_test_window_net":float(wf.test_mean.mean()),"median_test_window_net":float(wf.test_mean.median()),"gate":"PASS_PRELIMINARY" if wf.test_mean.mean()>0 and (wf.test_mean>=1000).any() else "FAIL_PRELIMINARY"}


def data_gate(root: Path) -> dict:
    con=duckdb.connect()
    out={}
    for symbol in SYMBOLS:
        idx=con.execute(
            f"SELECT COUNT(*) n, MIN(timestamp) tmin, MAX(timestamp) tmax, COUNT(DISTINCT trading_day) days FROM read_parquet('{root / 'index' / (symbol+'.parquet')}')"
        ).fetchone()
        out[symbol]={"rows":int(idx[0]),"timestamp_min":str(idx[1]),"timestamp_max":str(idx[2]),"days":int(idx[3])}
    con.close()
    return {"symbols":out,"gate":"PASS" if all(v["rows"]>50000 and v["days"]>300 for v in out.values()) else "FAIL"}


def run(root: Path, out: Path, slippage: float) -> dict:
    out.mkdir(parents=True,exist_ok=True)
    gate=data_gate(root); (out/"phase10_data_gate.json").write_text(json.dumps(gate,indent=2))
    if gate["gate"]!="PASS": return {"stage":"DATA_GATE","gate":"FAIL","data_gate":gate}
    indexes=load_indices(root); expiry_map=classify_expiries(root)
    signals=build_signals(indexes); signals.to_csv(out/"phase10_signals.csv",index=False)
    entries=select_entries(signals,root,expiry_map); entries.to_csv(out/"phase10_entries.csv",index=False)
    trades=simulate(entries,root,out,slippage)
    board=leaderboard(trades); board.to_csv(out/"phase10_leaderboard.csv",index=False)
    wf,wfs=walk_forward(trades); wf.to_csv(out/"phase10_walk_forward.csv",index=False)
    summary={"variants":len(variant_grid()),"signals":len(signals),"entries":len(entries),"trades":len(trades),"target_qualified_prelim":int((board.mean_active_day_net>=1000).sum()) if not board.empty else 0,"best":board.iloc[0].to_dict() if not board.empty else None,"walk_forward":wfs,"slippage_points":slippage}
    (out/"phase10_summary.json").write_text(json.dumps(summary,indent=2,default=str))
    print(json.dumps(summary,indent=2,default=str)); return summary


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--data",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--slippage",type=float,default=0.20)
    a=ap.parse_args(); run(a.data,a.out,a.slippage)


if __name__=="__main__":
    main()
