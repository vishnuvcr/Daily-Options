from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from research.contracts import nifty_lot_size
from research.cost_model import OptionCostModel


OR_MINUTES = (5, 15, 30)
BREAK_PCTS = (0.0005, 0.0010)
REENTRY_PCTS = (0.0002, 0.0005)
EXPIRIES = ("WEEK", "MONTH")
WIDTHS = (1, 2)
HOLDS = (15, 30, 60)


@dataclass(frozen=True)
class Variant:
    or_minutes: int
    break_pct: float
    reentry_pct: float
    expiry_type: str
    width_steps: int
    hold_minutes: int

    def key(self) -> str:
        return json.dumps(
            {
                "or_minutes": self.or_minutes,
                "break_pct": self.break_pct,
                "reentry_pct": self.reentry_pct,
                "expiry_type": self.expiry_type,
                "width_steps": self.width_steps,
                "hold_minutes": self.hold_minutes,
            },
            sort_keys=True,
        )


def parameter_grid() -> list[Variant]:
    return [
        Variant(or_m, br, re, ex, w, h)
        for or_m in OR_MINUTES
        for br in BREAK_PCTS
        for re in REENTRY_PCTS
        for ex in EXPIRIES
        for w in WIDTHS
        for h in HOLDS
    ]


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


def raw_query(root: Path) -> str:
    g = parquet_glob(root)
    return f"""
    SELECT
      datetime + INTERVAL '5 hours 30 minutes' AS datetime_ist,
      CAST(date AS DATE) AS trade_date,
      expiry_type,
      option_type,
      CAST(strike_price AS DOUBLE) AS strike_price,
      CAST(close AS DOUBLE) AS close
    FROM read_parquet('{g}', union_by_name=true)
    WHERE close > 0
      AND STRFTIME(datetime + INTERVAL '5 hours 30 minutes','%H:%M:%S')
          BETWEEN '09:15:00' AND '14:45:00'
    """


def build_signal_rows(spot: pd.DataFrame, params: list[Variant]) -> pd.DataFrame:
    if spot.empty:
        return pd.DataFrame()

    spot = spot.copy()
    spot["datetime_ist"] = pd.to_datetime(spot["datetime_ist"])

    rows: list[dict] = []
    for p in params:
        for trade_date, g in spot.groupby("trade_date", sort=True):
            g = g.sort_values("datetime_ist").reset_index(drop=True)
            if g.empty:
                continue

            day_open = pd.Timestamp(f"{trade_date} 09:15:00")
            or_end = day_open + pd.Timedelta(minutes=p.or_minutes - 1)
            opening = g.loc[
                (g["datetime_ist"] >= day_open)
                & (g["datetime_ist"] <= or_end),
                "spot",
            ]
            if len(opening) < max(3, p.or_minutes // 2):
                continue

            or_high = float(opening.max())
            or_low = float(opening.min())

            after = g.loc[g["datetime_ist"] > or_end].copy()
            down_seen = False
            up_seen = False
            chosen = None

            for row in after.itertuples(index=False):
                px = float(row.spot)
                ts = row.datetime_ist

                if not down_seen and px <= or_low * (1.0 - p.break_pct):
                    down_seen = True
                    continue
                if not up_seen and px >= or_high * (1.0 + p.break_pct):
                    up_seen = True
                    continue

                if down_seen and px >= or_low * (1.0 + p.reentry_pct):
                    chosen = ("CALL", ts, px, "downside_false_break")
                    break
                if up_seen and px <= or_high * (1.0 - p.reentry_pct):
                    chosen = ("PUT", ts, px, "upside_false_break")
                    break

            if chosen is None:
                continue

            direction, signal_time, spot_px, event = chosen
            rows.append(
                {
                    "trade_date": trade_date,
                    "signal_time": signal_time,
                    "signal_spot": float(spot_px),
                    "direction": direction,
                    "event": event,
                    "or_high": or_high,
                    "or_low": or_low,
                    "variant": p.key(),
                    "or_minutes": p.or_minutes,
                    "break_pct": p.break_pct,
                    "reentry_pct": p.reentry_pct,
                    "hold_minutes": p.hold_minutes,
                    "expiry_type": p.expiry_type,
                    "width_steps": p.width_steps,
                    "entry_anchor": signal_time + pd.Timedelta(minutes=1),
                }
            )
    return pd.DataFrame(rows)


def grouped_raw(raw: pd.DataFrame) -> dict:
    return {
        key: g.sort_values("datetime_ist").copy()
        for key, g in raw.groupby(["trade_date", "expiry_type"], sort=False)
    }


def choose_entries(signals: pd.DataFrame, raw: pd.DataFrame) -> pd.DataFrame:
    if signals.empty:
        return pd.DataFrame()

    groups = grouped_raw(raw)
    rows = []
    for row in signals.itertuples(index=False):
        g = groups.get((row.trade_date, row.expiry_type))
        if g is None:
            continue
        q = g.loc[
            (g["datetime_ist"] >= row.entry_anchor)
            & (g["datetime_ist"] <= row.entry_anchor + pd.Timedelta(minutes=2))
            & (g["option_type"] == row.direction)
        ]
        if q.empty:
            continue

        entry_time = q["datetime_ist"].min()
        q = q.loc[q["datetime_ist"].eq(entry_time)]
        strikes = sorted(q["strike_price"].dropna().unique())
        if not strikes:
            continue

        atm = min(strikes, key=lambda k: abs(float(k) - float(row.signal_spot)))
        if row.direction == "CALL":
            wings = sorted(k for k in strikes if k > atm)
        else:
            wings = sorted((k for k in strikes if k < atm), reverse=True)
        if len(wings) < int(row.width_steps):
            continue

        wing = float(wings[int(row.width_steps) - 1])
        le = q.loc[np.isclose(q["strike_price"], atm), "close"]
        se = q.loc[np.isclose(q["strike_price"], wing), "close"]
        if le.empty or se.empty:
            continue

        rows.append(
            {
                **row._asdict(),
                "entry_time": entry_time,
                "atm_strike": float(atm),
                "wing_strike": wing,
                "long_entry": float(le.iloc[0]),
                "short_entry": float(se.iloc[0]),
            }
        )
    return pd.DataFrame(rows)


def simulate_paths(entries: pd.DataFrame, raw: pd.DataFrame) -> pd.DataFrame:
    if entries.empty:
        return pd.DataFrame()

    groups = grouped_raw(raw)
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

    out = []
    for row in setups.itertuples(index=False):
        g = groups.get((row.trade_date, row.expiry_type))
        if g is None:
            continue
        end_time = row.entry_time + pd.Timedelta(minutes=int(row.hold_minutes))
        q = g.loc[
            (g["datetime_ist"] >= row.entry_time)
            & (g["datetime_ist"] <= end_time)
            & (g["option_type"] == row.direction)
            & g["strike_price"].isin([row.atm_strike, row.wing_strike])
        ]
        if q.empty:
            continue

        pivot = q.pivot_table(
            index="datetime_ist",
            columns="strike_price",
            values="close",
            aggfunc="last",
        ).sort_index().dropna(
            subset=[row.atm_strike, row.wing_strike]
        )
        if pivot.empty or row.entry_time not in pivot.index:
            continue

        spread = pivot[row.atm_strike] - pivot[row.wing_strike]
        debit = float(spread.loc[row.entry_time])
        if not np.isfinite(debit) or debit <= 0:
            continue

        stop = 0.50 * debit
        target = 1.75 * debit
        path = spread.loc[spread.index >= row.entry_time]
        exit_time = path.index[-1]
        exit_reason = "time"

        for dt, value in path.iloc[1:].items():
            v = float(value)
            if v <= stop:
                exit_time, exit_reason = dt, "stop"
                break
            if v >= target:
                exit_time, exit_reason = dt, "target"
                break

        exit_row = pivot.loc[exit_time]
        out.append(
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
                "exit_reason": exit_reason,
                "debit": debit,
            }
        )

    if not out:
        return pd.DataFrame()

    paths = pd.DataFrame(out)
    return entries.merge(
        paths,
        on=setup_cols + ["long_entry", "short_entry"],
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
            le,
            se,
            lx,
            sx,
            int(lot),
            slippage_points=slippage_points,
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


def summarize(trades: pd.DataFrame, calendar_days: int) -> tuple[pd.DataFrame, dict]:
    if trades.empty:
        return pd.DataFrame(), {"gate": "NO_TRADES"}

    rows = []
    for variant, g in trades.groupby("variant", sort=False):
        daily = g.groupby("trade_date")["net_pnl"].sum()
        gains = g.loc[g["net_pnl"] > 0, "net_pnl"].sum()
        losses = -g.loc[g["net_pnl"] < 0, "net_pnl"].sum()
        rows.append(
            {
                "variant": variant,
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
        "gate": "PASS_PRELIMINARY"
        if bool((board["mean_all_day_net"] >= 1000).any())
        else "FAIL_PRELIMINARY"
    }


def walk_forward(trades: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    if trades.empty:
        return pd.DataFrame(), {"gate": "NO_TRADES"}

    trades = trades.copy()
    trades["trade_date"] = pd.to_datetime(trades["trade_date"]).dt.date
    dates = sorted(trades["trade_date"].unique())

    train_len, val_len, embargo, test_len, step = 180, 60, 5, 60, 60
    results = []
    start = 0

    while start + train_len + val_len + embargo + test_len <= len(dates):
        train_dates = set(dates[start : start + train_len])
        val_dates = set(dates[start + train_len : start + train_len + val_len])
        test_start = start + train_len + val_len + embargo
        test_dates = set(dates[test_start : test_start + test_len])

        train = trades[trades["trade_date"].isin(train_dates)]
        val = trades[trades["trade_date"].isin(val_dates)]
        test = trades[trades["trade_date"].isin(test_dates)]

        train_scores = []
        for variant, vg in train.groupby("variant"):
            if len(vg) < 10:
                continue
            train_scores.append(
                (variant, float(vg.groupby("trade_date")["net_pnl"].sum().mean()))
            )

        if not train_scores:
            start += step
            continue

        train_scores.sort(key=lambda z: z[1], reverse=True)
        val_scores = []

        for variant, _ in train_scores[:12]:
            vg = val[val["variant"].eq(variant)]
            if len(vg) < 5:
                continue
            val_scores.append(
                (variant, float(vg.groupby("trade_date")["net_pnl"].sum().mean()))
            )

        if not val_scores:
            start += step
            continue

        val_scores.sort(key=lambda z: z[1], reverse=True)
        selected = val_scores[0][0]
        tg = test[test["variant"].eq(selected)]
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
    summary = {
        "walk_forward_windows": int(len(out)),
        "positive_test_windows": int((out["test_mean"] > 0).sum()) if not out.empty else 0,
        "target_qualified_windows": int((out["test_mean"] >= 1000).sum()) if not out.empty else 0,
        "mean_test_window_net": float(out["test_mean"].mean()) if not out.empty else None,
        "median_test_window_net": float(out["test_mean"].median()) if not out.empty else None,
        "gate": (
            "PASS_PRELIMINARY"
            if (
                not out.empty
                and out["test_mean"].mean() > 0
                and (out["test_mean"] >= 1000).any()
            )
            else "FAIL_PRELIMINARY"
        ),
    }
    return out, summary


def diagnostics(signals: pd.DataFrame, spot: pd.DataFrame) -> pd.DataFrame:
    if signals.empty:
        return pd.DataFrame()

    s = signals[["trade_date", "signal_time", "signal_spot", "direction", "event", "variant"]].copy()
    spot = spot.sort_values(["trade_date", "datetime_ist"]).copy()
    rows = []

    for row in s.itertuples(index=False):
        g = spot.loc[spot["trade_date"].eq(row.trade_date)]
        future = g.loc[g["datetime_ist"] > row.signal_time].head(60)
        if future.empty:
            continue
        px0 = float(row.signal_spot)
        vals = future["spot"].to_numpy(float)
        rows.append(
            {
                "trade_date": row.trade_date,
                "signal_time": row.signal_time,
                "direction": row.direction,
                "event": row.event,
                "fwd_15_return_pct": float((vals[min(14, len(vals)-1)] / px0 - 1.0) * 100.0),
                "fwd_30_return_pct": float((vals[min(29, len(vals)-1)] / px0 - 1.0) * 100.0),
                "fwd_60_return_pct": float((vals[min(59, len(vals)-1)] / px0 - 1.0) * 100.0),
            }
        )
    return pd.DataFrame(rows)


def run(data_root: Path, out_root: Path) -> dict:
    con = duckdb.connect()
    spot = con.execute(spot_query(data_root)).df()
    raw = con.execute(raw_query(data_root)).df()
    con.close()

    spot["datetime_ist"] = pd.to_datetime(spot["datetime_ist"])
    raw["datetime_ist"] = pd.to_datetime(raw["datetime_ist"])

    params = parameter_grid()
    signals = build_signal_rows(spot, params)
    entries = choose_entries(signals, raw)
    trades = simulate_paths(entries, raw)

    out_root.mkdir(parents=True, exist_ok=True)
    signals.to_csv(out_root / "phase3i_signals.csv", index=False)
    diagnostics(signals, spot).to_csv(out_root / "phase3i_diagnostics.csv", index=False)
    trades.to_csv(out_root / "phase3i_trades.csv", index=False)

    result = {
        "features": int(len(spot)),
        "signals": int(len(signals)),
        "entries": int(len(entries)),
        "trades": int(len(trades)),
        "variants": len(params),
        "runs": {},
    }

    for slip in (0.20, 0.40):
        scored = attach_pnl(trades, slip)
        tag = f"s{str(slip).replace('.', '_')}"
        d = out_root / tag
        d.mkdir(exist_ok=True)

        board, preliminary = summarize(scored, int(spot["trade_date"].nunique()))
        board.to_csv(d / "leaderboard.csv", index=False)
        wf, wf_summary = walk_forward(scored)
        wf.to_csv(d / "walk_forward.csv", index=False)

        summary = {
            "slippage_points": slip,
            "preliminary": preliminary,
            "walk_forward": wf_summary,
            "gate": wf_summary.get("gate", preliminary.get("gate")),
        }
        (d / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
        result["runs"][str(slip)] = summary

    (out_root / "summary.json").write_text(json.dumps(result, indent=2, default=str))
    print(json.dumps(result, indent=2, default=str))
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=Path("reports/phase3i"))
    args = ap.parse_args()
    run(args.data, args.out)


if __name__ == "__main__":
    main()
