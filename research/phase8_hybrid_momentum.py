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


ENTRY_STARTS = ("09:45:00", "10:00:00")
EXPIRIES = ("WEEK", "MONTH")
HOLDS = (15, 30, 45)
CONDITION_LEVELS = (3, 4)
RISK_PROFILES = (
    {"sl_pct": 0.15, "target_pct": 0.40, "trail_trigger": 0.12, "trail_gap": 0.08},
    {"sl_pct": 0.20, "target_pct": 0.60, "trail_trigger": 0.20, "trail_gap": 0.12},
)


@dataclass(frozen=True)
class Variant:
    family: str
    entry_start: str
    expiry_type: str
    condition_level: int
    hold_minutes: int
    risk_id: int

    @property
    def key(self) -> str:
        return (
            f"{self.family}|{self.entry_start}|{self.expiry_type}|"
            f"{self.condition_level}|{self.hold_minutes}|risk{self.risk_id}"
        )


def variant_grid() -> list[Variant]:
    return [
        Variant(family, entry_start, expiry_type, level, hold, risk_id)
        for family in ("trend", "mean_reversion")
        for entry_start in ENTRY_STARTS
        for expiry_type in EXPIRIES
        for level in CONDITION_LEVELS
        for hold in HOLDS
        for risk_id in range(len(RISK_PROFILES))
    ]


def parquet_glob(root: Path) -> str:
    return (root / "**" / "*.parquet").as_posix()


def load_features(root: Path) -> pd.DataFrame:
    glob = parquet_glob(root)
    sql = f"""
    WITH base AS (
      SELECT
        datetime,
        CAST(date AS DATE) AS trade_date,
        expiry_type,
        option_type,
        strike_type,
        CAST(spot AS DOUBLE) AS spot,
        CAST(open AS DOUBLE) AS open,
        CAST(high AS DOUBLE) AS high,
        CAST(low AS DOUBLE) AS low,
        CAST(close AS DOUBLE) AS close,
        CAST(iv AS DOUBLE) AS iv,
        CASE WHEN volume >= 0 THEN CAST(volume AS DOUBLE) ELSE NULL END AS volume,
        CAST(oi AS DOUBLE) AS oi
      FROM read_parquet('{glob}', union_by_name=true)
      WHERE close > 0
        AND expiry_type IN ('WEEK','MONTH')
    ),
    minute AS (
      SELECT
        datetime,
        trade_date,
        expiry_type,
        MAX(spot) AS spot,
        MAX(CASE WHEN strike_type='ATM' AND option_type='CALL' THEN open END) AS call_open,
        MAX(CASE WHEN strike_type='ATM' AND option_type='CALL' THEN close END) AS call_close,
        MAX(CASE WHEN strike_type='ATM' AND option_type='PUT' THEN open END) AS put_open,
        MAX(CASE WHEN strike_type='ATM' AND option_type='PUT' THEN close END) AS put_close,
        AVG(CASE WHEN strike_type='ATM' AND option_type='CALL' AND iv BETWEEN 0 AND 300 THEN iv END) AS call_iv,
        AVG(CASE WHEN strike_type='ATM' AND option_type='PUT' AND iv BETWEEN 0 AND 300 THEN iv END) AS put_iv,
        SUM(CASE WHEN strike_type IN ('ATM-2','ATM-1','ATM','ATM+1','ATM+2') AND option_type='CALL' THEN volume ELSE 0 END) AS call_vol,
        SUM(CASE WHEN strike_type IN ('ATM-2','ATM-1','ATM','ATM+1','ATM+2') AND option_type='PUT' THEN volume ELSE 0 END) AS put_vol,
        SUM(CASE WHEN strike_type IN ('ATM-2','ATM-1','ATM','ATM+1','ATM+2') AND option_type='CALL' THEN oi ELSE 0 END) AS call_oi,
        SUM(CASE WHEN strike_type IN ('ATM-2','ATM-1','ATM','ATM+1','ATM+2') AND option_type='PUT' THEN oi ELSE 0 END) AS put_oi
      FROM base
      WHERE STRFTIME(datetime + INTERVAL '5 hours 30 minutes','%H:%M:%S') BETWEEN '09:15:00' AND '12:45:00'
      GROUP BY ALL
    )
    SELECT * FROM minute
    ORDER BY trade_date, expiry_type, datetime
    """
    con = duckdb.connect()
    df = con.execute(sql).df()
    con.close()
    if df.empty:
        return df

    df["datetime"] = pd.to_datetime(df["datetime"], utc=True) + pd.Timedelta(hours=5, minutes=30)
    df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date
    df = df.sort_values(["trade_date", "expiry_type", "datetime"]).reset_index(drop=True)

    g = df.groupby(["trade_date", "expiry_type"], sort=False)
    df["ret1"] = g["spot"].pct_change(1)
    df["ret3"] = g["spot"].pct_change(3)
    df["ret5"] = g["spot"].pct_change(5)
    df["roll_mean20"] = g["spot"].transform(lambda s: s.rolling(20, min_periods=20).mean())
    df["roll_std20"] = g["spot"].transform(lambda s: s.rolling(20, min_periods=20).std())
    df["z20"] = (df["spot"] - df["roll_mean20"]) / df["roll_std20"].replace(0, np.nan)
    df["ema9"] = g["spot"].transform(lambda s: s.ewm(span=9, adjust=False, min_periods=9).mean())
    df["ema20"] = g["spot"].transform(lambda s: s.ewm(span=20, adjust=False, min_periods=20).mean())
    df["ema50"] = g["spot"].transform(lambda s: s.ewm(span=50, adjust=False, min_periods=50).mean())

    delta = g["spot"].diff()
    gain = delta.clip(lower=0).groupby([df["trade_date"], df["expiry_type"]]).transform(
        lambda s: s.rolling(14, min_periods=14).mean()
    )
    loss = (-delta.clip(upper=0)).groupby([df["trade_date"], df["expiry_type"]]).transform(
        lambda s: s.rolling(14, min_periods=14).mean()
    )
    rs = gain / loss.replace(0, np.nan)
    df["rsi14"] = 100 - (100 / (1 + rs))

    df["call_ret1"] = g["call_close"].pct_change(1)
    df["call_ret3"] = g["call_close"].pct_change(3)
    df["put_ret1"] = g["put_close"].pct_change(1)
    df["put_ret3"] = g["put_close"].pct_change(3)

    df["oi_imb"] = (df["call_oi"] - df["put_oi"]) / (df["call_oi"] + df["put_oi"]).replace(0, np.nan)
    df["vol_imb"] = (df["call_vol"] - df["put_vol"]) / (df["call_vol"] + df["put_vol"]).replace(0, np.nan)

    df["session_minute"] = df["datetime"].dt.hour * 60 + df["datetime"].dt.minute - (9 * 60 + 15)
    local_times = df["datetime"].dt.strftime("%H:%M:%S")
    return df.loc[local_times.between("09:30:00", "12:30:00")].copy()


def make_signals(features: pd.DataFrame) -> pd.DataFrame:
    if features.empty:
        return pd.DataFrame()

    rows = []
    for v in variant_grid():
        x = features.loc[
            (features["expiry_type"] == v.expiry_type)
            & (features["datetime"].dt.strftime("%H:%M:%S") >= v.entry_start)
        ].copy()
        if x.empty:
            continue

        trend_long = pd.DataFrame({
            "trend": (x["ema20"] > x["ema50"]) & (x["ema9"] > x["ema20"]),
            "rsi": x["rsi14"] >= 55,
            "momentum": x["ret3"] > 0,
            "option_confirmation": (x["call_ret1"] > 0) & (x["call_ret3"] > 0),
        }, index=x.index)
        trend_short = pd.DataFrame({
            "trend": (x["ema20"] < x["ema50"]) & (x["ema9"] < x["ema20"]),
            "rsi": x["rsi14"] <= 45,
            "momentum": x["ret3"] < 0,
            "option_confirmation": (x["put_ret1"] > 0) & (x["put_ret3"] > 0),
        }, index=x.index)

        mr_long = pd.DataFrame({
            "oversold": x["rsi14"] <= 30,
            "vol_extreme": x["z20"] <= -2,
            "weak_trend": (x["ema20"] - x["ema50"]).abs() / x["spot"] <= 0.0015,
            "option_confirmation": (x["call_ret1"] > 0) & (x["call_ret3"] > 0),
        }, index=x.index)
        mr_short = pd.DataFrame({
            "overbought": x["rsi14"] >= 70,
            "vol_extreme": x["z20"] >= 2,
            "weak_trend": (x["ema20"] - x["ema50"]).abs() / x["spot"] <= 0.0015,
            "option_confirmation": (x["put_ret1"] > 0) & (x["put_ret3"] > 0),
        }, index=x.index)

        if v.family == "trend":
            long_ok = trend_long.sum(axis=1) >= v.condition_level
            short_ok = trend_short.sum(axis=1) >= v.condition_level
        else:
            long_ok = mr_long.sum(axis=1) >= v.condition_level
            short_ok = mr_short.sum(axis=1) >= v.condition_level

        x["direction"] = np.where(long_ok, "CALL", np.where(short_ok, "PUT", ""))
        x = x.loc[x["direction"] != ""].sort_values(["trade_date", "datetime"])
        x = x.drop_duplicates(["trade_date"], keep="first")
        if x.empty:
            continue

        risk = RISK_PROFILES[v.risk_id]
        x["variant_id"] = v.key
        x["family"] = v.family
        x["entry_time_local"] = x["datetime"] + pd.Timedelta(minutes=1)
        x["hold_minutes"] = v.hold_minutes
        x["risk_id"] = v.risk_id
        x["sl_pct"] = risk["sl_pct"]
        x["target_pct"] = risk["target_pct"]
        x["trail_trigger"] = risk["trail_trigger"]
        x["trail_gap"] = risk["trail_gap"]
        rows.append(x[[
            "variant_id","family","risk_id","trade_date","datetime","entry_time_local",
            "direction","spot","hold_minutes","sl_pct","target_pct","trail_trigger","trail_gap"
        ]])

    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def attach_contract_paths(signals: pd.DataFrame, root: Path) -> pd.DataFrame:
    if signals.empty:
        return signals
    con = duckdb.connect()
    con.register("signals_df", signals)
    glob = parquet_glob(root)

    sql = f"""
    WITH raw AS (
      SELECT
        CAST(date AS DATE) AS trade_date,
        expiry_type,
        option_type,
        CAST(strike_price AS DOUBLE) AS strike_price,
        CAST(datetime AS TIMESTAMPTZ) + INTERVAL '5 hours 30 minutes' AS local_ts,
        CAST(open AS DOUBLE) AS open
      FROM read_parquet('{glob}', union_by_name=true)
      WHERE close > 0 AND expiry_type IN ('WEEK','MONTH')
    ),
    ranked AS (
      SELECT s.*, r.strike_price, r.local_ts,
             ROW_NUMBER() OVER (
               PARTITION BY s.variant_id, s.trade_date
               ORDER BY ABS(r.strike_price - s.spot), r.local_ts
             ) AS rn
      FROM signals_df s
      JOIN raw r
        ON r.trade_date=s.trade_date
       AND r.expiry_type=split_part(s.variant_id,'|',3)
       AND r.option_type=s.direction
       AND r.local_ts BETWEEN s.entry_time_local AND s.entry_time_local + INTERVAL '2 minutes'
    )
    SELECT * FROM ranked WHERE rn=1
    """
    entries = con.execute(sql).df()
    con.close()
    if entries.empty:
        return entries
    if "open" not in entries.columns:
        raise ValueError("Phase 8 executable-entry query must include option open price")
    entries["entry_time_local"] = pd.to_datetime(entries["local_ts"])
    entries["entry_price"] = pd.to_numeric(entries["open"], errors="coerce")
    entries = entries.loc[entries["entry_price"].gt(0)].copy()
    return entries


def simulate_paths(entries: pd.DataFrame, root: Path, out_dir: Path, slippage: float) -> pd.DataFrame:
    if entries.empty:
        return pd.DataFrame()

    con = duckdb.connect()
    con.register("entries_df", entries)
    glob = parquet_glob(root)
    sql = f"""
    WITH raw AS (
      SELECT
        CAST(date AS DATE) AS trade_date,
        expiry_type,
        option_type,
        CAST(strike_price AS DOUBLE) AS strike_price,
        CAST(datetime AS TIMESTAMPTZ) + INTERVAL '5 hours 30 minutes' AS local_ts,
        CAST(open AS DOUBLE) AS open,
        CAST(high AS DOUBLE) AS high,
        CAST(low AS DOUBLE) AS low,
        CAST(close AS DOUBLE) AS close
      FROM read_parquet('{glob}', union_by_name=true)
      WHERE close > 0 AND expiry_type IN ('WEEK','MONTH')
    )
    SELECT e.variant_id,e.family,e.risk_id,e.trade_date,e.direction,e.strike_price,
           e.entry_time_local,e.entry_price,e.hold_minutes,e.sl_pct,e.target_pct,
           e.trail_trigger,e.trail_gap,r.local_ts,r.open,r.high,r.low,r.close
    FROM entries_df e
    JOIN raw r
      ON r.trade_date=e.trade_date
     AND r.expiry_type=split_part(e.variant_id,'|',3)
     AND r.option_type=e.direction
     AND r.strike_price=e.strike_price
     AND r.local_ts>=e.entry_time_local
     AND r.local_ts<=e.entry_time_local + e.hold_minutes*INTERVAL '1 minute'
    ORDER BY e.variant_id,e.trade_date,r.local_ts
    """
    rows = con.execute(sql).df()
    con.close()
    if rows.empty:
        return pd.DataFrame()

    cm = OptionCostModel()
    result = []
    for (variant_id, trade_date), g in rows.groupby(["variant_id","trade_date"], sort=False):
        g=g.sort_values("local_ts")
        first=g.iloc[0]
        entry=float(first.entry_price)
        sl=entry*(1-float(first.sl_pct))
        tgt=entry*(1+float(first.target_pct))
        trigger=entry*(1+float(first.trail_trigger))
        trail_active=False
        trail_stop=sl
        peak=entry
        exit_price=float(g.iloc[-1].close)
        exit_time=g.iloc[-1].local_ts
        reason="TIME"

        for _,bar in g.iterrows():
            high=float(bar.high); low=float(bar.low)
            if low <= sl:
                exit_price=sl; exit_time=bar.local_ts; reason="SL"; break
            if high >= tgt:
                exit_price=tgt; exit_time=bar.local_ts; reason="TARGET"; break
            if trail_active and low <= trail_stop:
                exit_price=trail_stop; exit_time=bar.local_ts; reason="TRAIL"; break
            if high >= trigger:
                trail_active=True
            if trail_active:
                peak=max(peak,high)
                trail_stop=max(trail_stop, peak*(1-float(first.trail_gap)))

        pnl=cm.net_pnl(entry,exit_price,1,nifty_lot_size(trade_date),slippage_points=slippage)
        result.append({
            "variant_id":variant_id,"family":first.family,"risk_id":int(first.risk_id),
            "trade_date":trade_date,"direction":first.direction,
            "entry_time":first.entry_time_local,"exit_time":exit_time,
            "entry_price":entry,"exit_price":exit_price,"net_pnl":pnl,
            "exit_reason":reason
        })
    out=pd.DataFrame(result)
    out_dir.mkdir(parents=True,exist_ok=True)
    out.to_csv(out_dir/"phase8_trades.csv",index=False)
    return out


def summarize(trades: pd.DataFrame, features: pd.DataFrame, out_dir: Path, slippage: float) -> dict:
    out_dir.mkdir(parents=True,exist_ok=True)
    if trades.empty:
        summary={"trades":0,"variants":0,"slippage":slippage,"gate":"NO_TRADES"}
        (out_dir/"phase8_summary.json").write_text(json.dumps(summary,indent=2))
        return summary

    ncal=features.groupby("expiry_type")["trade_date"].nunique().to_dict()
    board=[]
    for variant,g in trades.groupby("variant_id",sort=False):
        daily=g.groupby("trade_date")["net_pnl"].sum()
        exp=variant.split("|")[2]
        wins=g.loc[g.net_pnl>0,"net_pnl"].sum()
        losses=-g.loc[g.net_pnl<0,"net_pnl"].sum()
        board.append({
            "variant_id":variant,
            "trades":len(g),
            "active_days":int(daily.size),
            "calendar_days":int(ncal.get(exp,daily.size)),
            "mean_active_day_net":float(daily.mean()),
            "mean_all_day_net":float(g.net_pnl.sum()/max(1,int(ncal.get(exp,daily.size)))),
            "median_trade":float(g.net_pnl.median()),
            "win_rate":float((g.net_pnl>0).mean()),
            "positive_day_rate_active":float((daily>0).mean()),
            "profit_factor":float(wins/losses) if losses>0 else 999.0,
            "max_drawdown":float((daily.cumsum()-daily.cumsum().cummax()).min()),
            "total_net":float(g.net_pnl.sum())
        })
    board=pd.DataFrame(board).sort_values(
        ["mean_active_day_net","positive_day_rate_active","profit_factor"],
        ascending=[False,False,False]
    ).reset_index(drop=True)
    board.to_csv(out_dir/"phase8_leaderboard.csv",index=False)

    best=board.iloc[0].to_dict()
    summary={
        "trades":int(len(trades)),
        "variants":int(len(board)),
        "target_qualified_variants":int((board["mean_active_day_net"]>=1000).sum()),
        "best":best,
        "slippage_points":slippage,
        "preliminary_gate":"PASS_PRELIMINARY" if (board["mean_active_day_net"]>=1000).any() else "FAIL_PRELIMINARY"
    }
    (out_dir/"phase8_summary.json").write_text(json.dumps(summary,indent=2,default=str))
    return summary


def run(data_root:Path,out_root:Path,slippage:float)->dict:
    features=load_features(data_root)
    if features.empty:
        return {"gate":"NO_DATA"}
    signals=make_signals(features)
    out_root.mkdir(parents=True,exist_ok=True)
    signals.to_csv(out_root/"phase8_signals.csv",index=False)
    entries=attach_contract_paths(signals,data_root)
    entries.to_csv(out_root/"phase8_entries.csv",index=False)
    trades=simulate_paths(entries,data_root,out_root,slippage)
    return summarize(trades,features,out_root,slippage)


def main()->None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--data",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--slippage",type=float,default=0.20)
    args=ap.parse_args()
    print(json.dumps(run(args.data,args.out,args.slippage),indent=2,default=str))


if __name__=="__main__":
    main()

# Phase 8 v2 execution checkpoint
