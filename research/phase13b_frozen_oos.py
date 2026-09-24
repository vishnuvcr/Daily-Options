from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from research.cost_model import OptionCostModel
from research.phase10_contracts import index_option_lot_size

SIGNAL_TIME = "14:45:00"
Z_THRESHOLD = 1.5
RV_PERCENTILE = 80.0
HOLD_MINUTES = 10
STOP_PCT = 0.30
TARGET_PCT = 0.60

def compute_spot_features(parquet_glob: str) -> pd.DataFrame:
    con = duckdb.connect()
    q = f"""
    SELECT CAST(datetime AS TIMESTAMP) AS datetime, AVG(CAST(spot AS DOUBLE)) AS spot
    FROM read_parquet('{parquet_glob}', union_by_name=true)
    WHERE date >= DATE '2021-01-01' AND date <= DATE '2025-12-31' AND spot IS NOT NULL
    GROUP BY 1 ORDER BY 1
    """
    spot = con.execute(q).df()
    con.close()
    spot['datetime'] = pd.to_datetime(spot['datetime'])
    local = spot['datetime'].dt.tz_localize('UTC').dt.tz_convert('Asia/Kolkata')
    spot['trade_date'] = local.dt.date
    spot['trade_time_ist'] = local.dt.strftime('%H:%M:%S')
    r1 = spot['spot'].pct_change()
    vol60 = r1.rolling(60, min_periods=30).std()
    r10 = spot['spot'].pct_change(10)
    spot['z10'] = r10 / vol60.replace(0, np.nan)
    spot['prior30high'] = spot['spot'].rolling(30, min_periods=30).max().shift(1)
    spot['rv_pct'] = vol60.rolling(390, min_periods=120).rank(pct=True) * 100.0
    return spot.loc[
        (spot['trade_time_ist'] == SIGNAL_TIME)
        & (spot['z10'] >= Z_THRESHOLD)
        & (spot['spot'] > spot['prior30high'])
        & (spot['rv_pct'] >= RV_PERCENTILE)
    ].copy()

def load_option_window(parquet_glob: str, signal_dates: list) -> pd.DataFrame:
    if not signal_dates:
        return pd.DataFrame()

    dates_sql = ",".join([f"DATE '{d}'" for d in signal_dates])
    con = duckdb.connect()
    q = f"""
    WITH raw AS (
      SELECT *
      FROM read_parquet('{parquet_glob}', union_by_name=true)
    )
    SELECT
      CAST(raw.datetime AS TIMESTAMP) AS datetime,
      CAST(raw.date AS DATE) AS trade_date,
      raw.option_type AS option_type,
      TRY_CAST(raw.expiry AS DATE) AS expiry,
      CAST(raw.strike_price AS DOUBLE) AS strike,
      CAST(raw.open AS DOUBLE) AS open,
      CAST(raw.high AS DOUBLE) AS high,
      CAST(raw.low AS DOUBLE) AS low,
      CAST(raw.close AS DOUBLE) AS close
    FROM raw
    WHERE CAST(raw.date AS DATE) IN ({dates_sql})
      AND raw.expiry_type = 'MONTH'
      AND raw.strike_type = 'ATM'
      AND raw.option_type = 'CALL'
      AND raw.datetime IS NOT NULL
      AND TRY_CAST(raw.expiry AS DATE) IS NOT NULL
    ORDER BY raw.datetime
    """
    df = con.execute(q).df()
    con.close()
    df['datetime'] = pd.to_datetime(df['datetime'])
    return df

def simulate(signals: pd.DataFrame, options: pd.DataFrame, slippage: float) -> pd.DataFrame:
    cm = OptionCostModel()
    rows = []
    for r in signals.itertuples(index=False):
        entry = pd.Timestamp(r.datetime) + pd.Timedelta(minutes=1)
        end = entry + pd.Timedelta(minutes=HOLD_MINUTES)
        x0 = options[(options.trade_date == r.trade_date) & (options.datetime >= entry) & (options.datetime <= end)].copy()
        if x0.empty:
            continue
        expiry_dates = pd.to_datetime(x0['expiry'], errors='coerce').dropna().dt.date
        future_expiries = sorted({d for d in expiry_dates if d >= r.trade_date})
        if not future_expiries:
            continue
        selected_expiry = future_expiries[0]
        x = x0[pd.to_datetime(x0['expiry'], errors='coerce').dt.date == selected_expiry].sort_values('datetime')
        if x.empty:
            continue
        first = x.iloc[0]
        entry_px = float(first.open)
        if entry_px <= 0:
            continue
        stop_level = entry_px * (1 - STOP_PCT)
        target_level = entry_px * (1 + TARGET_PCT)
        exit_ts = x.datetime.iloc[-1]
        reason = 'TIME'
        for bar in x.itertuples(index=False):
            if float(bar.low) <= stop_level:
                exit_ts = bar.datetime; reason = 'STOP'; break
            if float(bar.high) >= target_level:
                exit_ts = bar.datetime; reason = 'TARGET'; break
        ex = x[x.datetime == exit_ts].iloc[-1]
        pnl = cm.net_pnl(entry_px, float(ex.close), qty=1, lot_size=index_option_lot_size('NIFTY', r.trade_date), slippage_points=slippage)
        rows.append({'trade_date': r.trade_date, 'signal_time': r.datetime, 'entry_time': entry, 'expiry': ex.expiry, 'strike': ex.strike, 'entry': entry_px, 'exit': float(ex.close), 'reason': reason, 'net_pnl': pnl})
    return pd.DataFrame(rows)

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--slippage', type=float, default=0.20)
    args = ap.parse_args()
    parquet_glob = str(args.root / 'NIFTY' / 'MONTH' / '*.parquet')
    signals = compute_spot_features(parquet_glob)
    options = load_option_window(parquet_glob, [d.isoformat() for d in signals.trade_date.unique()])
    trades = simulate(signals, options, args.slippage)
    args.out.mkdir(parents=True, exist_ok=True)
    trades.to_csv(args.out / 'phase13b_trades.csv', index=False)
    if trades.empty:
        summary = {'signals': int(len(signals)), 'trades': 0, 'mean_active_day_net': None, 'slippage_points_per_leg': args.slippage, 'gate': 'FAIL_NO_TRADES'}
    else:
        daily = trades.groupby('trade_date')['net_pnl'].sum()
        wins = trades.loc[trades.net_pnl > 0, 'net_pnl'].sum()
        losses = -trades.loc[trades.net_pnl < 0, 'net_pnl'].sum()
        summary = {'signals': int(len(signals)), 'trades': int(len(trades)), 'active_days': int(daily.size), 'mean_active_day_net': float(daily.mean()), 'median_active_day_net': float(daily.median()), 'win_rate': float((trades.net_pnl > 0).mean()), 'positive_day_rate': float((daily > 0).mean()), 'profit_factor': float(wins / losses) if losses > 0 else 999.0, 'max_drawdown': float((daily.cumsum() - daily.cumsum().cummax()).min()), 'total_net': float(trades.net_pnl.sum()), 'target_qualified': bool(daily.mean() >= 1000), 'slippage_points_per_leg': args.slippage, 'gate': 'PASS_REFERENCE_ONLY' if daily.mean() > 0 else 'FAIL'}
    (args.out / 'phase13b_summary.json').write_text(json.dumps(summary, indent=2, default=str))
    (args.out / 'phase13b_decision.json').write_text(json.dumps({'frozen_rule':'w10|z1.5|vp80|14:45:00|LONG|MONTH|h10|r0','period':'2021-01-01 through 2025-12-31','dataset':'artist-23/nifty-options-data','summary':summary}, indent=2, default=str))
    print(json.dumps(summary, indent=2, default=str))

if __name__ == '__main__':
    main()