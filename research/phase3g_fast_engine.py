from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb
import pandas as pd

from research.contracts import nifty_lot_size
from research.cost_model import OptionCostModel
from research.phase3g_oi_confirmed_breakout import (
    parameter_grid,
    feature_query,
    raw_query,
    build_signals,
    summarize,
    walk_forward,
)


def grouped_raw(raw: pd.DataFrame) -> dict:
    return {
        key: group.sort_values("datetime").copy()
        for key, group in raw.groupby(["trade_date", "expiry_type"], sort=False)
    }


def choose_entries_fast(signals: pd.DataFrame, raw: pd.DataFrame) -> pd.DataFrame:
    if signals.empty:
        return signals
    groups = grouped_raw(raw)
    rows = []
    for idx, row in enumerate(signals.itertuples(index=False)):
        g = groups.get((row.trade_date, row.expiry_type))
        if g is None:
            continue
        q = g[(g["datetime"] == row.entry_time) & (g["option_type"] == row.direction)]
        if q.empty:
            continue
        strikes = sorted(q["strike_price"].dropna().unique())
        if not strikes:
            continue
        atm = min(strikes, key=lambda k: abs(float(k) - float(row.spot)))
        meta = json.loads(row.variant)
        width = int(meta["width_steps"])
        if row.direction == "CALL":
            wings = sorted(k for k in strikes if k > atm)
        else:
            wings = sorted((k for k in strikes if k < atm), reverse=True)
        if len(wings) < width:
            continue
        wing = float(wings[width - 1])
        le = q.loc[q["strike_price"].eq(atm), "close"]
        se = q.loc[q["strike_price"].eq(wing), "close"]
        if le.empty or se.empty:
            continue
        rows.append({
            "trade_id": idx,
            "trade_date": row.trade_date,
            "expiry_type": row.expiry_type,
            "entry_time": row.entry_time,
            "direction": row.direction,
            "spot": float(row.spot),
            "variant": row.variant,
            "atm_strike": float(atm),
            "wing_strike": wing,
            "long_entry": float(le.iloc[0]),
            "short_entry": float(se.iloc[0]),
            "hold_minutes": int(meta["hold_minutes"]),
        })
    return pd.DataFrame(rows)


def simulate_setups_fast(entries: pd.DataFrame, raw: pd.DataFrame) -> pd.DataFrame:
    if entries.empty:
        return entries
    groups = grouped_raw(raw)
    setup_cols = [
        "trade_date", "expiry_type", "entry_time", "direction",
        "atm_strike", "wing_strike", "hold_minutes"
    ]
    setups = entries.drop_duplicates(setup_cols).reset_index(drop=True)
    outputs = []
    for row in setups.itertuples(index=False):
        g = groups.get((row.trade_date, row.expiry_type))
        if g is None:
            continue
        end_time = row.entry_time + pd.Timedelta(minutes=int(row.hold_minutes))
        sub = g[
            (g["datetime"] >= row.entry_time)
            & (g["datetime"] <= end_time)
            & (g["option_type"] == row.direction)
            & g["strike_price"].isin([row.atm_strike, row.wing_strike])
        ]
        if sub.empty:
            continue
        pivot = sub.pivot_table(
            index="datetime",
            columns="strike_price",
            values="close",
            aggfunc="last",
        ).dropna(subset=[row.atm_strike, row.wing_strike])
        if pivot.empty or row.entry_time not in pivot.index:
            continue
        spread = pivot[row.atm_strike] - pivot[row.wing_strike]
        debit = float(spread.loc[row.entry_time])
        if debit <= 0:
            continue
        stop = 0.50 * debit
        target = 1.75 * debit
        path = spread.loc[spread.index >= row.entry_time]
        exit_time = path.index[-1]
        exit_value = float(path.iloc[-1])
        reason = "time"
        for dt, value in path.iloc[1:].items():
            value = float(value)
            if value <= stop:
                exit_time, exit_value, reason = dt, value, "stop"
                break
            if value >= target:
                exit_time, exit_value, reason = dt, value, "target"
                break
        exit_row = pivot.loc[exit_time]
        outputs.append({
            "trade_date": row.trade_date,
            "expiry_type": row.expiry_type,
            "entry_time": row.entry_time,
            "direction": row.direction,
            "atm_strike": row.atm_strike,
            "wing_strike": row.wing_strike,
            "hold_minutes": row.hold_minutes,
            "long_entry": row.long_entry,
            "short_entry": row.short_entry,
            "long_exit": float(exit_row[row.atm_strike]),
            "short_exit": float(exit_row[row.wing_strike]),
            "exit_time": exit_time,
            "exit_reason": reason,
            "debit": debit,
        })
    if not outputs:
        return pd.DataFrame()
    paths = pd.DataFrame(outputs)
    return entries.merge(paths, on=setup_cols + ["long_entry", "short_entry"], how="inner")


def attach_pnl_fast(trades: pd.DataFrame, slippage_points: float) -> pd.DataFrame:
    if trades.empty:
        return trades
    cm = OptionCostModel()
    out = trades.copy()
    out["lot_size"] = out["trade_date"].map(nifty_lot_size)
    out["net_pnl"] = [
        cm.vertical_debit_spread_net_pnl(
            le, se, lx, sx, int(lot), slippage_points=slippage_points
        )
        for le, se, lx, sx, lot in zip(
            out["long_entry"], out["short_entry"],
            out["long_exit"], out["short_exit"], out["lot_size"]
        )
    ]
    return out


def run(data_root: Path, out_dir: Path, slippage: float) -> dict:
    con = duckdb.connect()
    features = con.execute(feature_query(data_root)).df()
    raw = con.execute(raw_query(data_root)).df()
    con.close()
    features["datetime"] = pd.to_datetime(features["datetime"])
    raw["datetime"] = pd.to_datetime(raw["datetime"])

    params = parameter_grid()
    signals = build_signals(features, params)
    entries = choose_entries_fast(signals, raw)
    trades = simulate_setups_fast(entries, raw)
    trades = attach_pnl_fast(trades, slippage)

    out_dir.mkdir(parents=True, exist_ok=True)
    trades.to_csv(out_dir / "phase3g_trades.csv", index=False)
    board, preliminary = summarize(trades, int(features["trade_date"].nunique()))
    board.to_csv(out_dir / "phase3g_leaderboard.csv", index=False)
    wf, wf_summary = walk_forward(trades)
    wf.to_csv(out_dir / "phase3g_walk_forward.csv", index=False)
    summary = {
        "features": int(len(features)),
        "signals": int(len(signals)),
        "entries": int(len(entries)),
        "unique_setups": int(len(entries.drop_duplicates([
            "trade_date","expiry_type","entry_time","direction",
            "atm_strike","wing_strike","hold_minutes"
        ]))) if not entries.empty else 0,
        "trades": int(len(trades)),
        "variants": len(params),
        "preliminary": preliminary,
        "walk_forward": wf_summary,
        "slippage_points": slippage,
        "gate": wf_summary.get("gate", preliminary.get("gate")),
    }
    (out_dir / "phase3g_summary.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(json.dumps(summary, indent=2, default=str))
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=Path("reports/phase3g_fast"))
    ap.add_argument("--slippage", type=float, default=0.20)
    args = ap.parse_args()
    run(args.data, args.out, args.slippage)


if __name__ == "__main__":
    main()
