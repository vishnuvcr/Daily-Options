from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from research.contracts import nifty_lot_size
from research.cost_model import OptionCostModel
from research.phase3i_opening_false_break_reversion import (
    HOLDS,
    EXPIRIES,
    WIDTHS,
    parameter_grid,
    raw_query,
    summarize,
    walk_forward,
)

OR_MINUTES = (5, 15, 30)
BREAK_PCTS = (0.0005, 0.0010)
REENTRY_PCTS = (0.0002, 0.0005)


def parquet_glob(root: Path) -> str:
    return (root / "**" / "*.parquet").as_posix()


def spot_query(root: Path) -> str:
    g = parquet_glob(root)
    return f"""
    SELECT
      datetime + INTERVAL '5 hours 30 minutes' AS datetime_ist,
      CAST(date AS DATE) AS trade_date,
      MAX(CAST(spot AS DOUBLE)) AS spot
    FROM read_parquet('{g}', union_by_name=true)
    WHERE close > 0
      AND STRFTIME(datetime + INTERVAL '5 hours 30 minutes','%H:%M:%S')
          BETWEEN '09:15:00' AND '14:45:00'
    GROUP BY ALL
    ORDER BY trade_date, datetime_ist
    """


def build_base_events(spot: pd.DataFrame) -> pd.DataFrame:
    """Find one first false-break/re-entry event per day for each OR/break/re-entry tuple."""
    if spot.empty:
        return pd.DataFrame()

    spot = spot.copy()
    spot["datetime_ist"] = pd.to_datetime(spot["datetime_ist"])
    event_rows = []

    for trade_date, g in spot.groupby("trade_date", sort=True):
        g = g.sort_values("datetime_ist").reset_index(drop=True)
        if g.empty:
            continue

        t0 = pd.Timestamp(f"{trade_date} 09:15:00")
        for or_m in OR_MINUTES:
            or_end = t0 + pd.Timedelta(minutes=or_m - 1)
            opening = g.loc[
                (g["datetime_ist"] >= t0) & (g["datetime_ist"] <= or_end),
                ["datetime_ist", "spot"],
            ]
            if len(opening) < max(3, or_m // 2):
                continue

            or_high = float(opening["spot"].max())
            or_low = float(opening["spot"].min())
            after = g.loc[g["datetime_ist"] > or_end, ["datetime_ist", "spot"]].copy()

            ts = after["datetime_ist"].to_numpy()
            px = after["spot"].to_numpy(float)

            for break_pct in BREAK_PCTS:
                down_mask = px <= or_low * (1.0 - break_pct)
                up_mask = px >= or_high * (1.0 + break_pct)

                down_idx = np.where(down_mask)[0]
                up_idx = np.where(up_mask)[0]

                for reentry_pct in REENTRY_PCTS:
                    candidates = []

                    if len(down_idx):
                        first_down = int(down_idx[0])
                        re = np.where(
                            px[first_down + 1:] >= or_low * (1.0 + reentry_pct)
                        )[0]
                        if len(re):
                            candidates.append((first_down + 1 + int(re[0]), "CALL", "downside_false_break"))

                    if len(up_idx):
                        first_up = int(up_idx[0])
                        re = np.where(
                            px[first_up + 1:] <= or_high * (1.0 - reentry_pct)
                        )[0]
                        if len(re):
                            candidates.append((first_up + 1 + int(re[0]), "PUT", "upside_false_break"))

                    if not candidates:
                        continue

                    # First re-entry event of either direction for this day/parameter tuple.
                    pos, direction, event = min(candidates, key=lambda x: x[0])
                    event_rows.append(
                        {
                            "trade_date": trade_date,
                            "signal_time": pd.Timestamp(ts[pos]),
                            "signal_spot": float(px[pos]),
                            "direction": direction,
                            "event": event,
                            "or_high": or_high,
                            "or_low": or_low,
                            "or_minutes": or_m,
                            "break_pct": break_pct,
                            "reentry_pct": reentry_pct,
                            "entry_anchor": pd.Timestamp(ts[pos]) + pd.Timedelta(minutes=1),
                        }
                    )

    return pd.DataFrame(event_rows)


def expand_events(events: pd.DataFrame) -> pd.DataFrame:
    if events.empty:
        return events
    base = []
    for row in events.itertuples(index=False):
        for expiry_type in EXPIRIES:
            for width_steps in WIDTHS:
                for hold_minutes in HOLDS:
                    variant = json.dumps(
                        {
                            "break_pct": row.break_pct,
                            "expiry_type": expiry_type,
                            "hold_minutes": hold_minutes,
                            "or_minutes": row.or_minutes,
                            "reentry_pct": row.reentry_pct,
                            "width_steps": width_steps,
                        },
                        sort_keys=True,
                    )
                    base.append(
                        {
                            "trade_date": row.trade_date,
                            "signal_time": row.signal_time,
                            "signal_spot": row.signal_spot,
                            "direction": row.direction,
                            "event": row.event,
                            "or_high": row.or_high,
                            "or_low": row.or_low,
                            "or_minutes": row.or_minutes,
                            "break_pct": row.break_pct,
                            "reentry_pct": row.reentry_pct,
                            "expiry_type": expiry_type,
                            "width_steps": width_steps,
                            "hold_minutes": hold_minutes,
                            "entry_anchor": row.entry_anchor,
                            "variant": variant,
                        }
                    )
    out = pd.DataFrame(base)
    out["trade_id"] = np.arange(len(out), dtype=int)
    return out


def indexed_groups(raw: pd.DataFrame) -> dict:
    maps = {}
    for key, g in raw.groupby(["trade_date", "expiry_type"], sort=False):
        opt_maps = {}
        for opt_type, og in g.groupby("option_type", sort=False):
            pivot = (
                og.pivot_table(
                    index="datetime_ist",
                    columns="strike_price",
                    values="close",
                    aggfunc="last",
                )
                .sort_index()
            )
            opt_maps[opt_type] = pivot
        maps[key] = opt_maps
    return maps


def choose_entries(events: pd.DataFrame, groups: dict) -> pd.DataFrame:
    if events.empty:
        return pd.DataFrame()

    # Entry choice depends on signal/event/expiry, not width or hold.
    rows = []
    for key, eg in events.groupby(
        ["trade_date", "signal_time", "direction", "expiry_type", "signal_spot"],
        sort=False,
    ):
        trade_date, signal_time, direction, expiry_type, signal_spot = key
        pivot = groups.get((trade_date, expiry_type), {}).get(direction)
        if pivot is None or pivot.empty:
            continue

        anchor = eg["entry_anchor"].iloc[0]
        idx = pivot.index
        pos = int(idx.searchsorted(anchor, side="left"))
        if pos >= len(idx):
            continue
        entry_time = idx[pos]
        if entry_time > anchor + pd.Timedelta(minutes=2):
            continue

        q = pivot.loc[entry_time]
        strikes = [float(s) for s in q.index if pd.notna(q.loc[s])]
        if not strikes:
            continue
        atm = min(strikes, key=lambda k: abs(k - float(signal_spot)))

        for width_steps in eg["width_steps"].unique():
            if direction == "CALL":
                wings = sorted(k for k in strikes if k > atm)
            else:
                wings = sorted((k for k in strikes if k < atm), reverse=True)
            if len(wings) < int(width_steps):
                continue
            wing = float(wings[int(width_steps) - 1])
            le = q.loc[atm]
            se = q.loc[wing]
            if pd.isna(le) or pd.isna(se):
                continue

            mask = eg["width_steps"].eq(width_steps)
            for row in eg.loc[mask].itertuples(index=False):
                rows.append(
                    {
                        **row._asdict(),
                        "entry_time": entry_time,
                        "atm_strike": float(atm),
                        "wing_strike": wing,
                        "long_entry": float(le),
                        "short_entry": float(se),
                    }
                )
    return pd.DataFrame(rows)


def simulate_paths(entries: pd.DataFrame, groups: dict) -> pd.DataFrame:
    if entries.empty:
        return pd.DataFrame()

    setup_cols = [
        "trade_date",
        "expiry_type",
        "entry_time",
        "direction",
        "atm_strike",
        "wing_strike",
        "hold_minutes",
    ]
    setups = entries.drop_duplicates(setup_cols).reset_index(drop=True)
    paths = []

    for row in setups.itertuples(index=False):
        pivot = groups.get((row.trade_date, row.expiry_type), {}).get(row.direction)
        if pivot is None or row.atm_strike not in pivot.columns or row.wing_strike not in pivot.columns:
            continue

        end = row.entry_time + pd.Timedelta(minutes=int(row.hold_minutes))
        path = pivot.loc[
            (pivot.index >= row.entry_time) & (pivot.index <= end),
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

        z = path.loc[exit_time]
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
                "long_exit": float(z.iloc[0]),
                "short_exit": float(z.iloc[1]),
                "exit_time": exit_time,
                "exit_reason": reason,
                "debit": debit,
            }
        )

    if not paths:
        return pd.DataFrame()
    return entries.merge(
        pd.DataFrame(paths),
        on=setup_cols + ["long_entry", "short_entry"],
        how="inner",
        suffixes=("", "_path"),
    )


def attach_pnl(trades: pd.DataFrame, slippage: float) -> pd.DataFrame:
    if trades.empty:
        return trades
    cm = OptionCostModel()
    out = trades.copy()
    out["lot_size"] = out["trade_date"].map(nifty_lot_size)
    out["net_pnl"] = [
        cm.vertical_debit_spread_net_pnl(
            le, se, lx, sx, int(lot), slippage_points=slippage
        )
        for le, se, lx, sx, lot in zip(
            out["long_entry"], out["short_entry"], out["long_exit"], out["short_exit"], out["lot_size"]
        )
    ]
    return out


def diagnostics(signals: pd.DataFrame, spot: pd.DataFrame) -> pd.DataFrame:
    if signals.empty:
        return pd.DataFrame()

    s = signals[["trade_date", "signal_time", "direction", "event", "signal_spot"]].drop_duplicates()
    base = spot.sort_values(["trade_date", "datetime_ist"]).copy()
    base["fwd15"] = base.groupby("trade_date")["spot"].shift(-15)
    base["fwd30"] = base.groupby("trade_date")["spot"].shift(-30)
    base["fwd60"] = base.groupby("trade_date")["spot"].shift(-60)

    m = s.merge(
        base[["trade_date", "datetime_ist", "spot", "fwd15", "fwd30", "fwd60"]],
        left_on=["trade_date", "signal_time"],
        right_on=["trade_date", "datetime_ist"],
        how="left",
    )
    m["fwd_15_return_pct"] = (m["fwd15"] / m["signal_spot"] - 1.0) * 100.0
    m["fwd_30_return_pct"] = (m["fwd30"] / m["signal_spot"] - 1.0) * 100.0
    m["fwd_60_return_pct"] = (m["fwd60"] / m["signal_spot"] - 1.0) * 100.0
    return m.drop(columns=["datetime_ist"]).dropna(subset=["fwd_15_return_pct"], how="all")


def run(root: Path, out: Path) -> dict:
    con = duckdb.connect()
    spot = con.execute(spot_query(root)).df()
    raw = con.execute(raw_query(root)).df()
    con.close()

    spot["datetime_ist"] = pd.to_datetime(spot["datetime_ist"])
    raw["datetime_ist"] = pd.to_datetime(raw["datetime_ist"])

    events = build_base_events(spot)
    signals = expand_events(events)
    groups = indexed_groups(raw)
    entries = choose_entries(signals, groups)
    trades = simulate_paths(entries, groups)

    out.mkdir(parents=True, exist_ok=True)
    events.to_csv(out / "phase3i_base_events.csv", index=False)
    signals.to_csv(out / "phase3i_signals.csv", index=False)
    diagnostics(signals, spot).to_csv(out / "phase3i_diagnostics.csv", index=False)
    trades.to_csv(out / "phase3i_trades.csv", index=False)

    summary = {
        "features": int(len(spot)),
        "base_events": int(len(events)),
        "signals": int(len(signals)),
        "entries": int(len(entries)),
        "trades": int(len(trades)),
        "variants": len(parameter_grid()),
        "runs": {},
    }

    for slip in (0.20, 0.40):
        scored = attach_pnl(trades, slip)
        tag = f"s{str(slip).replace('.', '_')}"
        d = out / tag
        d.mkdir(exist_ok=True)

        board, prelim = summarize(scored, int(spot["trade_date"].nunique()))
        board.to_csv(d / "leaderboard.csv", index=False)
        wf, wf_summary = walk_forward(scored)
        wf.to_csv(d / "walk_forward.csv", index=False)
        run_summary = {
            "slippage_points": slip,
            "preliminary": prelim,
            "walk_forward": wf_summary,
            "gate": wf_summary.get("gate", prelim.get("gate")),
        }
        (d / "summary.json").write_text(json.dumps(run_summary, indent=2, default=str))
        summary["runs"][str(slip)] = run_summary

    (out / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print(json.dumps(summary, indent=2, default=str))
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=Path("reports/phase3i"))
    args = ap.parse_args()
    run(args.data, args.out)


if __name__ == "__main__":
    main()
