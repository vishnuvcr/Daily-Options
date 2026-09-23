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
BREAK_BUFFERS = (0.0, 0.0005, 0.0010)
POLARITIES = (1, -1)
WIDTHS = (1, 2)
HOLDS = (30, 60, 90)


def parquet_glob(root: Path) -> str:
    return (root / "**" / "*.parquet").as_posix()


def load_features(root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    source = parquet_glob(root)
    feature_sql = f"""
    WITH base AS (
      SELECT
        datetime,
        CAST(date AS DATE) AS trade_date,
        expiry_type,
        option_type,
        strike_type,
        CAST(strike_price AS DOUBLE) AS strike_price,
        CAST(spot AS DOUBLE) AS spot,
        CAST(oi AS DOUBLE) AS oi
      FROM read_parquet('{source}', union_by_name=true)
      WHERE close > 0
    ),
    ref AS (
      SELECT
        trade_date,
        expiry_type,
        ANY_VALUE(strike_price) FILTER (
          WHERE strike_type='ATM'
            AND STRFTIME(datetime + INTERVAL '5 hours 30 minutes','%H:%M:%S') BETWEEN '09:29:00' AND '09:31:00'
        ) AS ref_strike
      FROM base
      GROUP BY trade_date, expiry_type
    ),
    band AS (
      SELECT
        b.datetime,
        b.trade_date,
        b.expiry_type,
        b.option_type,
        b.strike_price,
        b.spot,
        b.oi
      FROM base b
      JOIN ref r
        ON b.trade_date=r.trade_date
       AND b.expiry_type=r.expiry_type
      WHERE ABS(b.strike_price-r.ref_strike) <= 100.0
    ),
    minute AS (
      SELECT
        datetime,
        trade_date,
        expiry_type,
        MAX(spot) AS spot,
        SUM(CASE WHEN option_type='CALL' THEN oi ELSE 0 END) AS call_oi,
        SUM(CASE WHEN option_type='PUT' THEN oi ELSE 0 END) AS put_oi
      FROM band
      GROUP BY ALL
    ),
    lagged AS (
      SELECT
        *,
        LAG(call_oi,15) OVER (PARTITION BY trade_date,expiry_type ORDER BY datetime) AS call_oi_15,
        LAG(put_oi,15) OVER (PARTITION BY trade_date,expiry_type ORDER BY datetime) AS put_oi_15,
        MAX(spot) OVER (
          PARTITION BY trade_date,expiry_type
          ORDER BY datetime
          ROWS BETWEEN 15 PRECEDING AND 1 PRECEDING
        ) AS prev15_high,
        MIN(spot) OVER (
          PARTITION BY trade_date,expiry_type
          ORDER BY datetime
          ROWS BETWEEN 15 PRECEDING AND 1 PRECEDING
        ) AS prev15_low,
        spot/LAG(spot,5) OVER (PARTITION BY trade_date,expiry_type ORDER BY datetime)-1 AS spot_ret5
      FROM minute
    )
    SELECT
      datetime,
      trade_date,
      expiry_type,
      spot,
      prev15_high,
      prev15_low,
      spot_ret5,
      (call_oi-call_oi_15)/NULLIF(call_oi_15,0) AS call_oi_chg15,
      (put_oi-put_oi_15)/NULLIF(put_oi_15,0) AS put_oi_chg15,
      (call_oi-call_oi_15)/NULLIF(call_oi_15,0)
        - (put_oi-put_oi_15)/NULLIF(put_oi_15,0) AS oi_reposition
    FROM lagged
    WHERE prev15_high IS NOT NULL
      AND prev15_low IS NOT NULL
      AND call_oi_15 IS NOT NULL
      AND put_oi_15 IS NOT NULL
      AND STRFTIME(datetime + INTERVAL '5 hours 30 minutes','%H:%M:%S') BETWEEN '09:45:00' AND '12:30:00'
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
      AND STRFTIME(datetime + INTERVAL '5 hours 30 minutes','%H:%M:%S')
          BETWEEN '09:40:00' AND '14:00:00'
    """

    con = duckdb.connect()
    feat = con.execute(feature_sql).df()
    raw = con.execute(raw_sql).df()
    con.close()
    feat["datetime"] = pd.to_datetime(feat["datetime"])
    raw["datetime"] = pd.to_datetime(raw["datetime"])
    return feat, raw


def event_candidates(features: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for threshold in OI_THRESHOLDS:
        for buffer in BREAK_BUFFERS:
            for polarity in POLARITIES:
                x = features.copy()
                up = x.spot >= x.prev15_high * (1.0 + buffer)
                dn = x.spot <= x.prev15_low * (1.0 - buffer)
                same_up = up & (polarity * x.oi_reposition >= threshold)
                same_dn = dn & (polarity * x.oi_reposition <= -threshold)
                x["direction"] = np.where(same_up, "CALL", np.where(same_dn, "PUT", ""))
                x = x[x.direction != ""].copy()
                if x.empty:
                    continue
                x["oi_threshold"] = threshold
                x["break_buffer"] = buffer
                x["polarity"] = polarity
                x = x.sort_values(["trade_date","expiry_type","datetime"]).drop_duplicates(
                    ["trade_date","expiry_type"], keep="first"
                )
                rows.append(x)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def add_entries(events: pd.DataFrame, raw: pd.DataFrame) -> pd.DataFrame:
    if events.empty:
        return events
    x = events.copy()
    x["entry_time"] = x["datetime"] + pd.Timedelta(minutes=1)
    q = raw[["trade_date","expiry_type","datetime","option_type","strike_type","strike_price","close"]].drop_duplicates(
        ["trade_date","expiry_type","datetime","option_type","strike_type"], keep="last"
    )
    x["atm_type"] = "ATM"
    x["wing1_type"] = np.where(x.direction.eq("CALL"), "ATM+1", "ATM-1")
    x["wing2_type"] = np.where(x.direction.eq("CALL"), "ATM+2", "ATM-2")

    atm = q.rename(columns={"datetime":"entry_time","option_type":"direction","strike_price":"atm_strike","close":"atm_entry"})
    atm = atm[atm.strike_type=="ATM"]
    x = x.merge(
        atm[["trade_date","expiry_type","entry_time","direction","atm_strike","atm_entry"]],
        on=["trade_date","expiry_type","entry_time","direction"],
        how="left",
    )

    w1 = q.rename(columns={"datetime":"entry_time","option_type":"direction","strike_price":"wing1_strike","close":"wing1_entry"})
    x = x.merge(
        w1[["trade_date","expiry_type","entry_time","direction","strike_type","wing1_strike","wing1_entry"]],
        left_on=["trade_date","expiry_type","entry_time","direction","wing1_type"],
        right_on=["trade_date","expiry_type","entry_time","direction","strike_type"],
        how="left",
    ).drop(columns=["strike_type"])

    w2 = q.rename(columns={"datetime":"entry_time","option_type":"direction","strike_price":"wing2_strike","close":"wing2_entry"})
    x = x.merge(
        w2[["trade_date","expiry_type","entry_time","direction","strike_type","wing2_strike","wing2_entry"]],
        left_on=["trade_date","expiry_type","entry_time","direction","wing2_type"],
        right_on=["trade_date","expiry_type","entry_time","direction","strike_type"],
        how="left",
    ).drop(columns=["strike_type"])

    return x.dropna(subset=["atm_strike","atm_entry","wing1_strike","wing1_entry","wing2_strike","wing2_entry"]).copy()


def evaluate(events: pd.DataFrame, raw: pd.DataFrame, features: pd.DataFrame, out: Path) -> pd.DataFrame:
    if events.empty:
        return pd.DataFrame()

    q = raw[["trade_date","expiry_type","datetime","option_type","strike_price","close"]].drop_duplicates(
        ["trade_date","expiry_type","datetime","option_type","strike_price"], keep="last"
    )

    all_rows = []
    cm = OptionCostModel()
    for width in WIDTHS:
        e = events.copy()
        if width == 1:
            e["wing_strike"] = e["wing1_strike"]
            e["wing_entry"] = e["wing1_entry"]
        else:
            e["wing_strike"] = e["wing2_strike"]
            e["wing_entry"] = e["wing2_entry"]

        for hold in HOLDS:
            x = e.copy()
            x["exit_time"] = x["entry_time"] + pd.Timedelta(minutes=hold)
            for option_type, strike_col, out_col in [
                ("CALL","atm_strike","long_exit"),
                ("CALL","wing_strike","short_exit"),
            ]:
                y = q[q.option_type==option_type].rename(
                    columns={"datetime":"exit_time","strike_price":"_strike","close":out_col}
                )
                x = x.merge(
                    y[["trade_date","expiry_type","exit_time","_strike",out_col]],
                    left_on=["trade_date","expiry_type","exit_time",strike_col],
                    right_on=["trade_date","expiry_type","exit_time","_strike"],
                    how="left",
                ).drop(columns=["_strike"])
                # For puts, this is swapped below through direction-specific selection.
            call = q[q.option_type=="CALL"].rename(
                columns={"datetime":"exit_time","strike_price":"_strike","close":"call_exit"}
            )
            put = q[q.option_type=="PUT"].rename(
                columns={"datetime":"exit_time","strike_price":"_strike","close":"put_exit"}
            )

            # Rebuild exact leg exits directionally with a compact per-direction merge.
            x = e.copy()
            x["exit_time"] = x["entry_time"] + pd.Timedelta(minutes=hold)
            call_atm = call[["trade_date","expiry_type","exit_time","_strike","close"]].rename(columns={"_strike":"atm_strike","close":"call_atm_exit"})
            put_atm = put[["trade_date","expiry_type","exit_time","_strike","close"]].rename(columns={"_strike":"atm_strike","close":"put_atm_exit"})
            call_w1 = call[["trade_date","expiry_type","exit_time","_strike","close"]].rename(columns={"_strike":"wing_strike","close":"call_wing_exit"})
            put_w1 = put[["trade_date","expiry_type","exit_time","_strike","close"]].rename(columns={"_strike":"wing_strike","close":"put_wing_exit"})

            x = x.merge(call_atm, on=["trade_date","expiry_type","exit_time","atm_strike"], how="left")
            x = x.merge(put_atm, on=["trade_date","expiry_type","exit_time","atm_strike"], how="left")
            x = x.merge(call_w1, on=["trade_date","expiry_type","exit_time","wing_strike"], how="left")
            x = x.merge(put_w1, on=["trade_date","expiry_type","exit_time","wing_strike"], how="left")

            x["long_exit"] = np.where(x.direction=="CALL", x.call_atm_exit, x.put_atm_exit)
            x["short_exit"] = np.where(x.direction=="CALL", x.call_wing_exit, x.put_wing_exit)
            x = x.dropna(subset=["long_exit","short_exit"]).copy()
            if x.empty:
                continue

            # x["long_entry"] is ATM and x["short_entry"] is selected wing for a debit spread.
            x["net_pnl"] = [
                cm.vertical_debit_spread_net_pnl(
                    float(a), float(b), float(c), float(d),
                    lot_size=nifty_lot_size(dt),
                    qty=1,
                    slippage_points=0.20,
                )
                for a,b,c,d,dt in zip(
                    x.atm_entry, x.wing_entry, x.long_exit, x.short_exit, x.trade_date
                )
            ]
            x["width_steps"] = width
            x["hold_minutes"] = hold
            all_rows.append(x)

    trades = pd.concat(all_rows, ignore_index=True) if all_rows else pd.DataFrame()
    if trades.empty:
        return pd.DataFrame()

    group_cols = ["expiry_type","oi_threshold","break_buffer","polarity","width_steps","hold_minutes"]
    rows = []
    for keys, g in trades.groupby(group_cols):
        d = g.groupby("trade_date").net_pnl.sum()
        cal = int(features[features.expiry_type.eq(keys[0])].trade_date.nunique())
        wins = g.loc[g.net_pnl>0,"net_pnl"].sum()
        losses = -g.loc[g.net_pnl<0,"net_pnl"].sum()
        rows.append({
            **dict(zip(group_cols,keys)),
            "trades": int(len(g)),
            "active_days": int(len(d)),
            "calendar_days": cal,
            "mean_active_day_net": float(d.mean()),
            "mean_all_day_net": float(g.net_pnl.sum()/max(1,cal)),
            "median_trade": float(g.net_pnl.median()),
            "win_rate": float((g.net_pnl>0).mean()),
            "positive_day_rate": float((d>0).sum()/max(1,cal)),
            "profit_factor": float(wins/losses) if losses else 999.0,
            "total_net": float(g.net_pnl.sum()),
            "max_drawdown": float((d.cumsum()-d.cumsum().cummax()).min()),
            "mean_entry_spread": float((g.atm_entry-g.wing_entry).mean()),
        })

    board = pd.DataFrame(rows).sort_values(
        ["mean_all_day_net","profit_factor","win_rate"],
        ascending=[False,False,False],
    ).reset_index(drop=True)

    out.mkdir(parents=True, exist_ok=True)
    trades.to_csv(out/"phase3f_oi_repositioning_trades.csv", index=False)
    board.to_csv(out/"phase3f_oi_repositioning_leaderboard.csv", index=False)

    return board


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=Path("reports"))
    args = ap.parse_args()

    features, raw = load_features(args.data)
    events = event_candidates(features)
    events = add_entries(events, raw)
    board = evaluate(events, raw, features, args.out)

    best = board.iloc[0].to_dict() if not board.empty else None
    summary = {
        "feature_rows": int(len(features)),
        "event_candidates": int(len(events)),
        "variants": int(len(board)),
        "target_daily_net": 1000.0,
        "target_qualified": int((board.mean_all_day_net >= 1000).sum()) if not board.empty else 0,
        "best": best,
        "gate": "PASS_PRELIMINARY" if best and best["mean_all_day_net"] >= 1000 else "FAIL_PRELIMINARY",
    }
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out/"phase3f_oi_repositioning_summary.json").write_text(
        json.dumps(summary, indent=2, default=str), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
