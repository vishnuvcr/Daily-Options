from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from research.cost_model import OptionCostModel
from research.phase14_global_cross_market_opening_gap import load_global_data, build_features

FROZEN_GLOBAL_Z = 0.5
FROZEN_GAP_THRESHOLD = 0.0075
FROZEN_SIGNAL_TIME = "09:30:00"
FROZEN_HOLD = 20
FROZEN_RISK = {"stop_pct": 0.30, "target_pct": 0.60}
VALIDATION_START = pd.Timestamp("2021-08-01").date()
VALIDATION_END = pd.Timestamp("2024-03-31").date()
LOT_SIZE = 50


def load_index(root: Path) -> pd.DataFrame:
    p = root / "index" / "NIFTY.parquet"
    if not p.exists():
        raise FileNotFoundError(p)
    df = pd.read_parquet(p)
    ts = pd.to_datetime(df["timestamp"], utc=True)
    out = pd.DataFrame({
        "datetime": ts.dt.tz_convert("UTC").dt.tz_localize(None),
        "spot_close": pd.to_numeric(df["close"], errors="coerce"),
    })
    out = out.dropna().sort_values("datetime")
    return out


def frozen_signal_dates(features: pd.DataFrame) -> pd.DataFrame:
    x = features[
        (features.trade_time_ist == FROZEN_SIGNAL_TIME)
        & (features.global_global3.abs() >= FROZEN_GLOBAL_Z)
        & (features.gap_signal.abs() >= FROZEN_GAP_THRESHOLD)
    ].copy()

    # Frozen FADE rule: global signal and opening gap must disagree.
    x = x[np.sign(x.global_global3) != np.sign(x.gap_signal)].copy()

    rows = []
    for d, day in x.groupby("trade_date", sort=True):
        r = day.iloc[0]
        rows.append({
            "trade_date": d,
            "signal_time": r.datetime,
            "entry_time": r.datetime + pd.Timedelta(minutes=1),
            "direction": "CALL" if float(r.gap_signal) < 0 else "PUT",
            "spot": float(r.spot_close),
            "global3": float(r.global_global3),
            "gap": float(r.gap_signal),
        })
    return pd.DataFrame(rows)


def load_selected_expiry_rows(root: Path, signals: pd.DataFrame) -> pd.DataFrame:
    if signals.empty:
        return pd.DataFrame()

    signal_dates = sorted({str(x) for x in signals.trade_date})
    date_sql = ",".join("'" + x + "'" for x in signal_dates)
    glob = (root / "options" / "NIFTY" / "*.parquet").as_posix()

    con = duckdb.connect()
    query = f"""
    SELECT
      CAST(timestamp AS TIMESTAMPTZ) AT TIME ZONE 'UTC' AS datetime_utc,
      CAST(trading_day AS DATE) AS trade_date,
      CAST(expiry AS DATE) AS expiry,
      CAST(strike AS DOUBLE) AS strike,
      CAST(option_type AS VARCHAR) AS option_type,
      CAST(open AS DOUBLE) AS open,
      CAST(high AS DOUBLE) AS high,
      CAST(low AS DOUBLE) AS low,
      CAST(close AS DOUBLE) AS close
    FROM read_parquet('{glob}', union_by_name=true)
    WHERE CAST(trading_day AS DATE) IN ({date_sql})
      AND CAST(expiry AS DATE) > CAST(trading_day AS DATE)
      AND option_type IN ('CE','PE','CALL','PUT')
      AND close > 0
    """
    out = con.execute(query).df()
    con.close()

    if out.empty:
        return out

    out["datetime_utc"] = pd.to_datetime(out["datetime_utc"], utc=True).dt.tz_localize(None)
    out["option_type"] = out["option_type"].replace({
        "CE": "CALL",
        "PE": "PUT",
    })
    return out


def simulate(signals: pd.DataFrame, options: pd.DataFrame, slippage: float) -> pd.DataFrame:
    if signals.empty or options.empty:
        return pd.DataFrame()

    cm = OptionCostModel()
    rows = []

    for rec in signals.itertuples(index=False):
        day = options[options.trade_date == rec.trade_date].copy()
        if day.empty:
            continue

        # Frozen monthly-contract rule: choose the first available contract
        # after the signal date among expiry files present in the independent source.
        expiries = sorted(pd.to_datetime(day.expiry).dt.date.unique())
        expiry_candidates = [d for d in expiries if d > rec.trade_date]
        if not expiry_candidates:
            continue
        expiry = expiry_candidates[0]

        side = rec.direction
        day = day[(day.expiry == expiry) & (day.option_type == side)].copy()
        if day.empty:
            continue

        # ATM at the signal minute, then fixed strike through exit.
        at_signal = day[day.datetime_utc == pd.Timestamp(rec.signal_time)]
        if at_signal.empty:
            continue

        atm = float(
            at_signal.iloc[(at_signal["strike"] - float(rec.spot)).abs().argsort().iloc[0]]["strike"]
        )

        entry = pd.Timestamp(rec.entry_time)
        exit_cutoff = entry + pd.Timedelta(minutes=FROZEN_HOLD)
        bars = day[
            (day.strike == atm)
            & (day.datetime_utc >= entry)
            & (day.datetime_utc <= exit_cutoff)
        ].sort_values("datetime_utc")

        if bars.empty or bars.iloc[0].datetime_utc > entry:
            continue

        first = bars.iloc[0]
        entry_px = float(first.open)
        if not np.isfinite(entry_px) or entry_px <= 0:
            continue

        stop = entry_px * (1 - FROZEN_RISK["stop_pct"])
        target = entry_px * (1 + FROZEN_RISK["target_pct"])
        exit_ts = bars.iloc[-1].datetime_utc
        reason = "TIME"

        for _, bar in bars.iterrows():
            if float(bar.low) <= stop:
                exit_ts = bar.datetime_utc
                reason = "STOP"
                break
            if float(bar.high) >= target:
                exit_ts = bar.datetime_utc
                reason = "TARGET"
                break

        ex = bars[bars.datetime_utc == exit_ts].iloc[-1]
        exit_px = float(ex.close)
        net = cm.net_pnl(
            entry_px,
            exit_px,
            qty=1,
            lot_size=LOT_SIZE,
            slippage_points=slippage,
        )

        rows.append({
            "trade_date": rec.trade_date,
            "year": pd.Timestamp(rec.trade_date).year,
            "direction": side,
            "expiry": expiry,
            "signal_time": rec.signal_time,
            "entry_time": rec.entry_time,
            "exit_time": exit_ts,
            "reason": reason,
            "strike": atm,
            "entry_premium": entry_px,
            "exit_premium": exit_px,
            "global3": rec.global3,
            "gap": rec.gap,
            "net_pnl": net,
        })

    return pd.DataFrame(rows)


def summarize(trades: pd.DataFrame, slippage: float) -> dict:
    if trades.empty:
        return {
            "frozen_rule": True,
            "trades": 0,
            "gate": "NO_TRADES",
            "slippage_points_per_leg": slippage,
        }

    daily = trades.groupby("trade_date").net_pnl.sum()
    years = []

    for year, g in trades.groupby("year"):
        yd = g.groupby("trade_date").net_pnl.sum()
        years.append({
            "year": int(year),
            "trades": int(len(g)),
            "active_days": int(len(yd)),
            "mean_active_day_net": float(yd.mean()),
            "median_active_day_net": float(yd.median()),
            "win_rate": float((g.net_pnl > 0).mean()),
            "total_net": float(g.net_pnl.sum()),
        })

    mean_active = float(daily.mean())
    positive_years = int(sum(x["mean_active_day_net"] > 0 for x in years))

    gate = (
        "PASS_CANDIDATE"
        if mean_active >= 1000 and positive_years >= 2 and len(trades) >= 100
        else "FAIL_LATER_OOS"
    )

    return {
        "frozen_rule": True,
        "validation_start": str(VALIDATION_START),
        "validation_end": str(VALIDATION_END),
        "lot_size": LOT_SIZE,
        "trades": int(len(trades)),
        "active_days": int(len(daily)),
        "mean_active_day_net": mean_active,
        "median_active_day_net": float(daily.median()),
        "mean_calendar_day_net": float(
            daily.sum() / max(1, (VALIDATION_END - VALIDATION_START).days + 1)
        ),
        "win_rate": float((trades.net_pnl > 0).mean()),
        "profit_factor": float(
            trades.loc[trades.net_pnl > 0, "net_pnl"].sum()
            / max(1e-9, -trades.loc[trades.net_pnl < 0, "net_pnl"].sum())
        ),
        "max_drawdown": float(
            (daily.cumsum() - daily.cumsum().cummax()).min()
        ),
        "target_mean": bool(mean_active >= 1000),
        "positive_years": positive_years,
        "years": years,
        "gate": gate,
        "slippage_points_per_leg": slippage,
    }


def run(root: Path, global_root: Path, out: Path, slippage: float) -> dict:
    spot = load_index(root)
    global_data = load_global_data(global_root)

    features = build_features(spot, global_data)
    features = features[
        (features.trade_date >= VALIDATION_START)
        & (features.trade_date <= VALIDATION_END)
    ].copy()

    signals = frozen_signal_dates(features)
    options = load_selected_expiry_rows(root, signals)
    trades = simulate(signals, options, slippage)

    out.mkdir(parents=True, exist_ok=True)
    trades.to_csv(out / "phase14_independent_trades.csv", index=False)

    summary = summarize(trades, slippage)
    summary["signal_days"] = int(len(signals))
    summary["option_rows_loaded"] = int(len(options))

    (out / "phase14_independent_summary.json").write_text(
        json.dumps(summary, indent=2, default=str)
    )
    print(json.dumps(summary, indent=2, default=str))
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--global-root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--slippage", type=float, default=0.20)
    args = ap.parse_args()
    run(args.root, args.global_root, args.out, args.slippage)


if __name__ == "__main__":
    main()
