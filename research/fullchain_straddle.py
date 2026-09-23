from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl

from research.contracts import nifty_lot_size
from research.cost_model import OptionCostModel

ANNUAL_MINUTES = 252 * 375
RISK_FREE = 0.06


@dataclass(frozen=True)
class Core:
    entry: str
    stop: float
    target_decay: float
    hold: int
    vrp_min: float


def bs_call(s, k, t, r, sigma):
    if t <= 0:
        return max(s-k, 0.0)
    if sigma <= 0:
        return max(s-k*math.exp(-r*t), 0.0)
    d1=(math.log(s/k)+(r+0.5*sigma*sigma)*t)/(sigma*math.sqrt(t))
    d2=d1-sigma*math.sqrt(t)
    cdf=lambda x: 0.5*(1+math.erf(x/math.sqrt(2)))
    return s*cdf(d1)-k*math.exp(-r*t)*cdf(d2)


def implied_vol(s,k,t,straddle):
    if not np.isfinite(straddle) or straddle <= abs(s-k) or t <= 0:
        return np.nan
    lo,hi=1e-4,5.0
    for _ in range(50):
        mid=(lo+hi)/2
        call=bs_call(s,k,t,RISK_FREE,mid)
        put=call-s+k*math.exp(-RISK_FREE*t)
        if call+put > straddle:
            hi=mid
        else:
            lo=mid
    return (lo+hi)/2


def load_year(path):
    cols=["date","timestamp","expiry","strike","option_type","open","high","low","close","volume"]
    df=pl.read_parquet(path, columns=cols)
    df=df.with_columns([
        pl.col("date").cast(pl.Date),
        pl.col("timestamp").cast(pl.Datetime("us")),
        pl.col("expiry").str.strptime(pl.Date, "%Y-%m-%d", strict=False),
        pl.col("strike").cast(pl.Float64),
        pl.col("option_type").cast(pl.String).str.to_uppercase(),
        pl.col("close").cast(pl.Float64),
        pl.col("high").cast(pl.Float64),
        pl.col("low").cast(pl.Float64),
    ])
    df=df.filter(pl.col("option_type").is_in(["CE","PE"]))
    return df


def forward_series(day_df: pl.DataFrame, expiry, strike, start, end):
    q=day_df.filter(
        (pl.col("expiry")==expiry) &
        (pl.col("strike")==strike) &
        (pl.col("timestamp")>=start) &
        (pl.col("timestamp")<=end)
    ).select(["timestamp","option_type","close"])
    if q.height==0:
        return None
    p=q.pivot(values="close",index="timestamp",columns="option_type",aggregate_function="first").sort("timestamp")
    if "CE" not in p.columns or "PE" not in p.columns:
        return None
    return p.with_columns((pl.col("strike") if "strike" in p.columns else pl.lit(float(strike))).alias("K"))


def prepare_day(day_df: pl.DataFrame, day, entry_label: str):
    expiry=day_df.select(pl.col("expiry").min()).item()
    if expiry is None or expiry < day:
        return None

    entry_time=pd.Timestamp(f"{day} {entry_label}")
    q=day_df.filter(
        (pl.col("expiry")==expiry) &
        (pl.col("timestamp")>=entry_time.to_datetime64()) &
        (pl.col("timestamp")<=(entry_time+pd.Timedelta(minutes=2)).to_datetime64()) &
        (pl.col("close")>0)
    )
    if q.height==0:
        return None

    px=q.group_by(["strike","option_type"]).agg(pl.col("close").first()).pivot(
        values="close",index="strike",columns="option_type",aggregate_function="first"
    )
    if "CE" not in px.columns or "PE" not in px.columns:
        return None
    px=px.drop_nulls(["CE","PE"]).with_columns(
        (pl.col("CE")-pl.col("PE")).abs().alias("parity_gap")
    ).sort("parity_gap")
    if px.height==0:
        return None

    strike=float(px["strike"][0])
    ce0=float(px["CE"][0]); pe0=float(px["PE"][0])
    entry=ce0+pe0

    fwd=day_df.filter(
        (pl.col("expiry")==expiry) &
        (pl.col("strike")==strike) &
        (pl.col("timestamp")>= (entry_time-pd.Timedelta(minutes=30)).to_datetime64()) &
        (pl.col("timestamp")<=entry_time.to_datetime64())
    ).select(["timestamp","option_type","close"])
    if fwd.height==0:
        return None
    f=fwd.pivot(values="close",index="timestamp",columns="option_type",aggregate_function="first").sort("timestamp")
    if "CE" not in f.columns or "PE" not in f.columns:
        return None
    rvf=(f.with_columns((pl.lit(strike)+pl.col("CE")-pl.col("PE")).alias("forward"))
           .select(["timestamp","forward"]))
    rvp=rvf.to_pandas()
    if len(rvp)<15:
        return None
    rv=float(rvp["forward"].pct_change().dropna().std()*math.sqrt(ANNUAL_MINUTES))

    forward=float(strike+ce0-pe0)
    years=max((pd.Timestamp(expiry)-entry_time)/pd.Timedelta(days=365.25),1/3650)
    iv=implied_vol(forward,strike,float(years),entry)
    vrp=iv-rv if np.isfinite(iv) else np.nan

    first15_end=day+pd.Timedelta(hours=9,minutes=30)
    ff=rvf.filter(
        (pl.col("timestamp")>=pd.Timestamp(day)+pd.Timedelta(hours=9,minutes=15)) &
        (pl.col("timestamp")<first15_end)
    )
    first15_range=np.nan
    if ff.height:
        vals=ff["forward"].to_numpy()
        first15_range=(np.nanmax(vals)-np.nanmin(vals))/forward if forward else np.nan

    path=day_df.filter(
        (pl.col("expiry")==expiry) &
        (pl.col("strike")==strike) &
        (pl.col("timestamp")>entry_time.to_datetime64()) &
        (pl.col("timestamp")<=(entry_time+pd.Timedelta(minutes=180)).to_datetime64())
    ).select(["timestamp","option_type","high","low","close"])
    piv=path.pivot(values=["high","low","close"],index="timestamp",columns="option_type",aggregate_function="first").sort("timestamp")
    needed=[f"{v}_{t}" for v in ("high","low","close") for t in ("CE","PE")]
    if piv.height==0 or not all(c in piv.columns for c in needed):
        return None
    return {
        "date":day,"entry":entry_label,"expiry":expiry,"strike":strike,"entry_premium":entry,
        "vrp":vrp,"iv":iv,"rv":rv,"first15_range":first15_range,
        "lot":nifty_lot_size(day),"piv":piv.to_pandas()
    }


def simulate(obs, stop_mult, target_decay, hold):
    p=obs["piv"].iloc[:hold].copy()
    entry=obs["entry_premium"]
    stop=entry*stop_mult; target=entry*(1-target_decay)
    xt=None; exit_value=None; reason="time"
    for _,r in p.iterrows():
        hi=float(r["high_CE"]+r["high_PE"])
        lo=float(r["low_CE"]+r["low_PE"])
        close=float(r["close_CE"]+r["close_PE"])
        if hi>=stop:
            xt=r.name; exit_value=stop; reason="stop"; break
        if lo<=target:
            xt=r.name; exit_value=target; reason="target"; break
        xt=r.name; exit_value=close
    return xt,exit_value,reason


def net_pnl(entry, exit_value, lot, cm):
    gross=(entry-exit_value)*lot
    turnover=(entry+exit_value)*lot
    brokerage=4*cm.brokerage_per_order
    exchange=turnover*cm.exchange_rate
    sebi=turnover*cm.sebi_rate
    stt=entry*lot*cm.stt_sell_rate
    stamp=exit_value*lot*cm.stamp_buy_rate
    gst=cm.gst_rate*(brokerage+exchange+sebi)
    slippage=4*0.20*lot
    return gross-(brokerage+exchange+sebi+stt+stamp+gst+slippage)


def run(path, out):
    df=load_year(path)
    dates=df.select(pl.col("date").unique().sort()).to_series().to_list()
    observations=[]
    for day in dates:
        day_df=df.filter(pl.col("date")==day)
        for entry in ("09:30:00","09:45:00","10:00:00"):
            obs=prepare_day(day_df,day,entry)
            if obs is not None:
                observations.append(obs)

    cm=OptionCostModel()
    configs=[Core(e,s,t,h,v) for e in ("09:30:00","09:45:00","10:00:00") for s in (1.4,1.6,1.8,2.0) for t in (0.25,0.35,0.45) for h in (60,120,180) for v in (None,0.0,0.02,0.04)]
    rows=[]
    for cfg in configs:
        daily={}
        trades=0
        for o in observations:
            if o["entry"]!=cfg.entry:
                continue
            if cfg.vrp_min is not None and (not np.isfinite(o["vrp"]) or o["vrp"]<cfg.vrp_min):
                continue
            _,exit_value,reason=simulate(o,cfg.stop,cfg.target_decay,cfg.hold)
            if exit_value is None:
                continue
            pnl=net_pnl(o["entry_premium"],exit_value,o["lot"],cm)
            daily[o["date"]]=daily.get(o["date"],0)+pnl
            trades+=1
        if trades < max(80,int(len(dates)*0.5)):
            continue
        d=pd.Series(0.0,index=pd.Index(dates))
        for k,v in daily.items(): d.loc[k]=v
        eq=d.cumsum(); dd=eq-eq.cummax()
        wins=d[d>0].sum(); losses=-d[d<0].sum()
        rows.append({
            "entry":cfg.entry,"stop":cfg.stop,"target_decay":cfg.target_decay,"hold":cfg.hold,"vrp_min":cfg.vrp_min,
            "trades":trades,"coverage":trades/len(dates),"mean_day_net":float(d.mean()),
            "median_day_net":float(d.median()),"p10_day_net":float(d.quantile(0.10)),
            "positive_day_rate":float((d>0).mean()),"max_drawdown":float(dd.min()),
            "profit_factor":float(wins/losses) if losses else 999.0
        })

    board=pd.DataFrame(rows).sort_values(["mean_day_net","positive_day_rate","max_drawdown"],ascending=[False,False,False]) if rows else pd.DataFrame()
    out.mkdir(parents=True,exist_ok=True)
    board.head(200).to_csv(out/"fullchain_straddle_leaderboard.csv",index=False)
    summary={
        "dataset":str(path),"calendar_days":len(dates),"entry_observations":len(observations),
        "variants_tested":len(configs),"target_daily_net_inr":1000.0,
        "target_qualified_count":int((board["mean_day_net"]>=1000).sum()) if not board.empty else 0,
        "best":board.iloc[0].to_dict() if not board.empty else None
    }
    (out/"fullchain_straddle_summary.json").write_text(json.dumps(summary,indent=2,default=str))
    print(json.dumps(summary,indent=2,default=str))


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--data",type=Path,required=True)
    ap.add_argument("--out",type=Path,default=Path("reports"))
    args=ap.parse_args()
    run(args.data,args.out)
