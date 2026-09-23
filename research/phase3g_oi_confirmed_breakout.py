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


BREAK_LOOKBACKS = (15, 30)
OI_WINDOWS = (3, 5)
OI_THRESHOLDS = (0.01, 0.02)
EXPIRIES = ("WEEK", "MONTH")
WIDTHS = (1, 2)
HOLDS = (60, 90)
IV_RV_MAX = (None, 1.25)
BREAK_PCT = 0.0005


@dataclass(frozen=True)
class Variant:
    lookback: int
    oi_window: int
    oi_threshold: float
    expiry_type: str
    width_steps: int
    hold_minutes: int
    iv_rv_max: float | None

    def key(self) -> str:
        return json.dumps({
            "lookback": self.lookback,
            "oi_window": self.oi_window,
            "oi_threshold": self.oi_threshold,
            "expiry_type": self.expiry_type,
            "width_steps": self.width_steps,
            "hold_minutes": self.hold_minutes,
            "iv_rv_max": self.iv_rv_max,
        }, sort_keys=True)


def parameter_grid() -> list[Variant]:
    return [
        Variant(lb, ow, ot, ex, w, h, iv)
        for lb in BREAK_LOOKBACKS
        for ow in OI_WINDOWS
        for ot in OI_THRESHOLDS
        for ex in EXPIRIES
        for w in WIDTHS
        for h in HOLDS
        for iv in IV_RV_MAX
    ]


def parquet_glob(root: Path) -> str:
    return (root / "**" / "*.parquet").as_posix()


def feature_query(root: Path) -> str:
    glob = parquet_glob(root)
    return """
    WITH base AS (
      SELECT
        datetime,
        CAST(date AS DATE) AS trade_date,
        expiry_type,
        option_type,
        strike_type,
        CAST(spot AS DOUBLE) AS spot,
        CAST(iv AS DOUBLE) AS iv,
        CAST(oi AS DOUBLE) AS oi,
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
        AVG(CASE WHEN strike_type='ATM' AND iv BETWEEN 0 AND 300 THEN iv END) AS atm_iv,
        SUM(CASE WHEN strike_type IN ('ATM-2','ATM-1','ATM','ATM+1','ATM+2')
                      AND option_type='CALL' THEN oi ELSE 0 END) AS call_oi,
        SUM(CASE WHEN strike_type IN ('ATM-2','ATM-1','ATM','ATM+1','ATM+2')
                      AND option_type='PUT' THEN oi ELSE 0 END) AS put_oi
      FROM base
      GROUP BY ALL
    ),
    d AS (
      SELECT *,
        (put_oi-call_oi)/NULLIF(put_oi+call_oi,0) AS pc_oi,
        LN(spot/LAG(spot) OVER (PARTITION BY trade_date, expiry_type ORDER BY datetime)) AS log_ret
      FROM minute
    )
    SELECT *,
      MAX(spot) OVER (
        PARTITION BY trade_date, expiry_type ORDER BY datetime
        ROWS BETWEEN 15 PRECEDING AND 1 PRECEDING
      ) AS high15,
      MIN(spot) OVER (
        PARTITION BY trade_date, expiry_type ORDER BY datetime
        ROWS BETWEEN 15 PRECEDING AND 1 PRECEDING
      ) AS low15,
      MAX(spot) OVER (
        PARTITION BY trade_date, expiry_type ORDER BY datetime
        ROWS BETWEEN 30 PRECEDING AND 1 PRECEDING
      ) AS high30,
      MIN(spot) OVER (
        PARTITION BY trade_date, expiry_type ORDER BY datetime
        ROWS BETWEEN 30 PRECEDING AND 1 PRECEDING
      ) AS low30,
      STDDEV_SAMP(log_ret) OVER (
        PARTITION BY trade_date, expiry_type ORDER BY datetime
        ROWS BETWEEN 14 PRECEDING AND CURRENT ROW
      ) * SQRT(252.0*375.0) * 100.0 AS rv15_pct,
      LEAD(pc_oi,3) OVER (
        PARTITION BY trade_date, expiry_type ORDER BY datetime
      ) - pc_oi AS doi3,
      LEAD(pc_oi,5) OVER (
        PARTITION BY trade_date, expiry_type ORDER BY datetime
      ) - pc_oi AS doi5
    FROM d
    WHERE STRFTIME(datetime + INTERVAL '5 hours 30 minutes','%H:%M:%S')
          BETWEEN '09:30:00' AND '12:30:00'
    ORDER BY trade_date, expiry_type, datetime
    """.replace("ROOT", glob)


def raw_query(root: Path) -> str:
    glob = parquet_glob(root)
    return """
    SELECT
      datetime,
      CAST(date AS DATE) AS trade_date,
      expiry_type,
      option_type,
      strike_type,
      CAST(strike_price AS DOUBLE) AS strike_price,
      CAST(close AS DOUBLE) AS close
    FROM read_parquet('ROOT', union_by_name=true)
    WHERE close > 0
      AND STRFTIME(datetime + INTERVAL '5 hours 30 minutes','%H:%M:%S')
          BETWEEN '09:20:00' AND '14:45:00'
    """.replace("ROOT", glob)


def build_signals(features: pd.DataFrame, params: list[Variant]) -> pd.DataFrame:
    rows: list[dict] = []
    for p in params:
        x = features.loc[features["expiry_type"].eq(p.expiry_type)].copy()
        high = x[f"high{p.lookback}"]
        low = x[f"low{p.lookback}"]
        doi = x[f"doi{p.oi_window}"]
        x["iv_rv_ratio"] = x["atm_iv"] / x["rv15_pct"].replace(0, np.nan)
        x = x.dropna(subset=[f"high{p.lookback}", f"low{p.lookback}", f"doi{p.oi_window}", "iv_rv_ratio"])
        bull = (x["spot"] >= high.loc[x.index] * (1.0 + BREAK_PCT)) & (doi.loc[x.index] >= p.oi_threshold)
        bear = (x["spot"] <= low.loc[x.index] * (1.0 - BREAK_PCT)) & (doi.loc[x.index] <= -p.oi_threshold)
        if p.iv_rv_max is not None:
            bull &= x["iv_rv_ratio"] <= p.iv_rv_max
            bear &= x["iv_rv_ratio"] <= p.iv_rv_max
        x["direction"] = np.where(bull, "CALL", np.where(bear, "PUT", ""))
        x = x.loc[x["direction"].ne("")].sort_values(["trade_date", "datetime"])
        if x.empty:
            continue
        x = x.drop_duplicates(["trade_date"], keep="first")
        rows.extend(
            {
                "trade_date": row.trade_date,
                "expiry_type": row.expiry_type,
                "signal_time": row.datetime,
                "entry_time": row.datetime + pd.Timedelta(minutes=p.oi_window + 1),
                "trade_id": int(len(rows)),
                "spot": float(row.spot),
                "direction": row.direction,
                "variant": p.key(),
            }
            for row in x.itertuples()
        )
    return pd.DataFrame(rows)


def choose_entry_legs(signals: pd.DataFrame, raw: pd.DataFrame) -> pd.DataFrame:
    if signals.empty:
        return signals
    s = signals.reset_index(drop=True).copy()
    s["trade_id"] = np.arange(len(s), dtype=int)
    q = raw.merge(
        s[["trade_id", "trade_date", "expiry_type", "entry_time", "direction", "spot"]],
        left_on=["trade_date", "expiry_type", "datetime", "option_type"],
        right_on=["trade_date", "expiry_type", "entry_time", "direction"],
        how="inner",
    )
    if q.empty:
        return pd.DataFrame()
    out = []
    meta = s.set_index("trade_id")
    for trade_id, g in q.groupby("trade_id", sort=False):
        row = meta.loc[trade_id].to_dict()
        row["trade_id"] = int(trade_id)
        strikes = sorted(g["strike_price"].dropna().unique())
        if not strikes:
            continue
        atm = min(strikes, key=lambda k: abs(float(k) - float(row["spot"])))
        width = int(json.loads(row["variant"])["width_steps"])
        if row["direction"] == "CALL":
            wings = sorted(k for k in strikes if k > atm)
        else:
            wings = sorted((k for k in strikes if k < atm), reverse=True)
        if len(wings) < width:
            continue
        wing = float(wings[width - 1])
        long_rows = g.loc[np.isclose(g["strike_price"], atm)]
        short_rows = g.loc[np.isclose(g["strike_price"], wing)]
        if long_rows.empty or short_rows.empty:
            continue
        row["atm_strike"] = float(atm)
        row["wing_strike"] = wing
        row["long_entry"] = float(long_rows["close"].iloc[0])
        row["short_entry"] = float(short_rows["close"].iloc[0])
        out.append(row)
    return pd.DataFrame(out)


def simulate_paths(trades: pd.DataFrame, raw: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return trades
    t = trades.copy()
    t["hold_minutes"] = t["variant"].map(lambda s: int(json.loads(s)["hold_minutes"]))
    t["max_exit_time"] = t["entry_time"] + pd.to_timedelta(t["hold_minutes"], unit="m")
    use = raw.merge(
        t[["trade_id", "trade_date", "expiry_type", "entry_time", "max_exit_time", "direction", "atm_strike", "wing_strike"]],
        on=["trade_date", "expiry_type"],
        how="inner",
    )
    use = use.loc[
        (use["datetime"] >= use["entry_time"]) &
        (use["datetime"] <= use["max_exit_time"]) &
        (use["option_type"] == use["direction"])
    ].copy()
    use = use.loc[
        np.isclose(use["strike_price"].to_numpy(), np.repeat(t[["atm_strike","wing_strike"]].to_numpy(), 1, axis=0).mean(axis=1)[0])
        if False else np.ones(len(use), dtype=bool)
    ]
    records = []
    for trade_id, g in use.groupby("trade_id", sort=False):
        tr = t.loc[t["trade_id"].eq(trade_id)].iloc[0]
        sub = g[g["strike_price"].isin([tr["atm_strike"], tr["wing_strike"]])].copy()
        if sub.empty:
            continue
        pivot = sub.pivot_table(index="datetime", columns="strike_price", values="close", aggfunc="last")
        if tr["atm_strike"] not in pivot.columns or tr["wing_strike"] not in pivot.columns:
            continue
        pivot = pivot.dropna(subset=[tr["atm_strike"], tr["wing_strike"]])
        if pivot.empty or tr["entry_time"] not in pivot.index:
            continue
        spread = pivot[tr["atm_strike"]] - pivot[tr["wing_strike"]]
        debit = float(spread.loc[tr["entry_time"]])
        if debit <= 0:
            continue
        stop = 0.50 * debit
        target = 1.75 * debit
        path = spread.loc[spread.index >= tr["entry_time"]]
        exit_time = path.index[-1]
        exit_value = float(path.iloc[-1])
        reason = "time"
        for dt, value in path.iloc[1:].items():
            v = float(value)
            if v <= stop:
                exit_time, exit_value, reason = dt, v, "stop"
                break
            if v >= target:
                exit_time, exit_value, reason = dt, v, "target"
                break
        exit_row = pivot.loc[exit_time]
        records.append({
            **tr.to_dict(),
            "exit_time": exit_time,
            "exit_reason": reason,
            "long_exit": float(exit_row[tr["atm_strike"]]),
            "short_exit": float(exit_row[tr["wing_strike"]]),
            "debit": debit,
        })
    return pd.DataFrame(records)


def attach_pnl(trades: pd.DataFrame, slippage_points: float = 0.20) -> pd.DataFrame:
    if trades.empty:
        return trades
    cm = OptionCostModel()
    out = trades.copy()
    out["lot_size"] = out["trade_date"].map(nifty_lot_size)
    out["net_pnl"] = [
        cm.vertical_debit_spread_net_pnl(le, se, lx, sx, int(lot), slippage_points=slippage_points)
        for le, se, lx, sx, lot in zip(
            out["long_entry"], out["short_entry"], out["long_exit"], out["short_exit"], out["lot_size"]
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
        rows.append({
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
        })
    board = pd.DataFrame(rows).sort_values(["mean_all_day_net","positive_day_rate"], ascending=False).reset_index(drop=True)
    return board, {"gate": "PASS_PRELIMINARY" if bool((board["mean_all_day_net"] >= 1000).any()) else "FAIL_PRELIMINARY"}


def walk_forward(trades: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    if trades.empty:
        return pd.DataFrame(), {"gate": "NO_TRADES"}
    dates = sorted(pd.to_datetime(trades["trade_date"]).dt.date.unique())
    train_len, val_len, embargo, test_len, step = 180, 60, 5, 60, 60
    results = []
    start = 0
    while start + train_len + val_len + embargo + test_len <= len(dates):
        train_dates = set(dates[start:start + train_len])
        val_dates = set(dates[start + train_len:start + train_len + val_len])
        test_start = start + train_len + val_len + embargo
        test_dates = set(dates[test_start:test_start + test_len])
        train = trades[trades["trade_date"].isin(train_dates)]
        val = trades[trades["trade_date"].isin(val_dates)]
        test = trades[trades["trade_date"].isin(test_dates)]
        scores = []
        for variant, vg in train.groupby("variant"):
            if len(vg) < 10:
                continue
            scores.append((variant, float(vg.groupby("trade_date")["net_pnl"].sum().mean())))
        if not scores:
            start += step
            continue
        scores.sort(key=lambda z: z[1], reverse=True)
        val_scores = []
        for variant, _ in scores[:12]:
            vg = val[val["variant"].eq(variant)]
            if len(vg) < 5:
                continue
            val_scores.append((variant, float(vg.groupby("trade_date")["net_pnl"].sum().mean())))
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
        results.append({
            "test_start": str(min(test_dates)),
            "test_end": str(max(test_dates)),
            "selected_variant": selected,
            "validation_mean": val_scores[0][1],
            "test_mean": float(daily.mean()),
            "test_median": float(daily.median()),
            "positive_day_rate": float((daily > 0).mean()),
            "trade_days": int(daily.size),
        })
        start += step
    out = pd.DataFrame(results)
    summary = {
        "walk_forward_windows": int(len(out)),
        "positive_test_windows": int((out["test_mean"] > 0).sum()) if not out.empty else 0,
        "target_qualified_windows": int((out["test_mean"] >= 1000).sum()) if not out.empty else 0,
        "mean_test_window_net": float(out["test_mean"].mean()) if not out.empty else None,
        "gate": "PASS_PRELIMINARY" if (not out.empty and out["test_mean"].mean() > 0 and (out["test_mean"] >= 1000).any()) else "FAIL_PRELIMINARY",
    }
    return out, summary


def run(data_root: Path, out_dir: Path, slippage_points: float = 0.20) -> dict:
    con = duckdb.connect()
    features = con.execute(feature_query(data_root)).df()
    raw = con.execute(raw_query(data_root)).df()
    con.close()
    features["datetime"] = pd.to_datetime(features["datetime"])
    raw["datetime"] = pd.to_datetime(raw["datetime"])
    params = parameter_grid()
    signals = build_signals(features, params)
    entries = choose_entry_legs(signals, raw)
    trades = attach_pnl(simulate_paths(entries, raw), slippage_points=slippage_points)
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
        "trades": int(len(trades)),
        "variants": len(params),
        "preliminary": preliminary,
        "walk_forward": wf_summary,
        "slippage_points": slippage_points,
        "volume_used": False,
        "gate": wf_summary["gate"],
    }
    (out_dir / "phase3g_summary.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(json.dumps(summary, indent=2, default=str))
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=Path("reports/phase3g"))
    ap.add_argument("--slippage", type=float, default=0.20)
    args = ap.parse_args()
    run(args.data, args.out, args.slippage)


if __name__ == "__main__":
    main()
