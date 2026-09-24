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
from research.phase18_nifty_iron_condor_regime import expiry_files, expiry_for_day, ist_wall

START_DATE = "2021-05-27"
END_DATE = "2026-08-04"
ENTRY_TIMES = ("10:15:00", "13:30:00")
GLOBAL_SETS = ("SP500", "GLOBAL3")
GLOBAL_Z = (0.5, 1.0)
GAP_THRESHOLDS = (0.0025, 0.0050)
MODES = ("CONT", "FADE")
SHORT_OFFSETS = (1, 2)
WING_WIDTHS = (1, 2)
RV_MAX = (1.00, 1.25)
HOLDS = (30, 60)
STOPS = (1.25, 1.50)
TARGET_DECAY = 0.50
MAX_ENTRY_DELAY = 3


@dataclass(frozen=True)
class Variant:
    global_set: str
    global_z: float
    gap_threshold: float
    mode: str
    entry_time: str
    short_offset: int
    wing_width: int
    rv_max: float
    hold: int
    stop: float

    @property
    def key(self) -> str:
        return (
            f"{self.global_set}|gz{self.global_z:.1f}|gap{self.gap_threshold:.4f}|"
            f"{self.mode}|{self.entry_time}|so{self.short_offset}|ww{self.wing_width}|"
            f"rv{self.rv_max:.2f}|h{self.hold}|s{self.stop:.2f}"
        )


def variant_grid() -> list[Variant]:
    return [
        Variant(gs, gz, gap, mode, et, so, ww, rv, hold, stop)
        for gs in GLOBAL_SETS
        for gz in GLOBAL_Z
        for gap in GAP_THRESHOLDS
        for mode in MODES
        for et in ENTRY_TIMES
        for so in SHORT_OFFSETS
        for ww in WING_WIDTHS
        for rv in RV_MAX
        for hold in HOLDS
        for stop in STOPS
    ]


def _load_global_csv(root: Path, name: str) -> pd.DataFrame:
    p = root / f"{name}.csv"
    if not p.exists():
        raise FileNotFoundError(p)
    x = pd.read_csv(p)
    x["date"] = pd.to_datetime(x["Date"], errors="coerce").dt.date
    x["close"] = pd.to_numeric(x["Close"], errors="coerce")
    x = x.dropna(subset=["date", "close"]).sort_values("date").drop_duplicates("date", keep="last")
    x["ret"] = x["close"].pct_change()
    mean = x["ret"].shift(1).rolling(20, min_periods=10).mean()
    std = x["ret"].shift(1).rolling(20, min_periods=10).std()
    x["z"] = (x["ret"] - mean) / std.replace(0, np.nan)
    return x[["date", "z"]].dropna()


def _global_z_before(df: pd.DataFrame, dates: pd.Series) -> pd.Series:
    left = pd.DataFrame({"date": pd.to_datetime(dates)})
    right = df.copy()
    right["date"] = pd.to_datetime(right["date"])
    merged = pd.merge_asof(
        left.sort_values("date"),
        right.sort_values("date"),
        on="date",
        direction="backward",
        allow_exact_matches=False,
    )
    return merged["z"].to_numpy()


def load_market(root: Path) -> pd.DataFrame:
    p = root / "index" / "NIFTY.parquet"
    con = duckdb.connect()
    con.execute("SET TimeZone='Asia/Kolkata'")
    q = f"""
    WITH b AS (
      SELECT "timestamp" ts,
             CAST(trading_day AS DATE) trade_date,
             CAST("close" AS DOUBLE) spot_close
      FROM read_parquet('{p}')
      WHERE CAST(trading_day AS DATE) BETWEEN DATE '{START_DATE}' AND DATE '{END_DATE}'
        AND "close" > 0
    ),
    r AS (
      SELECT *,
             spot_close/LAG(spot_close,1) OVER(PARTITION BY trade_date ORDER BY ts)-1 ret1,
             spot_close/LAG(spot_close,10) OVER(PARTITION BY trade_date ORDER BY ts)-1 ret10
      FROM b
    ),
    v AS (
      SELECT *,
             STDDEV_SAMP(ret1) OVER(
               PARTITION BY trade_date ORDER BY ts
               ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
             ) rv20
      FROM r
    ),
    z AS (
      SELECT *,
             rv20/NULLIF(
               AVG(rv20) OVER(
                 PARTITION BY trade_date ORDER BY ts
                 ROWS BETWEEN 119 PRECEDING AND CURRENT ROW
               ),0
             ) rv_ratio
      FROM v
    ),
    daily0 AS (
      SELECT trade_date,
             arg_min(spot_close, ts) day_open,
             arg_max(spot_close, ts) day_close
      FROM b
      GROUP BY trade_date
    ),
    daily AS (
      SELECT trade_date, day_open, day_close,
             LAG(day_close) OVER(ORDER BY trade_date) prev_close
      FROM daily0
    )
    SELECT z.trade_date,z.ts,z.spot_close,z.ret10,z.rv_ratio,
           d.day_open,d.prev_close
    FROM z JOIN daily d USING(trade_date)
    WHERE z.ret10 IS NOT NULL
      AND z.rv_ratio IS NOT NULL
      AND STRFTIME(z.ts,'%H:%M:%S') IN ('10:15:00','13:30:00')
    ORDER BY z.trade_date,z.ts
    """
    x = con.execute(q).df()
    con.close()
    if x.empty:
        return x
    x["trade_date"] = pd.to_datetime(x["trade_date"]).dt.date
    x["ts"] = ist_wall(x.ts)
    x["gap_return"] = x["day_open"] / x["prev_close"] - 1.0
    return x.dropna(subset=["gap_return"])


def load_global(root: Path) -> dict[str, pd.DataFrame]:
    return {
        "SP500": _load_global_csv(root, "SP500"),
        "NASDAQ": _load_global_csv(root, "NASDAQ"),
        "NIKKEI": _load_global_csv(root, "NIKKEI"),
    }


def build_features(market: pd.DataFrame, global_data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    x = market.copy()
    x["z_sp500"] = _global_z_before(global_data["SP500"], x["trade_date"])
    x["z_nasdaq"] = _global_z_before(global_data["NASDAQ"], x["trade_date"])
    x["z_nikkei"] = _global_z_before(global_data["NIKKEI"], x["trade_date"])
    x["global_global3"] = x[["z_sp500","z_nasdaq","z_nikkei"]].mean(axis=1)
    x["trade_time_ist"] = x["ts"].dt.strftime("%H:%M:%S")
    return x


def load_quotes(root: Path, features: pd.DataFrame) -> pd.DataFrame:
    files = expiry_files(root)
    chosen = {d: expiry_for_day(files, d) for d in features.trade_date.unique()}
    chosen = {d: x for d, x in chosen.items() if x is not None}
    wanted = features[["trade_date","ts"]].drop_duplicates().copy()
    wanted["end_ts"] = wanted["ts"] + pd.Timedelta(minutes=MAX_ENTRY_DELAY)
    con = duckdb.connect()
    con.execute("SET TimeZone='Asia/Kolkata'")
    con.register("wanted", wanted)
    chunks = []
    for expiry_date, path in sorted(set(chosen.values()), key=lambda x: x[0]):
        dates = [d for d,(ed,_) in chosen.items() if ed == expiry_date]
        if not dates:
            continue
        vals = ",".join(f"DATE '{d}'" for d in dates)
        q = f"""
        SELECT "timestamp" ts,
               CAST(trading_day AS DATE) trade_date,
               CAST(strike AS DOUBLE) strike,
               CAST(option_type AS VARCHAR) option_type,
               CAST(open AS DOUBLE) open_px
        FROM read_parquet('{path}')
        JOIN wanted w
          ON CAST(trading_day AS DATE)=w.trade_date
         AND "timestamp">=w.ts AND "timestamp"<=w.end_ts
        WHERE CAST(trading_day AS DATE) IN ({vals})
          AND "close">0
        """
        z = con.execute(q).df()
        if not z.empty:
            z["ts"] = ist_wall(z.ts)
            z["expiry"] = expiry_date
            chunks.append(z)
    con.close()
    return pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()


def build_entries(features: pd.DataFrame, quotes: pd.DataFrame) -> pd.DataFrame:
    if features.empty or quotes.empty:
        return pd.DataFrame()

    rows = []
    for v in variant_grid():
        gcol = "z_sp500" if v.global_set == "SP500" else "global_global3"
        cand = features[
            (features.trade_time_ist == v.entry_time)
            & features[gcol].abs().ge(v.global_z)
            & features.gap_return.abs().ge(v.gap_threshold)
            & features.rv_ratio.le(v.rv_max)
        ].copy()
        if cand.empty:
            continue

        agree = np.sign(cand[gcol]) == np.sign(cand.gap_return)
        cand = cand[agree if v.mode == "CONT" else ~agree]
        if cand.empty:
            continue

        for r in cand.itertuples(index=False):
            # CONT: gap-up -> bullish PE credit spread; gap-down -> bearish CE credit spread.
            # FADE: invert the direction.
            if v.mode == "CONT":
                side = "PE" if r.gap_return > 0 else "CE"
            else:
                side = "CE" if r.gap_return > 0 else "PE"

            q = quotes[
                (quotes.trade_date == r.trade_date)
                & (quotes.ts > r.ts)
                & (quotes.ts <= r.ts + pd.Timedelta(minutes=MAX_ENTRY_DELAY))
                & (quotes.option_type == side)
            ]
            sig = quotes[
                (quotes.trade_date == r.trade_date)
                & (quotes.ts == r.ts)
                & (quotes.option_type == side)
            ]
            if sig.empty:
                continue
            strikes = np.sort(sig.strike.dropna().unique())
            if len(strikes) < 6:
                continue
            atm = int(np.argmin(np.abs(strikes - r.spot_close)))
            si = atm - v.short_offset if side == "PE" else atm + v.short_offset
            wi = si - v.wing_width if side == "PE" else si + v.wing_width
            if not (0 <= si < len(strikes) and 0 <= wi < len(strikes)):
                continue

            short_strike = float(strikes[si])
            wing_strike = float(strikes[wi])
            a = q[q.strike == short_strike]
            b = q[q.strike == wing_strike]
            common = sorted(set(a.ts).intersection(set(b.ts)))
            if not common:
                continue
            entry_ts = common[0]
            ea = a[a.ts == entry_ts].iloc[0]
            eb = b[b.ts == entry_ts].iloc[0]
            credit = float(ea.open_px - eb.open_px)
            if not np.isfinite(credit) or credit <= 0:
                continue

            rows.append({
                "variant_id": v.key,
                "trade_date": r.trade_date,
                "signal_ts": r.ts,
                "entry_ts": entry_ts,
                "entry_delay": float((entry_ts-r.ts).total_seconds()/60),
                "expiry": pd.Timestamp(ea.expiry).date(),
                "side": side,
                "short_strike": short_strike,
                "wing_strike": wing_strike,
                "short_entry": float(ea.open_px),
                "wing_entry": float(eb.open_px),
                "entry_credit": credit,
                "hold": v.hold,
                "stop": v.stop,
            })
    return pd.DataFrame(rows)


def simulate(root: Path, entries: pd.DataFrame, out: Path, slippage: float) -> pd.DataFrame:
    if entries.empty:
        return pd.DataFrame()

    files = dict(expiry_files(root))
    unique = entries.drop_duplicates(
        ["trade_date","entry_ts","expiry","side","short_strike","wing_strike","hold","stop"]
    ).copy()

    all_quotes = []
    con = duckdb.connect()
    con.execute("SET TimeZone='Asia/Kolkata'")
    con.register("legs", unique[["trade_date","entry_ts","expiry","side","short_strike","wing_strike"]].drop_duplicates())

    for expiry_date, path in sorted(files.items()):
        active = int(con.execute("SELECT COUNT(*) FROM legs WHERE expiry=?", [expiry_date]).fetchone()[0])
        if not active:
            continue
        q = f"""
        SELECT "timestamp" ts,
               CAST(trading_day AS DATE) trade_date,
               CAST(strike AS DOUBLE) strike,
               CAST(option_type AS VARCHAR) option_type,
               CAST(high AS DOUBLE) high,
               CAST(low AS DOUBLE) low,
               CAST("close" AS DOUBLE) close_px
        FROM read_parquet('{path}') o
        JOIN legs l
          ON l.expiry = DATE '{expiry_date}'
         AND CAST(o.trading_day AS DATE)=l.trade_date
         AND o.option_type=l.side
         AND CAST(o.strike AS DOUBLE) IN(l.short_strike,l.wing_strike)
         AND o."timestamp">=l.entry_ts
         AND o."timestamp"<=l.entry_ts+INTERVAL '60 minutes'
        WHERE o."close">0
        """
        z = con.execute(q).df()
        if not z.empty:
            z["ts"] = ist_wall(z.ts)
            z["expiry"] = expiry_date
            all_quotes.append(z)
    con.close()

    if not all_quotes:
        return pd.DataFrame()

    win = pd.concat(all_quotes, ignore_index=True)
    win["trade_date"] = pd.to_datetime(win["trade_date"]).dt.date

    outcomes = []
    for rec in unique.itertuples(index=False):
        q = win[
            (win.trade_date == rec.trade_date)
            & (win.expiry == rec.expiry)
            & (win.option_type == rec.side)
            & (win.strike.isin([rec.short_strike, rec.wing_strike]))
            & (win.ts >= rec.entry_ts)
        ]
        if q.empty:
            continue
        a = q[q.strike == rec.short_strike][["ts","high","low","close_px"]].rename(columns={"high":"sh","low":"sl","close_px":"sc"})
        b = q[q.strike == rec.wing_strike][["ts","high","low","close_px"]].rename(columns={"high":"wh","low":"wl","close_px":"wc"})
        m = a.merge(b,on="ts").sort_values("ts")
        if m.empty:
            continue

        mm = m[m.ts <= rec.entry_ts + pd.Timedelta(minutes=rec.hold)]
        if mm.empty:
            continue
        spread_high = mm.sh - mm.wl
        spread_low = mm.sl - mm.wh
        stop_value = rec.entry_credit * rec.stop
        target_value = rec.entry_credit * TARGET_DECAY
        si = np.flatnonzero(spread_high >= stop_value)
        ti = np.flatnonzero(spread_low <= target_value)
        si = int(si[0]) if len(si) else 10**9
        ti = int(ti[0]) if len(ti) else 10**9

        if si <= ti and si < 10**9:
            ix, reason = si, "STOP"
        elif ti < 10**9:
            ix, reason = ti, "TARGET"
        else:
            ix, reason = len(mm) - 1, "TIME"

        ex = mm.iloc[ix]
        net = OptionCostModel().vertical_credit_spread_net_pnl(
            rec.short_entry, rec.wing_entry,
            float(ex.sc), float(ex.wc),
            lot_size=index_option_lot_size("NIFTY", rec.trade_date),
            slippage_points=slippage
        )
        outcomes.append({
            **rec._asdict(),
            "exit_time": ex.ts,
            "reason": reason,
            "net_pnl": net
        })

    outcomes_df = pd.DataFrame(outcomes)
    if outcomes_df.empty:
        return pd.DataFrame()
    join_cols = ["trade_date","entry_ts","expiry","side","short_strike","wing_strike","hold","stop"]
    return entries.merge(outcomes_df, on=join_cols, how="inner")


def leaderboard(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame()
    rows = []
    for vid, g in trades.groupby("variant_id", sort=False):
        d = g.groupby("trade_date").net_pnl.sum()
        pos = g.loc[g.net_pnl > 0, "net_pnl"].sum()
        neg = -g.loc[g.net_pnl < 0, "net_pnl"].sum()
        rows.append({
            "variant_id": vid,
            "trades": len(g),
            "active_days": len(d),
            "mean_active_day_net": float(d.mean()),
            "median_active_day_net": float(d.median()),
            "win_rate": float((g.net_pnl > 0).mean()),
            "positive_day_rate": float((d > 0).mean()),
            "profit_factor": float(pos / neg) if neg > 0 else 999.0,
            "max_drawdown": float((d.cumsum() - d.cumsum().cummax()).min()),
            "total_net": float(g.net_pnl.sum())
        })
    return pd.DataFrame(rows).sort_values("mean_active_day_net", ascending=False)


def run(root: Path, global_root: Path, out: Path, slippage: float):
    out.mkdir(parents=True, exist_ok=True)
    market = load_market(root)
    global_data = load_global(global_root)
    features = build_features(market, global_data)
    quotes = load_quotes(root, features)
    entries = build_entries(features, quotes)
    trades = simulate(root, entries, out, slippage)
    board = leaderboard(trades)
    board.to_csv(out / "phase19_leaderboard.csv", index=False)
    trades.to_csv(out / "phase19_trades.csv", index=False)
    summary = {
        "variants": len(variant_grid()),
        "market_rows": len(market),
        "feature_rows": len(features),
        "quote_rows": len(quotes),
        "entry_rows": len(entries),
        "trades": len(trades),
        "positive_variants": int((board.mean_active_day_net > 0).sum()) if not board.empty else 0,
        "target_qualified": int((board.mean_active_day_net >= 1000).sum()) if not board.empty else 0,
        "best": board.iloc[0].to_dict() if not board.empty else None,
        "mean_entry_delay": float(entries.entry_delay.mean()) if not entries.empty else None,
        "p90_entry_delay": float(entries.entry_delay.quantile(0.90)) if not entries.empty else None,
        "slippage": slippage
    }
    (out / "phase19_summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print(json.dumps(summary, indent=2, default=str))
    return summary


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--global-root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--slippage", type=float, default=0.20)
    args = ap.parse_args()
    run(args.data, args.global_root, args.out, args.slippage)
