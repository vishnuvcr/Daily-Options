from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from research.contracts import nifty_lot_size
from research.cost_model import OptionCostModel


OI_THRESHOLDS = (0.05, 0.10, 0.20)
VOL_THRESHOLDS = (0.05, 0.10, 0.20)
RET_THRESHOLDS = (0.0, 0.0005, 0.0010)
IVRV_MIN = (0.0, 1.0, 1.25)
WIDTHS = (1, 2)
HOLDS = (30, 60, 90)
ENTRY_IST = ("09:45:00", "10:00:00", "10:15:00")


def parquet_glob(root: Path) -> str:
    return (root / "**" / "*.parquet").as_posix()


def feature_query(root: Path) -> str:
    glob = parquet_glob(root)
    times = ",".join(repr(x) for x in ENTRY_IST)
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
        SUM(CASE WHEN strike_type IN ('ATM-2','ATM-1','ATM','ATM+1','ATM+2') AND option_type='CALL' THEN volume ELSE 0 END) AS call_vol,
        SUM(CASE WHEN strike_type IN ('ATM-2','ATM-1','ATM','ATM+1','ATM+2') AND option_type='PUT'  THEN volume ELSE 0 END) AS put_vol,
        SUM(CASE WHEN strike_type IN ('ATM-2','ATM-1','ATM','ATM+1','ATM+2') AND option_type='CALL' THEN oi ELSE 0 END) AS call_oi,
        SUM(CASE WHEN strike_type IN ('ATM-2','ATM-1','ATM','ATM+1','ATM+2') AND option_type='PUT'  THEN oi ELSE 0 END) AS put_oi
      FROM base
      GROUP BY ALL
    ),
    lagged AS (
      SELECT
        *,
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
          PARTITION BY trade_date,expiry_type
          ORDER BY datetime
          ROWS BETWEEN 14 PRECEDING AND CURRENT ROW
        ) * SQRT(252.0*375.0) * 100.0 AS rv15_pct
      FROM lagged
    )
    SELECT *,
      atm_iv / NULLIF(rv15_pct,0) AS iv_rv_ratio
    FROM with_rv
    WHERE STRFTIME(datetime + INTERVAL '5 hours 30 minutes','%H:%M:%S') IN ({times})
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
      AND STRFTIME(datetime + INTERVAL '5 hours 30 minutes','%H:%M:%S')
          BETWEEN '09:40:00' AND '12:30:00'
    """


def cost_vector(cm: OptionCostModel, le, se, lx, sx, lot) -> np.ndarray:
    multiplier = lot.astype(float)
    gross = ((lx - le) + (se - sx)) * multiplier
    turnover = (le + se + lx + sx) * multiplier
    brokerage = 4.0 * cm.brokerage_per_order
    exchange = turnover * cm.exchange_rate
    sebi = turnover * cm.sebi_rate
    stt = (se + lx) * multiplier * cm.stt_sell_rate
    stamp = (le + sx) * multiplier * cm.stamp_buy_rate
    gst = cm.gst_rate * (brokerage + exchange + sebi)
    slippage = 4.0 * 0.20 * multiplier
    return gross - (brokerage + exchange + sebi + stt + stamp + gst + slippage)


def make_parameter_grid() -> pd.DataFrame:
    rows = []
    for oi in OI_THRESHOLDS:
        for vol in VOL_THRESHOLDS:
            for ret in RET_THRESHOLDS:
                for ivrv in IVRV_MIN:
                    for width in WIDTHS:
                        for hold in HOLDS:
                            rows.append({
                                "oi_thr": oi,
                                "vol_thr": vol,
                                "ret_thr": ret,
                                "iv_rv_min": ivrv,
                                "width_steps": width,
                                "hold_minutes": hold,
                            })
    return pd.DataFrame(rows)


def run_tournament(root: Path, out: Path) -> dict:
    con = duckdb.connect()
    features = con.execute(feature_query(root)).df()
    raw = con.execute(raw_query(root)).df()
    con.close()

    if features.empty or raw.empty:
        summary = {
            "features": int(len(features)),
            "raw_rows_used": int(len(raw)),
            "trades": 0,
            "variants": 0,
            "target_daily_net": 1000.0,
            "gate": "NO_DATA",
        }
        out.mkdir(parents=True, exist_ok=True)
        (out / "phase3f_directional_summary.json").write_text(json.dumps(summary, indent=2))
        return summary

    features["datetime"] = pd.to_datetime(features["datetime"])
    raw["datetime"] = pd.to_datetime(raw["datetime"])
    features["entry_time"] = features["datetime"] + pd.Timedelta(minutes=1)

    # One trade candidate per day/expiry/parameter tuple: first valid signal wins.
    threshold_rows = []
    for oi in OI_THRESHOLDS:
        for vol in VOL_THRESHOLDS:
            for ret in RET_THRESHOLDS:
                for ivrv in IVRV_MIN:
                    threshold_rows.append({
                        "oi_thr": oi,
                        "vol_thr": vol,
                        "ret_thr": ret,
                        "iv_rv_min": ivrv,
                    })
    params = pd.DataFrame(threshold_rows)

    signals = features.assign(_key=1).merge(params.assign(_key=1), on="_key").drop(columns="_key")
    signals["direction"] = np.where(
        (signals["oi_imb"] >= signals["oi_thr"])
        & (signals["vol_imb"] >= signals["vol_thr"])
        & (signals["spot_ret15"] >= signals["ret_thr"])
        & (signals["iv_rv_ratio"] >= signals["iv_rv_min"]),
        "CALL",
        np.where(
            (signals["oi_imb"] <= -signals["oi_thr"])
            & (signals["vol_imb"] <= -signals["vol_thr"])
            & (signals["spot_ret15"] <= -signals["ret_thr"])
            & (signals["iv_rv_ratio"] >= signals["iv_rv_min"]),
            "PUT",
            "",
        ),
    )
    signals = signals[signals["direction"] != ""].copy()
    signals = signals.sort_values(["trade_date","expiry_type","oi_thr","vol_thr","ret_thr","iv_rv_min","datetime"])
    signals = signals.drop_duplicates(
        ["trade_date","expiry_type","oi_thr","vol_thr","ret_thr","iv_rv_min"],
        keep="first",
    )

    # Keep only the quotes needed for entry selection.
    quote_cols = ["trade_date","expiry_type","datetime","option_type","strike_type","strike_price","close"]
    quotes = raw[quote_cols].drop_duplicates(
        ["trade_date","expiry_type","datetime","option_type","strike_type"],
        keep="last",
    ).copy()

    signals["atm_type"] = "ATM"
    signals["wing_type"] = np.where(signals["direction"].eq("CALL"), "ATM+1", "ATM-1")

    entry_atm = quotes.rename(columns={
        "datetime":"entry_time",
        "option_type":"direction",
        "strike_price":"atm_strike",
        "close":"atm_entry",
    })
    entry_atm = entry_atm[["trade_date","expiry_type","entry_time","direction","strike_type","atm_strike","atm_entry"]]
    signals = signals.merge(
        entry_atm,
        left_on=["trade_date","expiry_type","entry_time","direction","atm_type"],
        right_on=["trade_date","expiry_type","entry_time","direction","strike_type"],
        how="left",
    ).drop(columns=["strike_type"])

    entry_wing = quotes.rename(columns={
        "datetime":"entry_time",
        "option_type":"direction",
        "strike_price":"wing_strike",
        "close":"wing_entry",
    })
    entry_wing = entry_wing[["trade_date","expiry_type","entry_time","direction","strike_type","wing_strike","wing_entry"]]
    signals = signals.merge(
        entry_wing,
        left_on=["trade_date","expiry_type","entry_time","direction","wing_type"],
        right_on=["trade_date","expiry_type","entry_time","direction","strike_type"],
        how="left",
    ).drop(columns=["strike_type"])

    signals = signals.dropna(subset=["atm_strike","wing_strike","atm_entry","wing_entry"]).copy()
    signals = signals[signals["atm_entry"] > signals["wing_entry"]].copy()

    if signals.empty:
        summary = {
            "features": int(len(features)),
            "raw_rows_used": int(len(raw)),
            "signals": 0,
            "trades": 0,
            "variants": 0,
            "target_daily_net": 1000.0,
            "gate": "NO_VALID_ENTRY_QUOTES",
        }
        out.mkdir(parents=True, exist_ok=True)
        (out / "phase3f_directional_summary.json").write_text(json.dumps(summary, indent=2))
        return summary

    # Add the second width and holding periods after entry strikes are known.
    signals = signals.assign(_key=1).merge(
        pd.DataFrame({"width_steps": WIDTHS}).assign(_key=1), on="_key"
    ).merge(
        pd.DataFrame({"hold_minutes": HOLDS}).assign(_key=1), on="_key"
    ).drop(columns="_key")

    signals["wing_type_for_entry"] = np.where(
        signals["width_steps"].eq(1),
        signals["wing_type"],
        np.where(signals["direction"].eq("CALL"), "ATM+2", "ATM-2"),
    )

    # Add actual second-width wing strike at entry for width=2; retain width=1 already known.
    width2 = signals[signals["width_steps"].eq(2)].copy()
    width1 = signals[signals["width_steps"].eq(1)].copy()
    if not width2.empty:
        q2 = quotes.rename(columns={
            "datetime":"entry_time",
            "option_type":"direction",
            "strike_price":"wing2_strike",
            "close":"wing2_entry",
        })
        q2 = q2[["trade_date","expiry_type","entry_time","direction","strike_type","wing2_strike","wing2_entry"]]
        width2 = width2.merge(
            q2,
            left_on=["trade_date","expiry_type","entry_time","direction","wing_type_for_entry"],
            right_on=["trade_date","expiry_type","entry_time","direction","strike_type"],
            how="left",
        ).drop(columns=["strike_type"])
        width2["wing_strike"] = width2["wing2_strike"]
        width2["wing_entry"] = width2["wing2_entry"]
        width2 = width2.drop(columns=["wing2_strike","wing2_entry"])
    signals = pd.concat([width1, width2], ignore_index=True)
    signals = signals.dropna(subset=["wing_strike","wing_entry"]).copy()

    # Exit prices are looked up by the exact strike selected at entry, avoiding moving-ATM leakage.
    exits = raw[["trade_date","expiry_type","datetime","option_type","strike_price","close"]].drop_duplicates(
        ["trade_date","expiry_type","datetime","option_type","strike_price"], keep="last"
    )
    exits_atm = exits.rename(columns={"datetime":"exit_time","option_type":"direction","strike_price":"atm_strike","close":"atm_exit"})
    exits_wing = exits.rename(columns={"datetime":"exit_time","option_type":"direction","strike_price":"wing_strike","close":"wing_exit"})
    for hold in HOLDS:
        signals.loc[signals["hold_minutes"].eq(hold), "exit_time"] = signals.loc[
            signals["hold_minutes"].eq(hold), "entry_time"
        ] + pd.Timedelta(minutes=hold)

    signals = signals.merge(
        exits_atm[["trade_date","expiry_type","exit_time","direction","atm_strike","atm_exit"]],
        on=["trade_date","expiry_type","exit_time","direction","atm_strike"],
        how="left",
    )
    signals = signals.merge(
        exits_wing[["trade_date","expiry_type","exit_time","direction","wing_strike","wing_exit"]],
        on=["trade_date","expiry_type","exit_time","direction","wing_strike"],
        how="left",
    )
    signals = signals.dropna(subset=["atm_exit","wing_exit"]).copy()

    cm = OptionCostModel()
    signals["lot_size"] = signals["trade_date"].map(lambda d: nifty_lot_size(d))
    signals["net_pnl"] = cost_vector(
        cm,
        signals["atm_entry"].to_numpy(float),
        signals["wing_entry"].to_numpy(float),
        signals["atm_exit"].to_numpy(float),
        signals["wing_exit"].to_numpy(float),
        signals["lot_size"].to_numpy(float),
    )

    group_cols = [
        "expiry_type","width_steps","hold_minutes",
        "oi_thr","vol_thr","ret_thr","iv_rv_min"
    ]
    calendar_days = (
        features.groupby("expiry_type")["trade_date"].nunique().to_dict()
    )

    leaderboard = []
    daily_records = []
    for keys, g in signals.groupby(group_cols, dropna=False):
        expiry = keys[0]
        daily = g.groupby("trade_date")["net_pnl"].sum()
        ncal = int(calendar_days.get(expiry, daily.index.nunique()))
        wins = g.loc[g["net_pnl"] > 0, "net_pnl"].sum()
        losses = -g.loc[g["net_pnl"] < 0, "net_pnl"].sum()
        leaderboard.append({
            **dict(zip(group_cols, keys)),
            "trades": int(len(g)),
            "active_days": int(daily.size),
            "calendar_days": ncal,
            "mean_active_day_net": float(daily.mean()),
            "mean_all_day_net": float(g["net_pnl"].sum() / max(1, ncal)),
            "median_trade": float(g["net_pnl"].median()),
            "win_rate": float((g["net_pnl"] > 0).mean()),
            "positive_day_rate": float((daily > 0).sum() / max(1, ncal)),
            "profit_factor": float(wins / losses) if losses > 0 else 999.0,
            "total_net": float(g["net_pnl"].sum()),
            "max_drawdown": float((daily.cumsum() - daily.cumsum().cummax()).min()),
            "mean_entry_spread": float((g["atm_entry"] - g["wing_entry"]).mean()),
        })

    board = pd.DataFrame(leaderboard).sort_values(
        ["mean_all_day_net","positive_day_rate","profit_factor"],
        ascending=[False,False,False],
    ).reset_index(drop=True)

    out.mkdir(parents=True, exist_ok=True)
    signals.to_csv(out / "phase3f_directional_trades.csv", index=False)
    board.to_csv(out / "phase3f_directional_leaderboard.csv", index=False)

    target_count = int((board["mean_all_day_net"] >= 1000.0).sum())
    best = board.iloc[0].to_dict() if not board.empty else None
    summary = {
        "features": int(len(features)),
        "raw_rows_used": int(len(raw)),
        "signals_after_direction_filter": int(len(signals)),
        "trades": int(len(signals)),
        "variants": int(len(board)),
        "calendar_days_by_expiry_type": {str(k): int(v) for k,v in calendar_days.items()},
        "target_daily_net": 1000.0,
        "target_qualified_variants": target_count,
        "best": best,
        "gate": "PASS_PRELIMINARY" if best and best["mean_all_day_net"] >= 1000 else "FAIL_PRELIMINARY",
        "data_quality_note": (
            "16 negative-volume observations in the source were converted to null before "
            "volume aggregation; the volume feature remains provisional pending independent reconciliation."
        ),
    }
    (out / "phase3f_directional_summary.json").write_text(
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
    run_tournament(args.data, args.out)


if __name__ == "__main__":
    main()
