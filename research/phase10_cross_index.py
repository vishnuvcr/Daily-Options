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


def idx_path(root: Path, symbol: str) -> str:
    return (root / "index" / f"{symbol}.parquet").as_posix()


def opt_glob(root: Path, symbol: str) -> str:
    return (root / "options" / symbol / "*.parquet").as_posix()


def classify_expiries(root: Path) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    con = duckdb.connect()
    for symbol in SYMBOLS:
        rows = con.execute(
            f"""
            SELECT DISTINCT CAST(expiry AS DATE) AS expiry
            FROM read_parquet('{opt_glob(root, symbol)}', union_by_name=true)
            WHERE expiry IS NOT NULL
            ORDER BY expiry
            """
        ).fetchall()
        dates = [pd.Timestamp(r[0]).date() for r in rows]
        by_month: dict[tuple[int, int], list] = {}
        for d in dates:
            by_month.setdefault((d.year, d.month), []).append(d)
        monthly = {max(v) for v in by_month.values()}
        result[symbol] = {
            d.isoformat(): ("MONTH" if d in monthly else "WEEK")
            for d in dates
        }
    con.close()
    return result


def load_indices(root: Path) -> pd.DataFrame:
    parts = []
    for symbol in SYMBOLS:
        con = duckdb.connect()
        df = con.execute(
            f"""
            SELECT
                CAST(timestamp AS TIMESTAMP) AS local_ts,
                CAST(trading_day AS DATE) AS trade_date,
                symbol,
                CAST(close AS DOUBLE) AS close
            FROM read_parquet('{idx_path(root, symbol)}', union_by_name=true)
            WHERE close > 0
            ORDER BY local_ts
            """
        ).df()
        con.close()
        parts.append(df)

    if not parts:
        return pd.DataFrame()

    raw = pd.concat(parts, ignore_index=True)
    pivot = (
        raw.pivot_table(index="local_ts", columns="symbol", values="close", aggfunc="last")
        .reindex(columns=SYMBOLS)
        .dropna()
        .sort_index()
    )
    for symbol in SYMBOLS:
        ret1 = pivot[symbol].pct_change()
        sigma5 = ret1.rolling(60, min_periods=60).std()
        pivot[f"{symbol}_ret5"] = pivot[symbol].pct_change(5)
        pivot[f"{symbol}_ret15"] = pivot[symbol].pct_change(15)
        pivot[f"{symbol}_z5"] = pivot[f"{symbol}_ret5"] / (sigma5 * np.sqrt(5)).replace(0, np.nan)

    abs_gap = pivot["NIFTY_z5"].abs() - pivot["BANKNIFTY_z5"].abs()
    pivot["leader"] = np.where(abs_gap >= 0, "NIFTY", "BANKNIFTY")
    pivot["leader_z"] = np.where(
        pivot["leader"].eq("NIFTY"), pivot["NIFTY_z5"], pivot["BANKNIFTY_z5"]
    )
    pivot["other_z"] = np.where(
        pivot["leader"].eq("NIFTY"), pivot["BANKNIFTY_z5"], pivot["NIFTY_z5"]
    )
    pivot["strength_gap"] = pivot["leader_z"].abs() - pivot["other_z"].abs()
    pivot["direction"] = np.where(pivot["leader_z"] > 0, "CALL", "PUT")
    pivot["trade_date"] = pivot.index.date

    local = pivot.index.strftime("%H:%M:%S")
    pivot = pivot.loc[(local >= "09:30:00") & (local <= "12:30:00")].copy()
    return pivot.reset_index()


def build_signals(indexes: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for v in variant_grid():
        x = indexes.loc[
            (indexes["local_ts"].dt.strftime("%H:%M:%S") >= v.entry_time)
            & (indexes["strength_gap"] >= v.threshold)
            & (indexes["leader_z"].abs() >= v.threshold)
        ].copy()
        if x.empty:
            continue
        x = x.sort_values(["trade_date", "local_ts"]).drop_duplicates("trade_date", keep="first")
        x["entry_anchor"] = x["local_ts"] + pd.Timedelta(minutes=1)
        x["variant_id"] = v.key
        x["expiry_type_requested"] = v.expiry_type
        x["width_steps"] = v.width_steps
        x["hold_minutes"] = v.hold_minutes
        x["risk_id"] = v.risk_id
        x["leader_spot"] = np.where(
            x["leader"].eq("NIFTY"), x["NIFTY"], x["BANKNIFTY"]
        )
        rows.append(
            x[
                [
                    "variant_id", "trade_date", "local_ts", "entry_anchor",
                    "leader", "leader_z", "strength_gap", "direction",
                    "leader_spot", "expiry_type_requested", "width_steps",
                    "hold_minutes", "risk_id",
                ]
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

    all_rows = []
    for symbol in SYMBOLS:
        ss = signals.loc[signals["leader"].eq(symbol)].copy()
        if ss.empty:
            continue

        exp_rows = [
            (pd.Timestamp(k).date(), v)
            for k, v in expiry_map[symbol].items()
        ]
        exp_df = pd.DataFrame(exp_rows, columns=["expiry", "expiry_type"])

        con = duckdb.connect()
        con.register("signals_df", ss)
        con.register("expiry_df", exp_df)

        # Pick the nearest future expiry of the requested type.
        chosen = con.execute(
            f"""
            WITH ranked AS (
              SELECT
                s.*,
                e.expiry,
                ROW_NUMBER() OVER (
                  PARTITION BY s.variant_id, s.trade_date
                  ORDER BY e.expiry
                ) AS rn
              FROM signals_df s
              JOIN expiry_df e
                ON e.expiry_type=s.expiry_type_requested
               AND e.expiry > s.trade_date
               AND e.expiry <= s.trade_date + INTERVAL 45 DAY
            )
            SELECT * FROM ranked WHERE rn=1
            """
        ).df()

        if chosen.empty:
            con.close()
            continue

        con.register("chosen_df", chosen)
        raw_sql = f"""
        SELECT
          CAST(trading_day AS DATE) AS trade_date,
          CAST(expiry AS DATE) AS expiry,
          CASE
            WHEN UPPER(CAST(option_type AS VARCHAR)) IN ('CALL','CE') THEN 'CALL'
            ELSE 'PUT'
          END AS option_side,
          CAST(strike AS DOUBLE) AS strike,
          CAST(timestamp AS TIMESTAMP) AS local_ts,
          CAST(close AS DOUBLE) AS close
        FROM read_parquet('{opt_glob(root, symbol)}', union_by_name=true)
        WHERE close > 0
        """
        con.register("raw_df", con.execute(raw_sql).df())  # symbol-level parquet scan remains bounded by one index
        # Use a DuckDB table for only rows that fall in the selected trade windows.
        candidates = con.execute(
            """
            SELECT
              c.variant_id, c.trade_date, c.local_ts AS signal_ts,
              c.entry_anchor, c.direction, c.expiry, c.leader_spot,
              r.option_side, r.strike, r.local_ts, r.close
            FROM chosen_df c
            JOIN raw_df r
              ON r.trade_date=c.trade_date
             AND r.expiry=c.expiry
             AND r.option_side=c.direction
             AND r.local_ts BETWEEN c.local_ts - INTERVAL 4 MINUTE
                                AND c.entry_anchor + INTERVAL 2 MINUTE
            """
        ).df()
        con.close()

        if candidates.empty:
            continue

        candidates = candidates.sort_values(["variant_id","trade_date","strike","local_ts"])
        # Pick ATM strike using the first executable entry quote after entry_anchor.
        for (variant_id, trade_date), g in candidates.groupby(["variant_id","trade_date"], sort=False):
            meta = g.iloc[0]
            entry_after = g.loc[g["local_ts"] >= meta.entry_anchor].copy()
            if entry_after.empty:
                continue
            entry_quotes = entry_after.groupby("strike", as_index=False)["local_ts"].min()
            entry_quotes["distance"] = (entry_quotes["strike"] - float(meta.leader_spot)).abs()
            entry_quotes = entry_quotes.sort_values(["distance","local_ts"])
            atm = float(entry_quotes.iloc[0]["strike"])
            entry_ts = pd.Timestamp(entry_quotes.iloc[0]["local_ts"])

            same = g.loc[g["local_ts"].eq(entry_ts)].copy()
            if same.empty:
                continue

            strikes = sorted(same["strike"].unique())
            if atm not in strikes:
                continue
            if meta.direction == "CALL":
                wings = sorted([float(s) for s in strikes if float(s) > atm])
            else:
                wings = sorted([float(s) for s in strikes if float(s) < atm], reverse=True)

            # Confirmation uses the ATM contract only and must exist before entry.
            atm_q = g.loc[g["strike"].eq(atm)].sort_values("local_ts")
            sig_q = atm_q.loc[atm_q["local_ts"] <= meta.signal_ts]
            prev_q = atm_q.loc[atm_q["local_ts"] <= meta.signal_ts - pd.Timedelta(minutes=3)]
            if sig_q.empty or prev_q.empty:
                continue
            p0 = float(sig_q.iloc[-1]["close"])
            p1 = float(prev_q.iloc[-1]["close"])
            if p1 <= 0:
                continue
            premium_ret3 = p0 / p1 - 1.0
            if not np.isfinite(premium_ret3) or premium_ret3 <= 0:
                continue

            for width_steps in (1, 2):
                if len(wings) < width_steps:
                    continue
                wing = float(wings[width_steps - 1])
                pair = same.loc[same["strike"].isin([atm, wing])]
                long_entry = float(pair.loc[pair["strike"].eq(atm), "close"].iloc[0])
                short_entry = float(pair.loc[pair["strike"].eq(wing), "close"].iloc[0])
                debit = long_entry - short_entry
                if debit <= 0:
                    continue
                all_rows.append(
                    {
                        "variant_id": variant_id,
                        "trade_date": trade_date,
                        "leader": meta.leader,
                        "direction": meta.direction,
                        "expiry": meta.expiry,
                        "entry_time": entry_ts,
                        "atm_strike": atm,
                        "wing_strike": wing,
                        "long_entry": long_entry,
                        "short_entry": short_entry,
                        "debit": debit,
                        "premium_ret3": premium_ret3,
                        "signal_time": meta.signal_ts,
                    }
                )

    return pd.DataFrame(all_rows)


def simulate(entries: pd.DataFrame, root: Path, out_dir: Path, slippage: float) -> pd.DataFrame:
    if entries.empty:
        return pd.DataFrame()

    cm = OptionCostModel()
    rows = []

    for symbol in SYMBOLS:
        es = entries.loc[entries["leader"].eq(symbol)].copy()
        if es.empty:
            continue
        con = duckdb.connect()
        con.register("entries_df", es)
        raw = con.execute(
            f"""
            SELECT
              CAST(trading_day AS DATE) AS trade_date,
              CAST(expiry AS DATE) AS expiry,
              CASE
                WHEN UPPER(CAST(option_type AS VARCHAR)) IN ('CALL','CE') THEN 'CALL'
                ELSE 'PUT'
              END AS option_side,
              CAST(strike AS DOUBLE) AS strike,
              CAST(timestamp AS TIMESTAMP) AS local_ts,
              CAST(open AS DOUBLE) AS open,
              CAST(high AS DOUBLE) AS high,
              CAST(low AS DOUBLE) AS low,
              CAST(close AS DOUBLE) AS close
            FROM read_parquet('{opt_glob(root, symbol)}', union_by_name=true)
            WHERE close > 0
            """
        ).df()
        con.close()

        for row in es.itertuples(index=False):
            g = raw.loc[
                (raw.trade_date == row.trade_date)
                & (raw.expiry == row.expiry)
                & (raw.option_side == row.direction)
                & raw.strike.isin([row.atm_strike, row.wing_strike])
                & raw.local_ts.between(
                    row.entry_time,
                    row.entry_time + pd.Timedelta(minutes=int(row.variant_id.split("|h")[1].split("|")[0]))
                )
            ].copy()
            if g.empty:
                continue

            pivot = (
                g.pivot_table(
                    index="local_ts",
                    columns="strike",
                    values=["open","high","low","close"],
                    aggfunc="last",
                ).sort_index()
            )
            if row.atm_strike not in pivot["close"].columns or row.wing_strike not in pivot["close"].columns:
                continue

            entry = pivot.iloc[0]
            long_entry = float(entry[("open", row.atm_strike)])
            short_entry = float(entry[("open", row.wing_strike)])
            debit = long_entry - short_entry
            if debit <= 0:
                continue

            risk_id = int(row.variant_id.split("|r")[1])
            prof = RISK_PROFILES[risk_id]
            stop_level = debit * (1 - prof["stop_pct"])
            target_level = debit * (1 + prof["target_pct"])
            exit_ts = pivot.index[-1]
            reason = "TIME"

            for ts, bar in pivot.iterrows():
                spread_high = float(bar[("high", row.atm_strike)] - bar[("low", row.wing_strike)])
                spread_low = float(bar[("low", row.atm_strike)] - bar[("high", row.wing_strike)])
                if spread_low <= stop_level:
                    exit_ts = ts
                    reason = "STOP"
                    break
                if spread_high >= target_level:
                    exit_ts = ts
                    reason = "TARGET"
                    break

            last = pivot.loc[pivot.index == exit_ts]
            if last.empty:
                last = pivot.iloc[[-1]]
            long_exit = float(last[("close", row.atm_strike)].iloc[0])
            short_exit = float(last[("close", row.wing_strike)].iloc[0])

            lot = index_option_lot_size(symbol, row.expiry)
            net = cm.vertical_debit_spread_net_pnl(
                long_entry, short_entry, long_exit, short_exit,
                lot_size=lot, qty=1, slippage_points=slippage
            )
            rows.append(
                {
                    "variant_id": row.variant_id,
                    "trade_date": row.trade_date,
                    "leader": row.leader,
                    "direction": row.direction,
                    "entry_time": row.entry_time,
                    "exit_time": exit_ts,
                    "expiry": row.expiry,
                    "atm_strike": row.atm_strike,
                    "wing_strike": row.wing_strike,
                    "entry_debit": debit,
                    "exit_debit": long_exit - short_exit,
                    "premium_ret3": row.premium_ret3,
                    "net_pnl": net,
                    "exit_reason": reason,
                }
            )

    out = pd.DataFrame(rows)
    out_dir.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_dir / "phase10_trades.csv", index=False)
    return out


def leaderboard(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame()
    rows = []
    for variant, g in trades.groupby("variant_id", sort=False):
        daily = g.groupby("trade_date")["net_pnl"].sum()
        wins = g.loc[g.net_pnl > 0, "net_pnl"].sum()
        losses = -g.loc[g.net_pnl < 0, "net_pnl"].sum()
        rows.append(
            {
                "variant_id": variant,
                "trades": len(g),
                "active_days": int(daily.size),
                "mean_active_day_net": float(daily.mean()),
                "win_rate": float((g.net_pnl > 0).mean()),
                "positive_day_rate": float((daily > 0).mean()),
                "profit_factor": float(wins / losses) if losses > 0 else 999.0,
                "max_drawdown": float((daily.cumsum() - daily.cumsum().cummax()).min()),
                "total_net": float(g.net_pnl.sum()),
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["mean_active_day_net", "profit_factor"], ascending=[False, False]
    ).reset_index(drop=True)


def walk_forward(trades: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    if trades.empty:
        return pd.DataFrame(), {"gate": "NO_TRADES"}
    x = trades.copy()
    x["trade_date"] = pd.to_datetime(x["trade_date"]).dt.date
    dates = sorted(x.trade_date.unique())
    tr, va, emb, te, step = 180, 60, 5, 60, 60
    rows = []
    start = 0
    while start + tr + va + emb + te <= len(dates):
        train = set(dates[start : start + tr])
        valid = set(dates[start + tr : start + tr + va])
        test = set(dates[start + tr + va + emb : start + tr + va + emb + te])
        a = x[x.trade_date.isin(train)]
        b = x[x.trade_date.isin(valid)]
        c = x[x.trade_date.isin(test)]
        scores = []
        for v, g in a.groupby("variant_id"):
            if len(g) >= 8:
                scores.append((v, float(g.groupby("trade_date").net_pnl.sum().mean())))
        scores.sort(key=lambda z: z[1], reverse=True)
        vs = []
        for v, _ in scores[:12]:
            g = b[b.variant_id.eq(v)]
            if len(g) >= 5:
                vs.append((v, float(g.groupby("trade_date").net_pnl.sum().mean())))
        if not vs:
            start += step
            continue
        vs.sort(key=lambda z: z[1], reverse=True)
        selected = vs[0][0]
        g = c[c.variant_id.eq(selected)]
        if g.empty:
            start += step
            continue
        d = g.groupby("trade_date").net_pnl.sum()
        rows.append(
            {
                "test_start": str(min(test)),
                "test_end": str(max(test)),
                "selected_variant": selected,
                "validation_mean": vs[0][1],
                "test_mean": float(d.mean()),
                "test_median": float(d.median()),
                "positive_day_rate": float((d > 0).mean()),
                "trade_days": int(d.size),
            }
        )
        start += step
    wf = pd.DataFrame(rows)
    if wf.empty:
        return wf, {
            "walk_forward_windows": 0,
            "positive_test_windows": 0,
            "target_windows": 0,
            "mean_test_window_net": None,
            "gate": "FAIL_PRELIMINARY",
        }
    return wf, {
        "walk_forward_windows": int(len(wf)),
        "positive_test_windows": int((wf.test_mean > 0).sum()),
        "target_windows": int((wf.test_mean >= 1000).sum()),
        "mean_test_window_net": float(wf.test_mean.mean()),
        "median_test_window_net": float(wf.test_mean.median()),
        "gate": "PASS_PRELIMINARY"
        if wf.test_mean.mean() > 0 and (wf.test_mean >= 1000).any()
        else "FAIL_PRELIMINARY",
    }


def data_gate(root: Path) -> dict:
    con = duckdb.connect()
    info = {}
    for symbol in SYMBOLS:
        row = con.execute(
            f"""
            SELECT
                COUNT(*) AS rows,
                MIN(timestamp) AS min_ts,
                MAX(timestamp) AS max_ts,
                COUNT(DISTINCT trading_day) AS days
            FROM read_parquet('{idx_path(root, symbol)}')
            """
        ).fetchone()
        info[symbol] = {
            "rows": int(row[0]),
            "min_ts": str(row[1]),
            "max_ts": str(row[2]),
            "days": int(row[3]),
        }
    con.close()
    gate = all(v["rows"] > 50000 and v["days"] > 300 for v in info.values())
    return {"symbols": info, "gate": "PASS" if gate else "FAIL"}


def run(root: Path, out: Path, slippage: float) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    gate = data_gate(root)
    (out / "phase10_data_gate.json").write_text(json.dumps(gate, indent=2))
    if gate["gate"] != "PASS":
        return {"stage": "DATA_GATE", "gate": "FAIL", "data_gate": gate}

    indexes = load_indices(root)
    expiry_map = classify_expiries(root)
    signals = build_signals(indexes)
    signals.to_csv(out / "phase10_signals.csv", index=False)
    entries = select_entries(signals, root, expiry_map)
    entries.to_csv(out / "phase10_entries.csv", index=False)
    trades = simulate(entries, root, out, slippage)
    board = leaderboard(trades)
    board.to_csv(out / "phase10_leaderboard.csv", index=False)
    wf, wfs = walk_forward(trades)
    wf.to_csv(out / "phase10_walk_forward.csv", index=False)
    summary = {
        "variants": len(variant_grid()),
        "signals": int(len(signals)),
        "entries": int(len(entries)),
        "trades": int(len(trades)),
        "target_qualified_prelim": int((board.mean_active_day_net >= 1000).sum())
        if not board.empty
        else 0,
        "best": board.iloc[0].to_dict() if not board.empty else None,
        "walk_forward": wfs,
        "slippage_points": slippage,
    }
    (out / "phase10_summary.json").write_text(
        json.dumps(summary, indent=2, default=str)
    )
    print(json.dumps(summary, indent=2, default=str))
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--slippage", type=float, default=0.20)
    args = ap.parse_args()
    run(args.data, args.out, args.slippage)


if __name__ == "__main__":
    main()
