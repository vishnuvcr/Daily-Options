from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from research.contracts import nifty_lot_size
from research.cost_model import OptionCostModel
from research.phase3i_futures_spot_lead_lag import (
    build_features,
    identify_spot_futures,
)

OPTION_DATA_REVISION = "45e0a04"
IST_OFFSET = pd.Timedelta(hours=5, minutes=30)

SIGNAL_SPECS = (
    {"feature": "lead_gap", "lookback": 3, "threshold_bps": 10.0, "mode": "continuation"},
    {"feature": "basis_change", "lookback": 3, "threshold_bps": 10.0, "mode": "continuation"},
)
EXPIRIES = ("WEEK", "MONTH")
WIDTH_STEPS = (1, 2)
HOLDS = (5, 10, 15)

SETUP_COLS = [
    "trade_id",
    "signal_variant",
    "trade_date",
    "expiry_type",
    "entry_time_utc",
    "direction",
    "atm_strike",
    "wing_strike",
    "hold_minutes",
]


def signal_variant_key(spec: dict) -> str:
    return json.dumps(spec, sort_keys=True)


def build_signal_events(spot: pd.DataFrame, futures: pd.DataFrame) -> pd.DataFrame:
    features = build_features(spot, futures)
    rows = []
    next_id = 0

    for spec in SIGNAL_SPECS:
        key = signal_variant_key(spec)
        if spec["feature"] == "lead_gap":
            raw = features[f"lead_gap_{spec['lookback']}_bps"]
        elif spec["feature"] == "basis_change":
            raw = features[f"basis_change_{spec['lookback']}_bps"]
        else:
            raise ValueError(spec["feature"])

        x = features.loc[raw.abs().ge(spec["threshold_bps"])].copy()
        x["raw_signal_bps"] = raw.loc[x.index]
        x["direction"] = np.where(x["raw_signal_bps"] > 0, "CALL", "PUT")
        x = x.sort_values(["trade_date", "datetime"]).drop_duplicates(["trade_date"], keep="first")

        for row in x.itertuples(index=False):
            rows.append(
                {
                    "trade_id": next_id,
                    "signal_variant": key,
                    "trade_date": row.trade_date,
                    "signal_time_local": row.datetime,
                    "entry_anchor_local": row.datetime + pd.Timedelta(minutes=1),
                    "entry_anchor_utc": row.datetime + pd.Timedelta(minutes=1) - IST_OFFSET,
                    "direction": row.direction,
                    "spot": float(row.spot),
                    "signal_value_bps": float(row.raw_signal_bps),
                }
            )
            next_id += 1

    return pd.DataFrame(rows)


def _parquet_glob(root: Path) -> str:
    return (root / "**" / "*.parquet").as_posix()


def load_entry_quotes(options_root: Path, signals: pd.DataFrame) -> pd.DataFrame:
    if signals.empty:
        return pd.DataFrame()

    rows = []
    for _, s in signals.iterrows():
        for expiry in EXPIRIES:
            r = s.copy()
            r["expiry_type"] = expiry
            r["setup_id"] = f"{int(s.trade_id)}::{expiry}"
            rows.append(r)
    setups = pd.DataFrame(rows)

    con = duckdb.connect()
    try:
        con.register("phase3i_signal_setups", setups)
        q = f"""
        WITH candidate AS (
          SELECT
            s.setup_id,
            s.trade_id,
            s.signal_variant,
            s.trade_date,
            s.signal_time_local,
            s.direction,
            s.spot AS signal_spot,
            s.expiry_type,
            o.datetime,
            CAST(o.strike_price AS DOUBLE) AS strike_price,
            CAST(o.close AS DOUBLE) AS close
          FROM phase3i_signal_setups s
          JOIN read_parquet('{_parquet_glob(options_root)}', union_by_name=true) o
            ON CAST(o.date AS DATE) = s.trade_date
           AND o.expiry_type = s.expiry_type
           AND o.option_type = s.direction
           AND o.datetime >= s.entry_anchor_utc
           AND o.datetime <= s.entry_anchor_utc + INTERVAL '2 minutes'
          WHERE o.close > 0
        )
        SELECT * FROM candidate
        ORDER BY setup_id, datetime, strike_price
        """
        return con.execute(q).df()
    finally:
        con.close()


def choose_entries(entry_quotes: pd.DataFrame) -> pd.DataFrame:
    if entry_quotes.empty:
        return pd.DataFrame()

    rows = []
    for setup_id, g in entry_quotes.groupby("setup_id", sort=False):
        g = g.sort_values(["datetime", "strike_price"])
        entry_time = g["datetime"].iloc[0]
        q = g.loc[g["datetime"].eq(entry_time)].dropna(subset=["strike_price", "close"]).copy()
        if q.empty:
            continue

        signal_spot = float(q["signal_spot"].iloc[0])
        direction = str(q["direction"].iloc[0])
        strikes = sorted(float(s) for s in q["strike_price"].unique())
        atm = min(strikes, key=lambda k: abs(k - signal_spot))
        if direction == "CALL":
            wings = sorted(k for k in strikes if k > atm)
        else:
            wings = sorted((k for k in strikes if k < atm), reverse=True)

        if len(wings) < max(WIDTH_STEPS):
            continue

        for width in WIDTH_STEPS:
            wing = float(wings[width - 1])
            lp = q.loc[np.isclose(q["strike_price"], atm), "close"]
            sp = q.loc[np.isclose(q["strike_price"], wing), "close"]
            if lp.empty or sp.empty:
                continue
            long_entry = float(lp.iloc[0])
            short_entry = float(sp.iloc[0])
            debit = long_entry - short_entry
            if not np.isfinite(debit) or debit <= 0:
                continue
            rows.append(
                {
                    "setup_id": setup_id,
                    "trade_id": int(g["trade_id"].iloc[0]),
                    "signal_variant": g["signal_variant"].iloc[0],
                    "trade_date": g["trade_date"].iloc[0],
                    "expiry_type": g["expiry_type"].iloc[0],
                    "signal_time_local": g["signal_time_local"].iloc[0],
                    "entry_time_utc": entry_time,
                    "direction": direction,
                    "atm_strike": atm,
                    "wing_strike": wing,
                    "width_steps": width,
                    "long_entry": long_entry,
                    "short_entry": short_entry,
                    "debit": debit,
                }
            )
    return pd.DataFrame(rows)


def load_exit_quotes(options_root: Path, entries: pd.DataFrame) -> pd.DataFrame:
    if entries.empty:
        return pd.DataFrame()

    setups = []
    for hold in HOLDS:
        x = entries.copy()
        x["hold_minutes"] = hold
        x["exit_deadline_utc"] = x["entry_time_utc"] + pd.to_timedelta(hold, unit="m")
        x["variant_id"] = x["setup_id"].astype(str) + f"::{hold}"
        setups.append(x)
    setups = pd.concat(setups, ignore_index=True)

    con = duckdb.connect()
    try:
        con.register("phase3i_option_setups", setups)
        q = f"""
        SELECT
          s.variant_id,
          s.setup_id,
          s.trade_id,
          s.signal_variant,
          s.trade_date,
          s.expiry_type,
          s.entry_time_utc,
          s.exit_deadline_utc,
          s.direction,
          s.atm_strike,
          s.wing_strike,
          s.width_steps,
          s.hold_minutes,
          s.long_entry,
          s.short_entry,
          o.datetime,
          CAST(o.strike_price AS DOUBLE) AS strike_price,
          CAST(o.close AS DOUBLE) AS close
        FROM phase3i_option_setups s
        JOIN read_parquet('{_parquet_glob(options_root)}', union_by_name=true) o
          ON CAST(o.date AS DATE) = s.trade_date
         AND o.expiry_type = s.expiry_type
         AND o.option_type = s.direction
         AND o.datetime >= s.entry_time_utc
         AND o.datetime <= s.exit_deadline_utc
         AND (
           CAST(o.strike_price AS DOUBLE) = s.atm_strike
           OR CAST(o.strike_price AS DOUBLE) = s.wing_strike
         )
        WHERE o.close > 0
        ORDER BY variant_id, datetime, strike_price
        """
        return con.execute(q).df()
    finally:
        con.close()


def simulate(entries: pd.DataFrame, exit_quotes: pd.DataFrame) -> pd.DataFrame:
    if entries.empty or exit_quotes.empty:
        return pd.DataFrame()

    rows = []
    for variant_id, g in exit_quotes.groupby("variant_id", sort=False):
        meta = g.iloc[0]
        pivot = (
            g.pivot_table(index="datetime", columns="strike_price", values="close", aggfunc="last")
            .sort_index()
            .dropna(subset=[meta.atm_strike, meta.wing_strike])
        )
        if pivot.empty or meta.entry_time_utc not in pivot.index:
            continue

        end = meta.exit_deadline_utc
        eligible = pivot.loc[(pivot.index >= meta.entry_time_utc) & (pivot.index <= end)]
        if eligible.empty:
            continue

        entry = float(eligible.loc[meta.entry_time_utc, meta.atm_strike] - eligible.loc[meta.entry_time_utc, meta.wing_strike])
        exit_time = eligible.index[-1]
        if end - exit_time > pd.Timedelta(minutes=1):
            continue

        exit_spread = float(eligible.loc[exit_time, meta.atm_strike] - eligible.loc[exit_time, meta.wing_strike])
        rows.append(
            {
                "variant_id": variant_id,
                "trade_id": int(meta.trade_id),
                "signal_variant": meta.signal_variant,
                "trade_date": meta.trade_date,
                "expiry_type": meta.expiry_type,
                "entry_time_utc": meta.entry_time_utc,
                "entry_time_local": pd.Timestamp(meta.entry_time_utc) + IST_OFFSET,
                "exit_time_utc": exit_time,
                "exit_time_local": exit_time + IST_OFFSET,
                "direction": meta.direction,
                "atm_strike": float(meta.atm_strike),
                "wing_strike": float(meta.wing_strike),
                "width_steps": int(meta.width_steps),
                "hold_minutes": int(meta.hold_minutes),
                "long_entry": float(meta.long_entry),
                "short_entry": float(meta.short_entry),
                "long_exit": float(eligible.loc[exit_time, meta.atm_strike]),
                "short_exit": float(eligible.loc[exit_time, meta.wing_strike]),
                "debit": entry,
                "exit_spread": exit_spread,
                "effective_hold_minutes": float((exit_time - meta.entry_time_utc).total_seconds() / 60.0),
            }
        )

    return pd.DataFrame(rows)


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
            out["long_entry"], out["short_entry"], out["long_exit"], out["short_exit"], out["lot_size"]
        )
    ]
    return out


def summarize(trades: pd.DataFrame, calendar_days: int) -> tuple[pd.DataFrame, dict]:
    if trades.empty:
        return pd.DataFrame(), {"gate": "NO_TRADES"}

    rows = []
    for variant, g in trades.groupby("variant_id", sort=False):
        daily = g.groupby("trade_date")["net_pnl"].sum()
        gains = g.loc[g["net_pnl"] > 0, "net_pnl"].sum()
        losses = -g.loc[g["net_pnl"] < 0, "net_pnl"].sum()
        rows.append(
            {
                "variant": variant,
                "signal_variant": g["signal_variant"].iloc[0],
                "trade_days": int(daily.size),
                "mean_active_day_net": float(daily.mean()),
                "mean_all_day_net": float(g["net_pnl"].sum() / max(calendar_days, 1)),
                "median_day_net": float(daily.median()),
                "win_rate": float((g["net_pnl"] > 0).mean()),
                "positive_day_rate": float((daily > 0).sum() / max(calendar_days, 1)),
                "profit_factor": float(gains / losses) if losses > 0 else 999.0,
                "max_drawdown": float((daily.cumsum() - daily.cumsum().cummax()).min()),
                "total_net": float(g["net_pnl"].sum()),
            }
        )

    board = pd.DataFrame(rows).sort_values(
        ["mean_all_day_net", "positive_day_rate"], ascending=False
    ).reset_index(drop=True)

    return board, {
        "gate": "PASS_PRELIMINARY" if bool((board["mean_all_day_net"] >= 1000).any()) else "FAIL_PRELIMINARY"
    }


def walk_forward(trades: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    if trades.empty:
        return pd.DataFrame(), {"gate": "NO_TRADES"}

    x = trades.copy()
    x["trade_date"] = pd.to_datetime(x["trade_date"]).dt.date
    dates = sorted(x["trade_date"].unique())

    train_len, val_len, embargo, test_len, step = 180, 60, 5, 60, 60
    results = []
    start = 0

    while start + train_len + val_len + embargo + test_len <= len(dates):
        train_dates = set(dates[start:start + train_len])
        val_dates = set(dates[start + train_len:start + train_len + val_len])
        test_start = start + train_len + val_len + embargo
        test_dates = set(dates[test_start:test_start + test_len])

        train = x[x["trade_date"].isin(train_dates)]
        val = x[x["trade_date"].isin(val_dates)]
        test = x[x["trade_date"].isin(test_dates)]

        train_scores = []
        for variant, vg in train.groupby("variant_id"):
            if len(vg) < 10:
                continue
            train_scores.append((variant, float(vg.groupby("trade_date")["net_pnl"].sum().mean())))

        if not train_scores:
            start += step
            continue

        train_scores.sort(key=lambda z: z[1], reverse=True)
        val_scores = []
        for variant, _ in train_scores[:12]:
            vg = val[val["variant_id"].eq(variant)]
            if len(vg) < 5:
                continue
            val_scores.append((variant, float(vg.groupby("trade_date")["net_pnl"].sum().mean())))

        if not val_scores:
            start += step
            continue

        val_scores.sort(key=lambda z: z[1], reverse=True)
        selected = val_scores[0][0]
        tg = test[test["variant_id"].eq(selected)]
        if tg.empty:
            start += step
            continue

        daily = tg.groupby("trade_date")["net_pnl"].sum()
        results.append(
            {
                "test_start": str(min(test_dates)),
                "test_end": str(max(test_dates)),
                "selected_variant": selected,
                "validation_mean": val_scores[0][1],
                "test_mean": float(daily.mean()),
                "test_median": float(daily.median()),
                "positive_day_rate": float((daily > 0).mean()),
                "trade_days": int(daily.size),
            }
        )
        start += step

    out = pd.DataFrame(results)
    if out.empty:
        return out, {
            "walk_forward_windows": 0,
            "positive_test_windows": 0,
            "target_qualified_windows": 0,
            "mean_test_window_net": None,
            "median_test_window_net": None,
            "gate": "FAIL_PRELIMINARY",
        }

    return out, {
        "walk_forward_windows": int(len(out)),
        "positive_test_windows": int((out["test_mean"] > 0).sum()),
        "target_qualified_windows": int((out["test_mean"] >= 1000).sum()),
        "mean_test_window_net": float(out["test_mean"].mean()),
        "median_test_window_net": float(out["test_mean"].median()),
        "gate": (
            "PASS_PRELIMINARY"
            if out["test_mean"].mean() > 0 and (out["test_mean"] >= 1000).any()
            else "FAIL_PRELIMINARY"
        ),
    }


def run(options_root: Path, futures_root: Path, out_dir: Path, slippage_points: float) -> dict:
    spot, fut, source_meta = identify_spot_futures(futures_root)
    signals = build_signal_events(spot, fut)

    entry_quotes = load_entry_quotes(options_root, signals)
    entries = choose_entries(entry_quotes)
    exit_quotes = load_exit_quotes(options_root, entries)
    trades = simulate(entries, exit_quotes)
    trades = attach_pnl(trades, slippage_points)

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "phase3i_option_source.json").write_text(
        json.dumps({"revision": OPTION_DATA_REVISION, "signal_source": source_meta}, indent=2, default=str),
        encoding="utf-8",
    )
    signals.to_csv(out_dir / "phase3i_signals.csv", index=False)
    entries.to_csv(out_dir / "phase3i_entries.csv", index=False)
    trades.to_csv(out_dir / "phase3i_trades.csv", index=False)

    calendar_days = int(signals["trade_date"].nunique()) if not signals.empty else 0
    board, preliminary = summarize(trades, calendar_days)
    board.to_csv(out_dir / "phase3i_leaderboard.csv", index=False)

    wf, wf_summary = walk_forward(trades)
    wf.to_csv(out_dir / "phase3i_walk_forward.csv", index=False)

    summary = {
        "option_data_revision": OPTION_DATA_REVISION,
        "signals": int(len(signals)),
        "entry_rows": int(len(entries)),
        "trades": int(len(trades)),
        "variants": len(SIGNAL_SPECS) * len(EXPIRIES) * len(WIDTH_STEPS) * len(HOLDS),
        "preliminary": preliminary,
        "walk_forward": wf_summary,
        "slippage_points": slippage_points,
        "gate": wf_summary.get("gate", preliminary.get("gate")),
    }
    (out_dir / "phase3i_option_summary.json").write_text(
        json.dumps(summary, indent=2, default=str),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, default=str))
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--options", type=Path, required=True)
    ap.add_argument("--futures", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--slippage", type=float, default=0.20)
    args = ap.parse_args()
    run(args.options, args.futures, args.out, args.slippage)


if __name__ == "__main__":
    main()
