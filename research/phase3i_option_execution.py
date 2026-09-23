from __future__ import annotations

import argparse
import json
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from research.contracts import nifty_lot_size
from research.cost_model import OptionCostModel
from research.phase3i_futures_spot_lead_lag import (
    build_features,
    identify_spot_futures,
)
from research.zenodo_option_source import (
    ContractFile,
    discover_option_files,
    read_contract_file,
)

OPTION_DATA_REVISION = "10.5281/zenodo.10899828-options-2017-2020"
IST_OFFSET = pd.Timedelta(hours=5, minutes=30)

SIGNAL_SPECS = (
    {"feature": "lead_gap", "lookback": 3, "threshold_bps": 10.0, "mode": "continuation"},
    {"feature": "basis_change", "lookback": 3, "threshold_bps": 10.0, "mode": "continuation"},
)
EXPIRIES = ("WEEK", "MONTH")
WIDTH_STEPS = (1, 2)
HOLDS = (5, 10, 15)


def signal_variant_key(spec: dict) -> str:
    return json.dumps(spec, sort_keys=True)


def build_signal_events(spot: pd.DataFrame, futures: pd.DataFrame) -> pd.DataFrame:
    features = build_features(spot, futures)
    rows: list[dict] = []
    next_id = 0

    for spec in SIGNAL_SPECS:
        key = signal_variant_key(spec)
        raw = (
            features[f"lead_gap_{spec['lookback']}_bps"]
            if spec["feature"] == "lead_gap"
            else features[f"basis_change_{spec['lookback']}_bps"]
        )
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
                    "direction": row.direction,
                    "spot": float(row.spot),
                    "signal_value_bps": float(row.raw_signal_bps),
                }
            )
            next_id += 1

    return pd.DataFrame(rows)


class OptionReader:
    def __init__(self, index: list[ContractFile]):
        self.index = index
        self._cache: dict[str, pd.DataFrame] = {}

    @lru_cache(maxsize=4096)
    def load(self, path: str) -> pd.DataFrame:
        out = read_contract_file(Path(path))
        return out

    def available_expiry_types(self) -> tuple[str, ...]:
        present = {x.expiry_type for x in self.index}
        return tuple(x for x in EXPIRIES if x in present)

    def candidate_contracts(
        self,
        trade_date,
        expiry_type: str,
        direction: str,
        spot: float,
    ) -> tuple[date | None, list[ContractFile]]:
        choices = [
            x for x in self.index
            if x.option_type == direction and x.expiry_type == expiry_type and x.expiry_date >= trade_date
        ]
        if not choices:
            return None, []

        expiry = min(x.expiry_date for x in choices)
        same_expiry = [x for x in choices if x.expiry_date == expiry]
        strikes = sorted({x.strike for x in same_expiry})
        near = [s for s in strikes if abs(s - float(spot)) <= 500.0]
        if not near:
            near = sorted(strikes, key=lambda s: abs(s - float(spot)))[:7]

        paths = [x for x in same_expiry if x.strike in near]
        return expiry, paths

    def paired_entry(
        self,
        signal,
        expiry_type: str,
    ) -> tuple[dict | None, list[str]]:
        expiry, contracts = self.candidate_contracts(
            signal.trade_date,
            expiry_type,
            signal.direction,
            float(signal.spot),
        )
        if expiry is None or not contracts:
            return None, []

        by_strike = {}
        anchor = pd.Timestamp(signal.entry_anchor_local)
        end = anchor + pd.Timedelta(minutes=2)

        for c in contracts:
            df = self.load(c.path)
            q = df.loc[
                (df["trade_date"] == signal.trade_date) &
                (df["datetime_local"] >= anchor) &
                (df["datetime_local"] <= end),
                ["datetime_local", "close"],
            ].copy()
            if not q.empty:
                q = q.groupby("datetime_local", as_index=False)["close"].last()
                by_strike.setdefault(c.strike, []).append(q)

        if not by_strike:
            return None, []

        strikes = sorted(by_strike)
        atm = min(strikes, key=lambda s: abs(float(s) - float(signal.spot)))
        if signal.direction == "CALL":
            wings = sorted(s for s in strikes if s > atm)
        else:
            wings = sorted((s for s in strikes if s < atm), reverse=True)
        if len(wings) < max(WIDTH_STEPS):
            return None, [f"expiry={expiry} missing OTM strikes for {signal.direction}"]

        merged = {}
        for strike, frames in by_strike.items():
            merged[strike] = pd.concat(frames, ignore_index=True).sort_values("datetime_local").drop_duplicates("datetime_local", keep="last")

        rows = []
        base = {
            "trade_id": int(signal.trade_id),
            "signal_variant": signal.signal_variant,
            "trade_date": signal.trade_date,
            "expiry_type": expiry_type,
            "expiry_date": expiry,
            "direction": signal.direction,
            "signal_time_local": signal.signal_time_local,
            "spot": float(signal.spot),
            "atm_strike": float(atm),
        }

        for width in WIDTH_STEPS:
            wing = float(wings[width - 1])
            pair = merged[atm].rename(columns={"close": "long_entry"}).merge(
                merged[wing].rename(columns={"close": "short_entry"}),
                on="datetime_local",
                how="inner",
            )
            if pair.empty:
                continue
            pair = pair.sort_values("datetime_local")
            entry_time = pair["datetime_local"].iloc[0]
            le = float(pair["long_entry"].iloc[0])
            se = float(pair["short_entry"].iloc[0])
            if not np.isfinite(le) or not np.isfinite(se) or le <= se:
                continue
            rows.append(
                {
                    **base,
                    "width_steps": int(width),
                    "entry_time_local": entry_time,
                    "entry_time_utc": entry_time - IST_OFFSET,
                    "long_entry": le,
                    "short_entry": se,
                    "debit": le - se,
                }
            )
        if not rows:
            return None, [f"expiry={expiry} no positive debit spread at common entry"]
        return rows, []


def build_entries(signals: pd.DataFrame, reader: OptionReader) -> tuple[pd.DataFrame, dict]:
    if signals.empty:
        return pd.DataFrame(), {"signals": 0, "attempts": 0, "success_rows": 0}

    expiry_types = reader.available_expiry_types()
    rows = []
    diagnostics = {
        "signals": int(len(signals)),
        "attempts": 0,
        "success_rows": 0,
        "available_expiry_types": list(expiry_types),
        "no_expiry": 0,
        "no_quotes_or_strikes": 0,
        "no_positive_debit": 0,
    }

    for signal in signals.itertuples(index=False):
        for expiry_type in expiry_types:
            diagnostics["attempts"] += 1
            entries, notes = reader.paired_entry(signal, expiry_type)
            if entries is None:
                diagnostics["no_quotes_or_strikes"] += 1
                if notes and "no positive debit" in notes[0]:
                    diagnostics["no_positive_debit"] += 1
                continue
            rows.extend(entries)

    diagnostics["success_rows"] = len(rows)
    return (pd.DataFrame(rows) if rows else pd.DataFrame()), diagnostics


def simulate(entries: pd.DataFrame, reader: OptionReader) -> pd.DataFrame:
    if entries.empty:
        return pd.DataFrame()

    rows = []
    for row in entries.itertuples(index=False):
        expiry = row.expiry_date
        candidates = [
            x for x in reader.index
            if x.expiry_date == expiry and x.expiry_type == row.expiry_type and x.option_type == row.direction
            and x.strike in {float(row.atm_strike), float(row.wing_strike)}
        ]
        by_strike = {}
        start = pd.Timestamp(row.entry_time_local)
        for c in candidates:
            df = reader.load(c.path)
            q = df.loc[
                (df["trade_date"] == row.trade_date) &
                (df["datetime_local"] >= start) &
                (df["datetime_local"] <= start + pd.Timedelta(minutes=max(HOLDS))),
                ["datetime_local", "close"],
            ].copy()
            if not q.empty:
                by_strike[c.strike] = q.groupby("datetime_local", as_index=False)["close"].last()

        if row.atm_strike not in by_strike or row.wing_strike not in by_strike:
            continue

        paired = by_strike[row.atm_strike].rename(columns={"close": "long_close"}).merge(
            by_strike[row.wing_strike].rename(columns={"close": "short_close"}),
            on="datetime_local",
            how="inner",
        ).sort_values("datetime_local")

        entry_pair = paired.loc[paired["datetime_local"].eq(start)]
        if entry_pair.empty:
            continue

        for hold in HOLDS:
            deadline = start + pd.Timedelta(minutes=hold)
            eligible = paired.loc[
                (paired["datetime_local"] >= start) &
                (paired["datetime_local"] <= deadline)
            ]
            if eligible.empty:
                continue

            exit_time = eligible["datetime_local"].max()
            if deadline - exit_time > pd.Timedelta(minutes=1):
                continue

            ep = entry_pair.iloc[0]
            xp = eligible.loc[eligible["datetime_local"].eq(exit_time)].iloc[0]
            rows.append(
                {
                    "variant_id": f"{row.signal_variant}::{row.expiry_type}::{row.width_steps}::{hold}",
                    "trade_id": int(row.trade_id),
                    "signal_variant": row.signal_variant,
                    "trade_date": row.trade_date,
                    "expiry_type": row.expiry_type,
                    "expiry_date": row.expiry_date,
                    "entry_time_local": start,
                    "entry_time_utc": start - IST_OFFSET,
                    "exit_time_local": exit_time,
                    "exit_time_utc": exit_time - IST_OFFSET,
                    "direction": row.direction,
                    "atm_strike": float(row.atm_strike),
                    "wing_strike": float(row.wing_strike),
                    "width_steps": int(row.width_steps),
                    "hold_minutes": int(hold),
                    "long_entry": float(ep.long_close),
                    "short_entry": float(ep.short_close),
                    "long_exit": float(xp.long_close),
                    "short_exit": float(xp.short_close),
                    "debit": float(ep.long_close - ep.short_close),
                    "exit_spread": float(xp.long_close - xp.short_close),
                    "effective_hold_minutes": float((exit_time - start).total_seconds() / 60.0),
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

    index_path = options_root.parent / "option_index.json"
    option_index = discover_option_files(options_root, index_path=index_path)
    reader = OptionReader(option_index)

    entries, entry_diag = build_entries(signals, reader)
    trades = attach_pnl(simulate(entries, reader), slippage_points)

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "phase3i_option_source.json").write_text(
        json.dumps(
            {
                "revision": OPTION_DATA_REVISION,
                "signal_source": source_meta,
                "option_files_indexed": len(option_index),
                "available_expiry_types": list(reader.available_expiry_types()),
        "source_common_trading_days": calendar_days,
        "source_date_min": str(min(common_dates)) if common_dates else None,
        "source_date_max": str(max(common_dates)) if common_dates else None,
                "entry_diagnostics": entry_diag,
            },
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )
    signals.to_csv(out_dir / "phase3i_signals.csv", index=False)
    entries.to_csv(out_dir / "phase3i_entries.csv", index=False)
    trades.to_csv(out_dir / "phase3i_trades.csv", index=False)

    common_dates = set(spot["trade_date"]).intersection(set(fut["trade_date"]))
    calendar_days = int(len(common_dates))
    board, preliminary = summarize(trades, calendar_days)
    board.to_csv(out_dir / "phase3i_leaderboard.csv", index=False)

    wf, wf_summary = walk_forward(trades)
    wf.to_csv(out_dir / "phase3i_walk_forward.csv", index=False)

    variants = len(SIGNAL_SPECS) * len(reader.available_expiry_types()) * len(WIDTH_STEPS) * len(HOLDS)
    summary = {
        "option_data_revision": OPTION_DATA_REVISION,
        "signals": int(len(signals)),
        "option_files_indexed": int(len(option_index)),
        "available_expiry_types": list(reader.available_expiry_types()),
        "entry_rows": int(len(entries)),
        "trades": int(len(trades)),
        "variants": variants,
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
