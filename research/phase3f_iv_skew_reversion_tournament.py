from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from research.contracts import nifty_lot_size
from research.cost_model import OptionCostModel


ENTRY_IST = ("09:45:00", "10:00:00", "10:15:00")
SKEW_SHOCK_POINTS = (2.0, 4.0, 6.0)
ABS_SKEW_MIN = (0.0, 2.0, 4.0)
HOLDS = (30, 60, 90)


def parquet_glob(root: Path) -> str:
    return (root / "**" / "*.parquet").as_posix()


def load_data(root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    source = parquet_glob(root)
    times = ",".join(repr(x) for x in ENTRY_IST)

    feature_sql = f"""
    WITH base AS (
      SELECT
        datetime,
        CAST(date AS DATE) AS trade_date,
        expiry_type,
        option_type,
        strike_type,
        CAST(iv AS DOUBLE) AS iv
      FROM read_parquet('{source}', union_by_name=true)
      WHERE close > 0
    ),
    minute AS (
      SELECT
        datetime,
        trade_date,
        expiry_type,
        AVG(CASE WHEN option_type='CALL' AND strike_type='ATM+1' AND iv BETWEEN 0 AND 300 THEN iv END) AS call_iv_1,
        AVG(CASE WHEN option_type='PUT' AND strike_type='ATM-1' AND iv BETWEEN 0 AND 300 THEN iv END) AS put_iv_1
      FROM base
      GROUP BY ALL
    ),
    lagged AS (
      SELECT
        *,
        put_iv_1 - call_iv_1 AS skew,
        (put_iv_1 - call_iv_1)
          - LAG(put_iv_1 - call_iv_1, 15) OVER (
              PARTITION BY trade_date, expiry_type ORDER BY datetime
            ) AS skew_chg15
      FROM minute
    )
    SELECT
      datetime,
      trade_date,
      expiry_type,
      skew,
      skew_chg15,
      ABS(skew) AS abs_skew
    FROM lagged
    WHERE STRFTIME(datetime + INTERVAL '5 hours 30 minutes','%H:%M:%S') IN ({times})
      AND skew IS NOT NULL
      AND skew_chg15 IS NOT NULL
    ORDER BY trade_date, expiry_type, datetime
    """

    raw_sql = f"""
    SELECT
      datetime,
      CAST(date AS DATE) AS trade_date,
      expiry_type,
      option_type,
      strike_type,
      CAST(strike_price AS DOUBLE) AS strike_price,
      CAST(close AS DOUBLE) AS close
    FROM read_parquet('{source}', union_by_name=true)
    WHERE close > 0
      AND strike_type IN ('ATM-2','ATM-1','ATM+1','ATM+2')
      AND STRFTIME(datetime + INTERVAL '5 hours 30 minutes','%H:%M:%S')
          BETWEEN '09:40:00' AND '13:45:00'
    """

    con = duckdb.connect()
    features = con.execute(feature_sql).df()
    raw = con.execute(raw_sql).df()
    con.close()

    features["datetime"] = pd.to_datetime(features["datetime"])
    raw["datetime"] = pd.to_datetime(raw["datetime"])
    return features, raw


def build_signals(features: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for entry_time, shock, skew_min, hold in itertools.product(
        ENTRY_IST, SKEW_SHOCK_POINTS, ABS_SKEW_MIN, HOLDS
    ):
        t = pd.to_datetime(features.datetime).dt.strftime("%H:%M:%S") == entry_time
        x = features.loc[
            t
            & (features.skew_chg15.abs() >= shock)
            & (features.abs_skew >= skew_min)
        ].copy()
        if x.empty:
            continue

        x["signal_time"] = x["datetime"]
        x["entry_time"] = x["datetime"] + pd.Timedelta(minutes=1)
        x["exit_time"] = x["entry_time"] + pd.Timedelta(minutes=hold)
        x["direction"] = np.where(x["skew_chg15"] > 0, "BULL", "BEAR")
        x["entry_clock"] = entry_time
        x["skew_shock"] = shock
        x["abs_skew_min"] = skew_min
        x["hold_minutes"] = hold

        x = x.sort_values(["trade_date", "expiry_type", "signal_time"]).drop_duplicates(
            ["trade_date", "expiry_type"], keep="first"
        )
        rows.append(x)

    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def quote_table(raw: pd.DataFrame) -> pd.DataFrame:
    return raw.drop_duplicates(
        ["trade_date", "expiry_type", "datetime", "option_type", "strike_type"], keep="last"
    )


def attach_four_legs(signals: pd.DataFrame, quotes: pd.DataFrame) -> pd.DataFrame:
    x = signals.copy()
    x["entry_time"] = pd.to_datetime(x["entry_time"])
    x["exit_time"] = pd.to_datetime(x["exit_time"])

    legs = [
        ("CALL", "ATM+1", "ce1"),
        ("CALL", "ATM+2", "ce2"),
        ("PUT", "ATM-1", "pe1"),
        ("PUT", "ATM-2", "pe2"),
    ]

    for opt_type, strike_type, name in legs:
        q = quotes[
            (quotes.option_type == opt_type)
            & (quotes.strike_type == strike_type)
        ][
            ["trade_date", "expiry_type", "datetime", "strike_price", "close"]
        ].rename(columns={
            "datetime": f"{name}_time",
            "strike_price": f"{name}_strike",
            "close": f"{name}_price",
        })

        x = x.merge(
            q,
            left_on=["trade_date", "expiry_type", "entry_time"],
            right_on=["trade_date", "expiry_type", f"{name}_time"],
            how="left",
        ).drop(columns=[f"{name}_time"])

        qx = quotes[
            (quotes.option_type == opt_type)
            & (quotes.strike_type == strike_type)
        ][
            ["trade_date", "expiry_type", "datetime", "strike_price", "close"]
        ].rename(columns={
            "datetime": f"{name}_exit_time",
            "strike_price": f"{name}_exit_strike",
            "close": f"{name}_exit_price",
        })

        x = x.merge(
            qx,
            left_on=["trade_date", "expiry_type", "exit_time", f"{name}_strike"],
            right_on=["trade_date", "expiry_type", f"{name}_exit_time", f"{name}_exit_strike"],
            how="left",
        ).drop(columns=[f"{name}_exit_time", f"{name}_exit_strike"])

    return x


def compute_net(df: pd.DataFrame) -> pd.Series:
    cm = OptionCostModel()
    lot = df.trade_date.map(nifty_lot_size).to_numpy(dtype=float)

    # BULL: +CE1 -CE2 -PE1 +PE2
    # BEAR: -CE1 +CE2 +PE1 -PE2
    s = np.where(df.direction.eq("BULL").to_numpy(), 1.0, -1.0)
    signs = np.column_stack([s, -s, -s, s])

    entry = np.column_stack([
        df.ce1_price.to_numpy(float),
        df.ce2_price.to_numpy(float),
        df.pe1_price.to_numpy(float),
        df.pe2_price.to_numpy(float),
    ])
    exit_ = np.column_stack([
        df.ce1_exit_price.to_numpy(float),
        df.ce2_exit_price.to_numpy(float),
        df.pe1_exit_price.to_numpy(float),
        df.pe2_exit_price.to_numpy(float),
    ])

    gross = ((exit_ * signs).sum(axis=1) - (entry * signs).sum(axis=1)) * lot
    turnover = (entry.sum(axis=1) + exit_.sum(axis=1)) * lot

    brokerage = 8.0 * cm.brokerage_per_order
    exchange = turnover * cm.exchange_rate
    sebi = turnover * cm.sebi_rate

    sell_entry = (-entry * signs * (signs < 0)).sum(axis=1)
    sell_exit = (exit_ * signs * (signs > 0)).sum(axis=1)
    buy_entry = (entry * signs * (signs > 0)).sum(axis=1)
    buy_exit = (-exit_ * signs * (signs < 0)).sum(axis=1)

    stt = (sell_entry + sell_exit) * lot * cm.stt_sell_rate
    stamp = (buy_entry + buy_exit) * lot * cm.stamp_buy_rate
    gst = cm.gst_rate * (brokerage + exchange + sebi)
    slippage = 8.0 * 0.20 * lot

    return pd.Series(
        gross - (brokerage + exchange + sebi + stt + stamp + gst + slippage),
        index=df.index,
    )


def metrics(g: pd.DataFrame, calendar_days: int) -> dict:
    daily = g.groupby("trade_date").net_pnl.sum()
    wins = g.loc[g.net_pnl > 0, "net_pnl"].sum()
    losses = -g.loc[g.net_pnl < 0, "net_pnl"].sum()
    return {
        "trades": int(len(g)),
        "active_days": int(len(daily)),
        "calendar_days": int(calendar_days),
        "mean_active_day_net": float(daily.mean()),
        "mean_all_day_net": float(g.net_pnl.sum() / max(1, calendar_days)),
        "median_trade": float(g.net_pnl.median()),
        "win_rate": float((g.net_pnl > 0).mean()),
        "positive_day_rate": float((daily > 0).sum() / max(1, calendar_days)),
        "profit_factor": float(wins / losses) if losses > 0 else 999.0,
        "total_net": float(g.net_pnl.sum()),
        "max_drawdown": float((daily.cumsum() - daily.cumsum().cummax()).min()),
        "mean_abs_skew": float(g.abs_skew.mean()),
        "mean_skew_shock": float(g.skew_chg15.abs().mean()),
    }


def run(root: Path, out: Path) -> dict:
    features, raw = load_data(root)
    signals = build_signals(features)

    if signals.empty:
        summary = {
            "features": int(len(features)),
            "signals": 0,
            "variants": 0,
            "target_daily_net": 1000.0,
            "gate": "NO_SIGNALS",
        }
        out.mkdir(parents=True, exist_ok=True)
        (out / "phase3f_skew_summary.json").write_text(json.dumps(summary, indent=2))
        return summary

    quotes = quote_table(raw)
    trades = attach_four_legs(signals, quotes)
    price_cols = [
        "ce1_price", "ce2_price", "pe1_price", "pe2_price",
        "ce1_exit_price", "ce2_exit_price", "pe1_exit_price", "pe2_exit_price",
    ]
    trades = trades.dropna(subset=price_cols).copy()
    if trades.empty:
        summary = {
            "features": int(len(features)),
            "signals": int(len(signals)),
            "trades": 0,
            "variants": 0,
            "target_daily_net": 1000.0,
            "gate": "NO_COMPLETE_QUOTES",
        }
        out.mkdir(parents=True, exist_ok=True)
        (out / "phase3f_skew_summary.json").write_text(json.dumps(summary, indent=2))
        return summary

    trades["net_pnl"] = compute_net(trades)

    group_cols = ["expiry_type", "entry_clock", "skew_shock", "abs_skew_min", "hold_minutes"]
    boards = []
    calendar = features.groupby("expiry_type").trade_date.nunique().to_dict()
    for keys, g in trades.groupby(group_cols):
        m = metrics(g, int(calendar.get(keys[0], g.trade_date.nunique())))
        boards.append({**dict(zip(group_cols, keys)), **m})

    board = pd.DataFrame(boards).sort_values(
        ["mean_all_day_net", "profit_factor", "win_rate"],
        ascending=[False, False, False],
    ).reset_index(drop=True)

    out.mkdir(parents=True, exist_ok=True)
    trades.to_csv(out / "phase3f_skew_trades.csv", index=False)
    board.to_csv(out / "phase3f_skew_leaderboard.csv", index=False)

    best = board.iloc[0].to_dict() if not board.empty else None
    summary = {
        "features": int(len(features)),
        "signals": int(len(signals)),
        "trades": int(len(trades)),
        "variants": int(len(board)),
        "calendar_days": {str(k): int(v) for k, v in calendar.items()},
        "target_daily_net": 1000.0,
        "target_qualified": int((board.mean_all_day_net >= 1000).sum()),
        "positive_variants": int((board.mean_all_day_net > 0).sum()),
        "best": best,
        "gate": "PASS_PRELIMINARY" if best and best["mean_all_day_net"] >= 1000 else "FAIL_PRELIMINARY",
    }
    (out / "phase3f_skew_summary.json").write_text(
        json.dumps(summary, indent=2, default=str),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, default=str))
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=Path("reports"))
    args = ap.parse_args()
    run(args.data, args.out)


if __name__ == "__main__":
    main()
