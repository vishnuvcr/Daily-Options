from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb
import pandas as pd

from research.contracts import nifty_lot_size
from research.cost_model import OptionCostModel


ENTRY_TIMES = ["09:45:00", "10:00:00", "10:15:00"]
WIDTHS = [1, 2]
HOLDS = [30, 60, 90]
OI_THRESHOLDS = [0.05, 0.10, 0.20]
VOL_THRESHOLDS = [0.05, 0.10, 0.20]
RET_THRESHOLDS = [0.0, 0.0005, 0.0010]
IVRV_MIN = [0.0, 1.0, 1.25]


def parquet_glob(root: Path) -> str:
    return (root / "**" / "*.parquet").as_posix()


def feature_query(root: Path) -> str:
    glob = parquet_glob(root)
    return f"""
    WITH base AS (
      SELECT
        datetime,
        CAST(date AS DATE) AS trade_date,
        expiry_type,
        option_type,
        strike_type,
        CAST(strike_price AS DOUBLE) AS strike_price,
        CAST(spot AS DOUBLE) AS spot,
        CAST(iv AS DOUBLE) AS iv,
        CASE WHEN volume >= 0 THEN CAST(volume AS DOUBLE) ELSE NULL END AS volume,
        CAST(oi AS DOUBLE) AS oi
      FROM read_parquet('{glob}', union_by_name=true)
      WHERE close > 0
    ),
    minute AS (
      SELECT
        datetime,
        trade_date,
        expiry_type,
        MAX(spot) AS spot,
        AVG(CASE WHEN strike_type='ATM' AND option_type='CALL' AND iv BETWEEN 0 AND 300 THEN iv END) AS atm_call_iv,
        AVG(CASE WHEN strike_type='ATM' AND option_type='PUT'  AND iv BETWEEN 0 AND 300 THEN iv END) AS atm_put_iv,
        SUM(CASE WHEN strike_type IN ('ATM-2','ATM-1','ATM','ATM+1','ATM+2') AND option_type='CALL' THEN oi ELSE 0 END) AS call_oi,
        SUM(CASE WHEN strike_type IN ('ATM-2','ATM-1','ATM','ATM+1','ATM+2') AND option_type='PUT'  THEN oi ELSE 0 END) AS put_oi,
        SUM(CASE WHEN strike_type IN ('ATM-2','ATM-1','ATM','ATM+1','ATM+2') AND option_type='CALL' THEN volume ELSE 0 END) AS call_vol,
        SUM(CASE WHEN strike_type IN ('ATM-2','ATM-1','ATM','ATM+1','ATM+2') AND option_type='PUT'  THEN volume ELSE 0 END) AS put_vol
      FROM base
      GROUP BY ALL
    ),
    lagged AS (
      SELECT *,
        (call_oi-put_oi)/NULLIF(call_oi+put_oi,0) AS oi_imb,
        (call_vol-put_vol)/NULLIF(call_vol+put_vol,0) AS vol_imb,
        (atm_call_iv+atm_put_iv)/2.0 AS atm_iv,
        atm_put_iv-atm_call_iv AS iv_skew,
        spot/LAG(spot,15) OVER (PARTITION BY trade_date,expiry_type ORDER BY datetime)-1 AS spot_ret15,
        atm_iv-LAG(atm_iv,15) OVER (PARTITION BY trade_date,expiry_type ORDER BY datetime) AS iv_chg15,
        LN(spot/LAG(spot) OVER (PARTITION BY trade_date,expiry_type ORDER BY datetime)) AS log_ret
      FROM minute
    ),
    with_rv AS (
      SELECT *,
        STDDEV_SAMP(log_ret) OVER (
          PARTITION BY trade_date,expiry_type ORDER BY datetime
          ROWS BETWEEN 14 PRECEDING AND CURRENT ROW
        ) * SQRT(252.0*375.0) * 100.0 AS rv15_pct
      FROM lagged
    )
    SELECT *,
      atm_iv / NULLIF(rv15_pct,0) AS iv_rv_ratio,
      STRFTIME(datetime + INTERVAL '5 hours 30 minutes','%H:%M:%S') AS ist_time
    FROM with_rv
    WHERE STRFTIME(datetime + INTERVAL '5 hours 30 minutes','%H:%M:%S') IN ({",".join(repr(x) for x in ENTRY_TIMES)})
      AND spot_ret15 IS NOT NULL
      AND oi_imb IS NOT NULL
      AND vol_imb IS NOT NULL
      AND atm_iv IS NOT NULL
    ORDER BY trade_date, expiry_type, datetime
    """


def raw_query(root: Path) -> str:
    glob = parquet_glob(root)
    return f"""
    SELECT
      datetime,
      CAST(date AS DATE) AS trade_date,
      expiry_type,
      option_type,
      strike_type,
      CAST(strike_price AS DOUBLE) AS strike_price,
      CAST(close AS DOUBLE) AS close
    FROM read_parquet('{glob}', union_by_name=true)
    WHERE close > 0
      AND STRFTIME(datetime + INTERVAL '5 hours 30 minutes','%H:%M:%S') >= '09:45:00'
      AND STRFTIME(datetime + INTERVAL '5 hours 30 minutes','%H:%M:%S') <= '12:15:00'
    """


def build_price_map(raw: pd.DataFrame) -> dict:
    raw = raw.copy()
    raw["datetime"] = pd.to_datetime(raw["datetime"])
    return {
        (r.trade_date, r.expiry_type, r.datetime, r.option_type, float(r.strike_price)): float(r.close)
        for r in raw.itertuples(index=False)
    }


def find_price(price_map: dict, d, expiry, ts, option_type, strike, max_lag=1):
    for k in range(max_lag + 1):
        key = (d, expiry, ts + pd.Timedelta(minutes=k), option_type, float(strike))
        if key in price_map:
            return price_map[key], key[2]
    return None, None


def trade_net_debit(cm: OptionCostModel, long_entry, short_entry, long_exit, short_exit, lot):
    return cm.vertical_debit_spread_net_pnl(
        long_entry, short_entry, long_exit, short_exit, lot_size=lot, qty=1, slippage_points=0.20
    )


def run_tournament(root: Path, out: Path) -> dict:
    con = duckdb.connect()
    features = con.execute(feature_query(root)).df()
    raw = con.execute(raw_query(root)).df()
    con.close()

    raw["datetime"] = pd.to_datetime(raw["datetime"])
    features["datetime"] = pd.to_datetime(features["datetime"])
    price_map = build_price_map(raw)

    trades = []
    for r in features.itertuples(index=False):
        # Signal uses information at t; entry begins at t+1 minute.
        entry_ts = r.datetime + pd.Timedelta(minutes=1)
        for oi_thr in OI_THRESHOLDS:
            for vol_thr in VOL_THRESHOLDS:
                for ret_thr in RET_THRESHOLDS:
                    direction = None
                    if r.oi_imb >= oi_thr and r.vol_imb >= vol_thr and r.spot_ret15 >= ret_thr:
                        direction = "CALL"
                    elif r.oi_imb <= -oi_thr and r.vol_imb <= -vol_thr and r.spot_ret15 <= -ret_thr:
                        direction = "PUT"
                    if direction is None:
                        continue
                    if not pd.notna(r.iv_rv_ratio):
                        continue
                    for iv_min in IVRV_MIN:
                        if r.iv_rv_ratio < iv_min:
                            continue
                        atm_row = raw[
                            (raw.trade_date == r.trade_date)
                            & (raw.expiry_type == r.expiry_type)
                            & (raw.datetime == entry_ts)
                            & (raw.strike_type == "ATM")
                            & (raw.option_type == direction)
                        ]
                        if atm_row.empty:
                            continue
                        atm = float(atm_row.iloc[0].strike_price)
                        if direction == "CALL":
                            wing_row = raw[
                                (raw.trade_date == r.trade_date)
                                & (raw.expiry_type == r.expiry_type)
                                & (raw.datetime == entry_ts)
                                & (raw.strike_type == f"ATM+{1}")
                                & (raw.option_type == direction)
                            ]
                            wing_sign = "CALL"
                        else:
                            wing_row = raw[
                                (raw.trade_date == r.trade_date)
                                & (raw.expiry_type == r.expiry_type)
                                & (raw.datetime == entry_ts)
                                & (raw.strike_type == "ATM-1")
                                & (raw.option_type == direction)
                            ]
                            wing_sign = "PUT"
                        if wing_row.empty:
                            continue
                        wing1 = float(wing_row.iloc[0].strike_price)

                        for width in WIDTHS:
                            if width == 2:
                                wing_type = f"ATM+2" if direction == "CALL" else "ATM-2"
                                wr = raw[
                                    (raw.trade_date == r.trade_date)
                                    & (raw.expiry_type == r.expiry_type)
                                    & (raw.datetime == entry_ts)
                                    & (raw.strike_type == wing_type)
                                    & (raw.option_type == direction)
                                ]
                                if wr.empty:
                                    continue
                                wing = float(wr.iloc[0].strike_price)
                            else:
                                wing = wing1

                            le, ets = find_price(price_map, r.trade_date, r.expiry_type, entry_ts, direction, atm)
                            se, _ = find_price(price_map, r.trade_date, r.expiry_type, entry_ts, direction, wing)
                            if le is None or se is None:
                                continue
                            entry_spread = le - se
                            if entry_spread <= 0:
                                continue

                            for hold in HOLDS:
                                requested_exit = entry_ts + pd.Timedelta(minutes=hold)
                                lx, xts = find_price(price_map, r.trade_date, r.expiry_type, requested_exit, direction, atm)
                                sx, _ = find_price(price_map, r.trade_date, r.expiry_type, requested_exit, direction, wing)
                                if lx is None or sx is None:
                                    continue
                                lot = nifty_lot_size(r.trade_date)
                                pnl = trade_net_debit(cm, le, se, lx, sx, lot)
                                trades.append({
                                    "trade_date": str(r.trade_date),
                                    "expiry_type": r.expiry_type,
                                    "signal_time_utc": r.datetime.isoformat(),
                                    "entry_time_utc": ets.isoformat() if ets is not None else entry_ts.isoformat(),
                                    "exit_time_utc": xts.isoformat() if xts is not None else requested_exit.isoformat(),
                                    "entry_time_ist": str((ets or entry_ts) + pd.Timedelta(hours=5, minutes=30)),
                                    "direction": direction,
                                    "width_steps": width,
                                    "hold_minutes": hold,
                                    "oi_thr": oi_thr,
                                    "vol_thr": vol_thr,
                                    "ret_thr": ret_thr,
                                    "iv_rv_min": iv_min,
                                    "oi_imb": float(r.oi_imb),
                                    "vol_imb": float(r.vol_imb),
                                    "spot_ret15": float(r.spot_ret15),
                                    "atm_iv": float(r.atm_iv),
                                    "iv_rv_ratio": float(r.iv_rv_ratio),
                                    "entry_spread": float(entry_spread),
                                    "net_pnl": float(pnl),
                                })

    trades_df = pd.DataFrame(trades)
    out.mkdir(parents=True, exist_ok=True)
    if trades_df.empty:
        summary = {"features": len(features), "trades": 0, "variants": 0, "target_daily_net": 1000.0}
        (out / "phase3f_directional_summary.json").write_text(json.dumps(summary, indent=2))
        return summary

    group_cols = ["expiry_type","width_steps","hold_minutes","oi_thr","vol_thr","ret_thr","iv_rv_min"]
    boards = []
    calendar_days = int(features["trade_date"].nunique())
    # Target-day metrics use all dates represented by valid feature rows, not only active trade days.
    for _, g in trades_df.groupby(group_cols, dropna=False):
        daily = g.groupby("trade_date")["net_pnl"].sum()
        wins = g.loc[g.net_pnl > 0, "net_pnl"].sum()
        losses = -g.loc[g.net_pnl < 0, "net_pnl"].sum()
        boards.append({
            **{k: row for k, row in zip(group_cols, g.iloc[0][group_cols])},
            "trades": len(g),
            "mean_active_day": float(daily.mean()),
            "mean_all_calendar_day": float(daily.sum()/max(1,calendar_days)),
            "median_trade": float(g.net_pnl.median()),
            "win_rate": float((g.net_pnl > 0).mean()),
            "profit_factor": float(wins/losses) if losses else 999.0,
            "total_net": float(g.net_pnl.sum()),
            "max_drawdown": float((daily.cumsum()-daily.cumsum().cummax()).min()),
        })

    board = pd.DataFrame(boards)
    board = board.sort_values(["mean_active_day","win_rate","profit_factor"], ascending=[False,False,False])
    trades_df.to_csv(out / "phase3f_directional_trades.csv", index=False)
    board.to_csv(out / "phase3f_directional_leaderboard.csv", index=False)
    best = board.iloc[0].to_dict()
    summary = {
        "features": int(len(features)),
        "raw_rows_used": int(len(raw)),
        "trades": int(len(trades_df)),
        "variants": int(len(board)),
        "calendar_days_with_trades": int(trades_df.trade_date.nunique()),
        "target_daily_net": 1000.0,
        "target_qualified_variants": int((board.mean_all_calendar_day >= 1000).sum()),
        "best": best,
        "data_quality_note": "Rows with negative volume are ignored in volume sums; the full source audit recorded 16 such rows.",
    }
    (out / "phase3f_directional_summary.json").write_text(json.dumps(summary, indent=2, default=str))
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=Path("reports"))
    args = ap.parse_args()
    summary = run_tournament(args.data, args.out)
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
