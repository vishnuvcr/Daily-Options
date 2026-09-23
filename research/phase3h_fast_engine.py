from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from research.contracts import nifty_lot_size
from research.cost_model import OptionCostModel
from research.phase3h_option_lead_lag import (
    parameter_grid,
    feature_query,
    raw_query,
    build_signals,
    summarize,
    walk_forward,
    diagnostic_summary,
)

SETUP_COLS = [
    "trade_date",
    "expiry_type",
    "entry_time",
    "direction",
    "atm_strike",
    "wing_strike",
    "hold_minutes",
]


def load_data(root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    con = duckdb.connect()
    features = con.execute(feature_query(root)).df()
    raw = con.execute(raw_query(root)).df()
    con.close()
    features["datetime"] = pd.to_datetime(features["datetime"])
    raw["datetime"] = pd.to_datetime(raw["datetime"])
    return features, raw


def indexed_groups(raw: pd.DataFrame) -> dict:
    maps = {}
    for key, g in raw.groupby(["trade_date", "expiry_type"], sort=False):
        opt_maps = {}
        for opt_type, og in g.groupby("option_type", sort=False):
            pivot = (
                og.pivot_table(
                    index="datetime",
                    columns="strike_price",
                    values="close",
                    aggfunc="last",
                )
                .sort_index()
            )
            opt_maps[opt_type] = pivot
        maps[key] = opt_maps
    return maps


def choose_entries_fast(signals: pd.DataFrame, groups: dict) -> pd.DataFrame:
    if signals.empty:
        return pd.DataFrame()

    rows = []
    for row in signals.itertuples(index=False):
        pmap = groups.get((row.trade_date, row.expiry_type), {})
        pivot = pmap.get(row.direction)
        if pivot is None or pivot.empty:
            continue

        idx = pivot.index
        pos = int(idx.searchsorted(row.entry_anchor, side="left"))
        if pos >= len(idx):
            continue
        entry_time = idx[pos]
        # Execution budget: next minute, with one-minute tolerance for a missing bar.
        if entry_time > row.entry_anchor + pd.Timedelta(minutes=2):
            continue

        q = pivot.loc[entry_time]
        strikes = [float(s) for s in q.index if pd.notna(q.loc[s])]
        if not strikes:
            continue

        atm = min(strikes, key=lambda k: abs(k - float(row.spot)))
        meta = json.loads(row.variant)
        width = int(meta["width_steps"])

        if row.direction == "CALL":
            wings = sorted(k for k in strikes if k > atm)
        else:
            wings = sorted((k for k in strikes if k < atm), reverse=True)

        if len(wings) < width:
            continue

        wing = float(wings[width - 1])
        if pd.isna(q.loc[atm]) or pd.isna(q.loc[wing]):
            continue

        rows.append(
            {
                **row._asdict(),
                "entry_time": entry_time,
                "atm_strike": float(atm),
                "wing_strike": wing,
                "long_entry": float(q.loc[atm]),
                "short_entry": float(q.loc[wing]),
                "hold_minutes": int(meta["hold_minutes"]),
            }
        )
    return pd.DataFrame(rows)


def simulate_paths_fast(entries: pd.DataFrame, groups: dict) -> pd.DataFrame:
    if entries.empty:
        return pd.DataFrame()

    setups = entries.drop_duplicates(SETUP_COLS).reset_index(drop=True)
    paths = []

    for row in setups.itertuples(index=False):
        pmap = groups.get((row.trade_date, row.expiry_type), {})
        pivot = pmap.get(row.direction)
        if pivot is None:
            continue
        if row.atm_strike not in pivot.columns or row.wing_strike not in pivot.columns:
            continue

        end_time = row.entry_time + pd.Timedelta(minutes=int(row.hold_minutes))
        path = pivot.loc[
            (pivot.index >= row.entry_time) & (pivot.index <= end_time),
            [row.atm_strike, row.wing_strike],
        ].dropna()

        if path.empty or row.entry_time not in path.index:
            continue

        spread = path[row.atm_strike] - path[row.wing_strike]
        debit = float(spread.loc[row.entry_time])
        if not np.isfinite(debit) or debit <= 0:
            continue

        stop = 0.50 * debit
        target = 1.75 * debit
        exit_time = path.index[-1]
        reason = "time"

        for dt, value in spread.iloc[1:].items():
            value = float(value)
            if value <= stop:
                exit_time, reason = dt, "stop"
                break
            if value >= target:
                exit_time, reason = dt, "target"
                break

        exit_row = path.loc[exit_time]
        paths.append(
            {
                "trade_date": row.trade_date,
                "expiry_type": row.expiry_type,
                "entry_time": row.entry_time,
                "direction": row.direction,
                "atm_strike": row.atm_strike,
                "wing_strike": row.wing_strike,
                "hold_minutes": row.hold_minutes,
                "long_entry": row.long_entry,
                "short_entry": row.short_entry,
                "long_exit": float(exit_row.iloc[0]),
                "short_exit": float(exit_row.iloc[1]),
                "exit_time": exit_time,
                "exit_reason": reason,
                "debit": debit,
            }
        )

    if not paths:
        return pd.DataFrame()

    path_df = pd.DataFrame(paths)
    # Reattach all parameter variants that share the same executable setup.
    return entries.merge(
        path_df,
        on=SETUP_COLS + ["long_entry", "short_entry"],
        how="inner",
        suffixes=("", "_path"),
    )


def attach_pnl(trades: pd.DataFrame, slippage_points: float) -> pd.DataFrame:
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
            out["long_entry"],
            out["short_entry"],
            out["long_exit"],
            out["short_exit"],
            out["lot_size"],
        )
    ]
    return out


def run(root: Path, out_dir: Path, slippage: float) -> dict:
    features, raw = load_data(root)
    groups = indexed_groups(raw)
    params = parameter_grid()

    signals = build_signals(features, params)
    entries = choose_entries_fast(signals, groups)
    trades = attach_pnl(simulate_paths_fast(entries, groups), slippage)

    out_dir.mkdir(parents=True, exist_ok=True)
    signals.to_csv(out_dir / "phase3h_signals.csv", index=False)
    diagnostic_summary(signals).to_csv(out_dir / "phase3h_leadlag_diagnostic.csv", index=False)
    trades.to_csv(out_dir / "phase3h_trades.csv", index=False)

    board, preliminary = summarize(trades, int(features["trade_date"].nunique()))
    board.to_csv(out_dir / "phase3h_leaderboard.csv", index=False)

    wf, wf_summary = walk_forward(trades)
    wf.to_csv(out_dir / "phase3h_walk_forward.csv", index=False)

    summary = {
        "features": int(len(features)),
        "signals": int(len(signals)),
        "entries": int(len(entries)),
        "trades": int(len(trades)),
        "variants": len(params),
        "preliminary": preliminary,
        "walk_forward": wf_summary,
        "slippage_points": slippage,
        "volume_used": False,
        "gate": wf_summary.get("gate", preliminary.get("gate")),
    }
    (out_dir / "phase3h_summary.json").write_text(
        json.dumps(summary, indent=2, default=str), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, default=str))
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=Path("reports/phase3h_fast"))
    ap.add_argument("--slippage", type=float, default=0.20)
    args = ap.parse_args()
    run(args.data, args.out, args.slippage)


if __name__ == "__main__":
    main()
