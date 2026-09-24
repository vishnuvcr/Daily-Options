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


SYMBOL = "BANKNIFTY"
ENTRY_TIMES = ("09:45:00", "10:00:00")
OPENING_RANGES = (5, 15)
BREAKOUT_PCTS = (0.0005, 0.0010)
PULLBACK_TOLS = (0.0002, 0.0005)
HOLDS = (15, 30)
RISK_PROFILES = (
    {"stop_pct": 0.20, "target_pct": 0.50},
    {"stop_pct": 0.30, "target_pct": 0.80},
)
PULLBACK_LOOKAHEAD_BARS = 10


@dataclass(frozen=True)
class Variant:
    opening_range: int
    breakout_pct: float
    pullback_tol: float
    entry_time: str
    hold_minutes: int
    risk_id: int

    @property
    def key(self) -> str:
        return (
            f"or{self.opening_range}|b{self.breakout_pct:.4f}|"
            f"pb{self.pullback_tol:.4f}|{self.entry_time}|"
            f"h{self.hold_minutes}|r{self.risk_id}"
        )


def variant_grid() -> list[Variant]:
    return [
        Variant(or_m, br, pb, et, hold, risk)
        for or_m in OPENING_RANGES
        for br in BREAKOUT_PCTS
        for pb in PULLBACK_TOLS
        for et in ENTRY_TIMES
        for hold in HOLDS
        for risk in range(len(RISK_PROFILES))
    ]


def idx_path(root: Path) -> str:
    return (root / "index" / f"{SYMBOL}.parquet").as_posix()


def opt_glob(root: Path) -> str:
    return (root / "options" / SYMBOL / "*.parquet").as_posix()


def load_spot(root: Path) -> pd.DataFrame:
    con = duckdb.connect()
    df = con.execute(
        f"""
        SELECT
            CAST(timestamp AS TIMESTAMP) AS local_ts,
            CAST(trading_day AS DATE) AS trade_date,
            CAST(open AS DOUBLE) AS open,
            CAST(high AS DOUBLE) AS high,
            CAST(low AS DOUBLE) AS low,
            CAST(close AS DOUBLE) AS close
        FROM read_parquet('{idx_path(root)}', union_by_name=true)
        WHERE close > 0
          AND local_ts::TIME BETWEEN TIME '09:15:00' AND TIME '11:30:00'
        ORDER BY trade_date, local_ts
        """
    ).df()
    con.close()
    if df.empty:
        return df
    df["local_ts"] = pd.to_datetime(df["local_ts"])
    df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date
    return df


def opening_range(df: pd.DataFrame, minutes: int) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    start = df["trade_date"].map(lambda d: pd.Timestamp(d) + pd.Timedelta(hours=9, minutes=15))
    end = start + pd.Timedelta(minutes=minutes)
    x = df.loc[(df["local_ts"] >= start) & (df["local_ts"] < end)].copy()
    if x.empty:
        return pd.DataFrame()
    return (
        x.groupby("trade_date")
        .agg(range_high=("high", "max"), range_low=("low", "min"), bars=("close", "size"))
        .reset_index()
    )


def load_oi_bias(root: Path) -> pd.DataFrame:
    con = duckdb.connect()
    df = con.execute(
        f"""
        WITH raw AS (
          SELECT
            CAST(timestamp AS TIMESTAMP) AS local_ts,
            CAST(trading_day AS DATE) AS trade_date,
            CAST(strike AS DOUBLE) AS strike,
            CASE
              WHEN UPPER(CAST(option_type AS VARCHAR)) IN ('CALL','CE') THEN 'CALL'
              WHEN UPPER(CAST(option_type AS VARCHAR)) IN ('PUT','PE') THEN 'PUT'
              ELSE NULL
            END AS side,
            CAST(open_interest AS DOUBLE) AS oi,
            CAST(close AS DOUBLE) AS close
          FROM read_parquet('{opt_glob(root)}', union_by_name=true)
          WHERE close > 0
            AND open_interest >= 0
        ),
        spot AS (
          SELECT
            CAST(timestamp AS TIMESTAMP) AS local_ts,
            CAST(trading_day AS DATE) AS trade_date,
            CAST(close AS DOUBLE) AS spot
          FROM read_parquet('{idx_path(root)}', union_by_name=true)
          WHERE close > 0
        ),
        chain AS (
          SELECT
            r.trade_date,
            r.local_ts,
            s.spot,
            r.side,
            r.strike,
            r.oi
          FROM raw r
          JOIN spot s
            ON s.trade_date=r.trade_date AND s.local_ts=r.local_ts
          WHERE ABS(r.strike-s.spot) <= 1000
        )
        SELECT
          trade_date,
          local_ts,
          SUM(CASE WHEN side='PUT' THEN oi ELSE 0 END) AS put_oi,
          SUM(CASE WHEN side='CALL' THEN oi ELSE 0 END) AS call_oi
        FROM chain
        GROUP BY trade_date, local_ts
        ORDER BY trade_date, local_ts
        """
    ).df()
    con.close()
    if df.empty:
        return df
    df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date
    total = (df["put_oi"] + df["call_oi"]).replace(0, np.nan)
    df["oi_bias"] = (df["put_oi"] - df["call_oi"]) / total
    return df[["trade_date", "local_ts", "oi_bias"]]


def build_signals(spot: pd.DataFrame, oi_bias: pd.DataFrame) -> pd.DataFrame:
    if spot.empty:
        return pd.DataFrame()

    rows = []
    for v in variant_grid():
        or_df = opening_range(spot, v.opening_range)
        if or_df.empty:
            continue
        x = spot.merge(or_df, on="trade_date", how="inner")
        x["trade_time"] = x["local_ts"].dt.strftime("%H:%M:%S")
        x = x.loc[x["trade_time"] >= v.entry_time].copy()
        if x.empty:
            continue
        x = x.merge(oi_bias, on=["trade_date", "local_ts"], how="left")

        for trade_date, day in x.groupby("trade_date", sort=True):
            day = day.sort_values("local_ts").reset_index(drop=True)
            if day.empty:
                continue
            breakout_idx = None
            direction = None
            level = np.nan
            for i, r in day.iterrows():
                if r["close"] >= r["range_high"] * (1 + v.breakout_pct):
                    breakout_idx = i
                    direction = "CALL"
                    level = float(r["range_high"])
                    break
                if r["close"] <= r["range_low"] * (1 - v.breakout_pct):
                    breakout_idx = i
                    direction = "PUT"
                    level = float(r["range_low"])
                    break
            if breakout_idx is None:
                continue

            end_i = min(len(day) - 1, breakout_idx + PULLBACK_LOOKAHEAD_BARS)
            for j in range(breakout_idx + 1, end_i + 1):
                r = day.iloc[j]
                tol = v.pullback_tol
                if direction == "CALL":
                    touched = float(r["low"]) <= level * (1 + tol)
                    reclaimed = float(r["close"]) > level
                    oi_ok = pd.notna(r["oi_bias"]) and float(r["oi_bias"]) > 0
                else:
                    touched = float(r["high"]) >= level * (1 - tol)
                    reclaimed = float(r["close"]) < level
                    oi_ok = pd.notna(r["oi_bias"]) and float(r["oi_bias"]) < 0
                if touched and reclaimed and oi_ok:
                    rows.append(
                        {
                            "variant_id": v.key,
                            "trade_date": trade_date,
                            "signal_time": r["local_ts"],
                            "entry_time": r["local_ts"] + pd.Timedelta(minutes=1),
                            "direction": direction,
                            "spot": float(r["close"]),
                            "breakout_level": level,
                            "hold_minutes": v.hold_minutes,
                            "risk_id": v.risk_id,
                            "oi_bias": float(r["oi_bias"]),
                        }
                    )
                    break

    return pd.DataFrame(rows)


def select_entries(signals: pd.DataFrame, root: Path) -> pd.DataFrame:
    if signals.empty:
        return pd.DataFrame()

    con = duckdb.connect()
    con.register("signals_df", signals)
    glob = opt_glob(root)
    sql = f"""
    WITH expiries AS (
      SELECT DISTINCT CAST(expiry AS DATE) AS expiry
      FROM read_parquet('{glob}', union_by_name=true)
      WHERE expiry IS NOT NULL
    ),
    next_exp AS (
      SELECT s.*, MIN(e.expiry) AS expiry
      FROM signals_df s
      JOIN expiries e ON e.expiry > s.trade_date
      GROUP BY ALL
    ),
    raw AS (
      SELECT
        CAST(trading_day AS DATE) AS trade_date,
        CAST(expiry AS DATE) AS expiry,
        CASE
          WHEN UPPER(CAST(option_type AS VARCHAR)) IN ('CALL','CE') THEN 'CALL'
          WHEN UPPER(CAST(option_type AS VARCHAR)) IN ('PUT','PE') THEN 'PUT'
          ELSE NULL
        END AS side,
        CAST(strike AS DOUBLE) AS strike,
        CAST(timestamp AS TIMESTAMP) AS local_ts,
        CAST(open AS DOUBLE) AS open
      FROM read_parquet('{glob}', union_by_name=true)
      WHERE close > 0
    ),
    atm_candidates AS (
      SELECT
        s.*,
        r.strike AS atm_strike,
        r.open AS atm_open,
        ROW_NUMBER() OVER (
          PARTITION BY s.variant_id, s.trade_date
          ORDER BY ABS(r.strike - s.spot), r.strike
        ) AS rn
      FROM next_exp s
      JOIN raw r
        ON r.trade_date=s.trade_date
       AND r.expiry=s.expiry
       AND r.side=s.direction
       AND r.local_ts=s.entry_time
    ),
    atm AS (
      SELECT * FROM atm_candidates WHERE rn=1
    ),
    wing_candidates AS (
      SELECT
        a.*,
        r.strike AS wing_strike,
        r.open AS wing_open,
        ROW_NUMBER() OVER (
          PARTITION BY a.variant_id, a.trade_date
          ORDER BY CASE WHEN a.direction='CALL' THEN r.strike ELSE -r.strike END ASC
        ) AS rn_wing
      FROM atm a
      JOIN raw r
        ON r.trade_date=a.trade_date
       AND r.expiry=a.expiry
       AND r.side=a.direction
       AND r.local_ts=a.entry_time
       AND CASE
             WHEN a.direction='CALL' THEN r.strike > a.atm_strike
             ELSE r.strike < a.atm_strike
           END
    )
    SELECT
      variant_id, trade_date, signal_time, entry_time, direction, spot,
      breakout_level, hold_minutes, risk_id, oi_bias, expiry,
      atm_strike, wing_strike,
      atm_open AS long_entry,
      wing_open AS short_entry,
      atm_open - wing_open AS debit
    FROM wing_candidates
    WHERE rn_wing=1 AND atm_open > wing_open
    """
    out = con.execute(sql).df()
    con.close()
    if out.empty:
        return out
    out["entry_time"] = pd.to_datetime(out["entry_time"])
    out["signal_time"] = pd.to_datetime(out["signal_time"])
    out["trade_date"] = pd.to_datetime(out["trade_date"]).dt.date
    return out

def simulate(entries: pd.DataFrame, root: Path, out_dir: Path, slippage: float) -> pd.DataFrame:
    if entries.empty:
        return pd.DataFrame()
    cm = OptionCostModel()
    out_rows = []

    con = duckdb.connect()
    con.register("entries_df", entries)
    path = con.execute(
        f"""
        WITH raw AS (
          SELECT
            CAST(trading_day AS DATE) AS trade_date,
            CAST(expiry AS DATE) AS expiry,
            CASE
              WHEN UPPER(CAST(option_type AS VARCHAR)) IN ('CALL','CE') THEN 'CALL'
              ELSE 'PUT'
            END AS side,
            CAST(strike AS DOUBLE) AS strike,
            CAST(timestamp AS TIMESTAMP) AS local_ts,
            CAST(open AS DOUBLE) AS open,
            CAST(high AS DOUBLE) AS high,
            CAST(low AS DOUBLE) AS low,
            CAST(close AS DOUBLE) AS close
          FROM read_parquet('{opt_glob(root)}', union_by_name=true)
          WHERE close > 0
        )
        SELECT
          e.*,
          r.local_ts,
          r.strike,
          r.open, r.high, r.low, r.close
        FROM entries_df e
        JOIN raw r
          ON r.trade_date=e.trade_date
         AND r.expiry=e.expiry
         AND r.side=e.direction
         AND r.strike IN (e.atm_strike, e.wing_strike)
         AND r.local_ts BETWEEN e.entry_time
                            AND e.entry_time + e.hold_minutes * INTERVAL '1 minute'
        ORDER BY e.variant_id, e.trade_date, r.local_ts
        """
    ).df()
    con.close()
    if path.empty:
        return pd.DataFrame()

    for (variant_id, trade_date), g in path.groupby(["variant_id", "trade_date"], sort=False):
        meta = g.iloc[0]
        pivot = (
            g.pivot_table(
                index="local_ts",
                columns="strike",
                values=["open", "high", "low", "close"],
                aggfunc="last",
            )
            .sort_index()
        )
        a = float(meta["atm_strike"])
        w = float(meta["wing_strike"])
        if a not in pivot["close"].columns or w not in pivot["close"].columns:
            continue

        first = pivot.iloc[0]
        long_entry = float(first[("open", a)])
        short_entry = float(first[("open", w)])
        debit = long_entry - short_entry
        if debit <= 0:
            continue

        prof = RISK_PROFILES[int(meta["risk_id"])]
        stop_level = debit * (1 - prof["stop_pct"])
        target_level = debit * (1 + prof["target_pct"])
        exit_ts = pivot.index[-1]
        reason = "TIME"

        for ts, bar in pivot.iterrows():
            spread_high = float(bar[("high", a)] - bar[("low", w)])
            spread_low = float(bar[("low", a)] - bar[("high", w)])
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
        long_exit = float(last[("close", a)].iloc[0])
        short_exit = float(last[("close", w)].iloc[0])

        net = cm.vertical_debit_spread_net_pnl(
            long_entry,
            short_entry,
            long_exit,
            short_exit,
            lot_size=index_option_lot_size(SYMBOL, meta["expiry"]),
            qty=1,
            slippage_points=slippage,
        )
        out_rows.append(
            {
                "variant_id": meta["variant_id"],
                "trade_date": trade_date,
                "direction": meta["direction"],
                "signal_time": meta["signal_time"],
                "entry_time": meta["entry_time"],
                "exit_time": exit_ts,
                "expiry": meta["expiry"],
                "atm_strike": a,
                "wing_strike": w,
                "entry_debit": debit,
                "exit_debit": long_exit - short_exit,
                "oi_bias": meta["oi_bias"],
                "net_pnl": net,
                "exit_reason": reason,
            }
        )

    out = pd.DataFrame(out_rows)
    out_dir.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_dir / "phase11_trades.csv", index=False)
    return out


def leaderboard(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame()
    rows = []
    for variant, g in trades.groupby("variant_id", sort=False):
        d = g.groupby("trade_date")["net_pnl"].sum()
        wins = g.loc[g.net_pnl > 0, "net_pnl"].sum()
        losses = -g.loc[g.net_pnl < 0, "net_pnl"].sum()
        rows.append(
            {
                "variant_id": variant,
                "trades": len(g),
                "active_days": int(d.size),
                "mean_active_day_net": float(d.mean()),
                "win_rate": float((g.net_pnl > 0).mean()),
                "positive_day_rate": float((d > 0).mean()),
                "profit_factor": float(wins / losses) if losses > 0 else 999.0,
                "max_drawdown": float((d.cumsum() - d.cumsum().cummax()).min()),
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
    dates = sorted(x["trade_date"].unique())
    train_len, val_len, embargo, test_len, step = 180, 60, 5, 60, 60
    rows = []
    start = 0
    while start + train_len + val_len + embargo + test_len <= len(dates):
        tr_dates = set(dates[start : start + train_len])
        va_dates = set(dates[start + train_len : start + train_len + val_len])
        te_dates = set(
            dates[start + train_len + val_len + embargo :
                 start + train_len + val_len + embargo + test_len]
        )
        tr = x[x.trade_date.isin(tr_dates)]
        va = x[x.trade_date.isin(va_dates)]
        te = x[x.trade_date.isin(te_dates)]
        train_scores = []
        for v, g in tr.groupby("variant_id"):
            if len(g) >= 8:
                train_scores.append((v, float(g.groupby("trade_date").net_pnl.sum().mean())))
        train_scores.sort(key=lambda z: z[1], reverse=True)
        val_scores = []
        for v, _ in train_scores[:12]:
            g = va[va.variant_id.eq(v)]
            if len(g) >= 5:
                val_scores.append((v, float(g.groupby("trade_date").net_pnl.sum().mean())))
        if not val_scores:
            start += step
            continue
        val_scores.sort(key=lambda z: z[1], reverse=True)
        selected = val_scores[0][0]
        test_g = te[te.variant_id.eq(selected)]
        if test_g.empty:
            start += step
            continue
        d = test_g.groupby("trade_date").net_pnl.sum()
        rows.append(
            {
                "test_start": str(min(te_dates)),
                "test_end": str(max(te_dates)),
                "selected_variant": selected,
                "validation_mean": val_scores[0][1],
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


def run(root: Path, out: Path, slippage: float) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    spot = load_spot(root)
    oi = load_oi_bias(root)
    signals = build_signals(spot, oi)
    signals.to_csv(out / "phase11_signals.csv", index=False)
    entries = select_entries(signals, root)
    entries.to_csv(out / "phase11_entries.csv", index=False)
    trades = simulate(entries, root, out, slippage)
    board = leaderboard(trades)
    board.to_csv(out / "phase11_leaderboard.csv", index=False)
    wf, wfs = walk_forward(trades)
    wf.to_csv(out / "phase11_walk_forward.csv", index=False)
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
        "data_license_note": "Research-only public dataset; licensed validation required for deployment.",
    }
    (out / "phase11_summary.json").write_text(json.dumps(summary, indent=2, default=str))
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
