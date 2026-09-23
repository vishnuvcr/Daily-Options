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


LOOKBACKS = (1, 3, 5)
PRESSURE_THRESHOLDS = (0.01, 0.02, 0.03)
EXPIRIES = ("WEEK", "MONTH")
WIDTHS = (1, 2)
HOLDS = (5, 10, 15)


@dataclass(frozen=True)
class Variant:
    lookback: int
    pressure_threshold: float
    expiry_type: str
    width_steps: int
    hold_minutes: int

    def key(self) -> str:
        return json.dumps(
            {
                "lookback": self.lookback,
                "pressure_threshold": self.pressure_threshold,
                "expiry_type": self.expiry_type,
                "width_steps": self.width_steps,
                "hold_minutes": self.hold_minutes,
            },
            sort_keys=True,
        )


def parameter_grid() -> list[Variant]:
    return [
        Variant(lb, th, ex, w, h)
        for lb in LOOKBACKS
        for th in PRESSURE_THRESHOLDS
        for ex in EXPIRIES
        for w in WIDTHS
        for h in HOLDS
    ]


def parquet_glob(root: Path) -> str:
    return (root / "**" / "*.parquet").as_posix()


def feature_query(root: Path) -> str:
    glob = parquet_glob(root)
    return (
        """
        WITH base AS (
          SELECT
            datetime,
            CAST(date AS DATE) AS trade_date,
            expiry_type,
            option_type,
            strike_type,
            CAST(spot AS DOUBLE) AS spot,
            CAST(close AS DOUBLE) AS close
          FROM read_parquet('ROOT', union_by_name=true)
          WHERE close > 0
        ),
        minute AS (
          SELECT
            datetime,
            trade_date,
            expiry_type,
            MAX(spot) AS spot,
            MAX(CASE WHEN strike_type='ATM' AND option_type='CALL' THEN close END) AS atm_call,
            MAX(CASE WHEN strike_type='ATM' AND option_type='PUT' THEN close END) AS atm_put
          FROM base
          WHERE STRFTIME(datetime + INTERVAL '5 hours 30 minutes','%H:%M:%S')
                BETWEEN '09:30:00' AND '12:30:00'
          GROUP BY ALL
        ),
        f AS (
          SELECT
            *,
            LN(atm_call / LAG(atm_call, 1) OVER (PARTITION BY trade_date, expiry_type ORDER BY datetime)) AS call_ret_1,
            LN(atm_put  / LAG(atm_put,  1) OVER (PARTITION BY trade_date, expiry_type ORDER BY datetime)) AS put_ret_1,
            LN(atm_call / LAG(atm_call, 3) OVER (PARTITION BY trade_date, expiry_type ORDER BY datetime)) AS call_ret_3,
            LN(atm_put  / LAG(atm_put,  3) OVER (PARTITION BY trade_date, expiry_type ORDER BY datetime)) AS put_ret_3,
            LN(atm_call / LAG(atm_call, 5) OVER (PARTITION BY trade_date, expiry_type ORDER BY datetime)) AS call_ret_5,
            LN(atm_put  / LAG(atm_put,  5) OVER (PARTITION BY trade_date, expiry_type ORDER BY datetime)) AS put_ret_5,
            LN(LEAD(spot, 1) OVER (PARTITION BY trade_date, expiry_type ORDER BY datetime) / spot) * 100.0 AS fwd_spot_1_pct,
            LN(LEAD(spot, 3) OVER (PARTITION BY trade_date, expiry_type ORDER BY datetime) / spot) * 100.0 AS fwd_spot_3_pct,
            LN(LEAD(spot, 5) OVER (PARTITION BY trade_date, expiry_type ORDER BY datetime) / spot) * 100.0 AS fwd_spot_5_pct
          FROM minute
        )
        SELECT
          *,
          call_ret_1 - put_ret_1 AS pressure_1,
          call_ret_3 - put_ret_3 AS pressure_3,
          call_ret_5 - put_ret_5 AS pressure_5
        FROM f
        WHERE atm_call IS NOT NULL AND atm_put IS NOT NULL
        ORDER BY trade_date, expiry_type, datetime
        """
        .replace("ROOT", glob)
    )


def raw_query(root: Path) -> str:
    glob = parquet_glob(root)
    return (
        """
        SELECT
          datetime,
          CAST(date AS DATE) AS trade_date,
          expiry_type,
          option_type,
          CAST(strike_price AS DOUBLE) AS strike_price,
          CAST(close AS DOUBLE) AS close
        FROM read_parquet('ROOT', union_by_name=true)
        WHERE close > 0
          AND STRFTIME(datetime + INTERVAL '5 hours 30 minutes','%H:%M:%S')
              BETWEEN '09:25:00' AND '13:15:00'
        """
        .replace("ROOT", glob)
    )


def build_signals(features: pd.DataFrame, params: list[Variant]) -> pd.DataFrame:
    rows: list[dict] = []
    for p in params:
        x = features.loc[features["expiry_type"].eq(p.expiry_type)].copy()
        pressure = x[f"pressure_{p.lookback}"]
        x = x.loc[pressure.notna() & np.isfinite(pressure)]
        bull = pressure >= p.pressure_threshold
        bear = pressure <= -p.pressure_threshold
        x = x.loc[bull | bear].copy()
        if x.empty:
            continue
        x["direction"] = np.where(bull.loc[x.index], "CALL", "PUT")
        x = x.sort_values(["trade_date", "datetime"]).drop_duplicates(["trade_date"], keep="first")
        for row in x.itertuples(index=False):
            rows.append(
                {
                    "trade_date": row.trade_date,
                    "expiry_type": row.expiry_type,
                    "signal_time": row.datetime,
                    "entry_anchor": row.datetime + pd.Timedelta(minutes=1),
                    "trade_id": len(rows),
                    "spot": float(row.spot),
                    "direction": row.direction,
                    "variant": p.key(),
                    "lookback": p.lookback,
                    "pressure": float(getattr(row, f"pressure_{p.lookback}")),
                    "fwd_spot_1_pct": float(row.fwd_spot_1_pct) if pd.notna(row.fwd_spot_1_pct) else np.nan,
                    "fwd_spot_3_pct": float(row.fwd_spot_3_pct) if pd.notna(row.fwd_spot_3_pct) else np.nan,
                    "fwd_spot_5_pct": float(row.fwd_spot_5_pct) if pd.notna(row.fwd_spot_5_pct) else np.nan,
                }
            )
    return pd.DataFrame(rows)


def grouped_raw(raw: pd.DataFrame) -> dict:
    return {
        key: g.sort_values("datetime").copy()
        for key, g in raw.groupby(["trade_date", "expiry_type"], sort=False)
    }


def choose_entries(signals: pd.DataFrame, raw: pd.DataFrame) -> pd.DataFrame:
    if signals.empty:
        return signals
    groups = grouped_raw(raw)
    rows: list[dict] = []
    for row in signals.itertuples(index=False):
        g = groups.get((row.trade_date, row.expiry_type))
        if g is None:
            continue
        q = g[(g["datetime"] >= row.entry_anchor) & (g["option_type"] == row.direction)]
        if q.empty:
            continue
        entry_time = q["datetime"].min()
        q = q.loc[q["datetime"].eq(entry_time)]
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
        long_rows = q.loc[np.isclose(q["strike_price"], atm)]
        short_rows = q.loc[np.isclose(q["strike_price"], wing)]
        if long_rows.empty or short_rows.empty:
            continue
        rows.append(
            {
                **row._asdict(),
                "entry_time": entry_time,
                "atm_strike": float(atm),
                "wing_strike": wing,
                "long_entry": float(long_rows["close"].iloc[0]),
                "short_entry": float(short_rows["close"].iloc[0]),
                "hold_minutes": int(meta["hold_minutes"]),
            }
        )
    return pd.DataFrame(rows)


def simulate_paths(entries: pd.DataFrame, raw: pd.DataFrame) -> pd.DataFrame:
    if entries.empty:
        return entries
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
        sub = g[
            (g["datetime"] >= row.entry_time)
            & (g["datetime"] <= end_time)
            & (g["option_type"] == row.direction)
            & g["strike_price"].isin([row.atm_strike, row.wing_strike])
        ]
        if sub.empty:
            continue
        pivot = sub.pivot_table(
            index="datetime", columns="strike_price", values="close", aggfunc="last"
        ).dropna(subset=[row.atm_strike, row.wing_strike])
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
        reason = "time"
        for dt, value in path.iloc[1:].items():
            value = float(value)
            if value <= stop:
                exit_time, reason = dt, "stop"
                break
            if value >= target:
                exit_time, reason = dt, "target"
                break
        exit_row = pivot.loc[exit_time]
        out.append(
            {
                **row._asdict(),
                "exit_time": exit_time,
                "exit_reason": reason,
                "long_exit": float(exit_row[row.atm_strike]),
                "short_exit": float(exit_row[row.wing_strike]),
                "debit": debit,
            }
        )
    return pd.DataFrame(out)


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


def diagnostic_summary(signals: pd.DataFrame) -> pd.DataFrame:
    if signals.empty:
        return pd.DataFrame()
    x = signals.copy()
    def bucket(threshold):
        return abs(float(threshold))
    rows = []
    x["pressure_threshold"] = x["variant"].map(lambda s: json.loads(s)["pressure_threshold"])
    x["lookback"] = x["variant"].map(lambda s: json.loads(s)["lookback"])
    # Collapse duplicate expiry-specific events before measuring spot response.
    x = x.drop_duplicates(["trade_date", "lookback", "pressure_threshold", "direction"])
    for (lb, th, direction), g in x.groupby(["lookback", "pressure_threshold", "direction"], sort=True):
        rows.append(
            {
                "lookback": int(lb),
                "pressure_threshold": float(th),
                "direction": direction,
                "events": int(len(g)),
                "mean_fwd_spot_1_pct": float(g["fwd_spot_1_pct"].mean()),
                "mean_fwd_spot_3_pct": float(g["fwd_spot_3_pct"].mean()),
                "mean_fwd_spot_5_pct": float(g["fwd_spot_5_pct"].mean()),
                "hit_rate_fwd_1": float((g["fwd_spot_1_pct"] > 0).mean()) if direction == "CALL" else float((g["fwd_spot_1_pct"] < 0).mean()),
                "hit_rate_fwd_3": float((g["fwd_spot_3_pct"] > 0).mean()) if direction == "CALL" else float((g["fwd_spot_3_pct"] < 0).mean()),
                "hit_rate_fwd_5": float((g["fwd_spot_5_pct"] > 0).mean()) if direction == "CALL" else float((g["fwd_spot_5_pct"] < 0).mean()),
            }
        )
    return pd.DataFrame(rows)


def run(data_root: Path, out_dir: Path, slippage_points: float) -> dict:
    con = duckdb.connect()
    features = con.execute(feature_query(data_root)).df()
    raw = con.execute(raw_query(data_root)).df()
    con.close()

    features["datetime"] = pd.to_datetime(features["datetime"])
    raw["datetime"] = pd.to_datetime(raw["datetime"])

    params = parameter_grid()
    signals = build_signals(features, params)
    entries = choose_entries(signals, raw)
    trades = attach_pnl(simulate_paths(entries, raw), slippage_points)

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
        "slippage_points": slippage_points,
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
    ap.add_argument("--out", type=Path, default=Path("reports/phase3h"))
    ap.add_argument("--slippage", type=float, default=0.20)
    args = ap.parse_args()
    run(args.data, args.out, args.slippage)


if __name__ == "__main__":
    main()
