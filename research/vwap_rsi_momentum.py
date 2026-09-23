from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from research.contracts import nifty_lot_size
from research.cost_model import OptionCostModel


@dataclass(frozen=True)
class Config:
    entry_minute: int
    required_conditions: int
    rsi_long: float
    rsi_short: float
    volume_ratio: float
    stop: float
    target: float
    hold: int
    trailing: bool


def add_features(day: pd.DataFrame) -> pd.DataFrame:
    x=day.sort_values("timestamp").copy()
    typical=(x.high+x.low+x.close)/3
    cumv=x.volume.clip(lower=0).cumsum().replace(0,np.nan)
    x["vwap"]=(typical*x.volume.clip(lower=0)).cumsum()/cumv
    x["ema20"]=x.close.ewm(span=20,adjust=False).mean()
    x["ema50"]=x.close.ewm(span=50,adjust=False).mean()
    d=x.close.diff()
    up=d.clip(lower=0).ewm(alpha=1/14,adjust=False).mean()
    dn=-d.clip(upper=0).ewm(alpha=1/14,adjust=False).mean()
    rs=up.div(dn)
    x["rsi"]=(100-100/(1+rs)).where(dn!=0,np.where(up>0,100.0,50.0))
    x["vol_ratio"]=x.volume/x.volume.rolling(20,min_periods=10).mean().replace(0,np.nan)
    tr=pd.concat([
        x.high-x.low,
        (x.high-x.close.shift()).abs(),
        (x.low-x.close.shift()).abs()
    ],axis=1).max(axis=1)
    x["atr_pct"]=tr.rolling(14).mean()/x.close
    x["atr_pctile"]=x.atr_pct.rolling(60,min_periods=20).rank(pct=True)
    return x


def first_signal(x: pd.DataFrame,cfg:Config,d):
    start=pd.Timestamp(d)+pd.Timedelta(minutes=cfg.entry_minute)
    end=start+pd.Timedelta(minutes=45)
    z=x[(x.timestamp>=start)&(x.timestamp<=end)].copy()
    z=z.replace([np.inf,-np.inf],np.nan).dropna(subset=["close","vwap","ema20","ema50","rsi","vol_ratio"])
    if z.empty:return None
    for _,r in z.iterrows():
        long_conds=[
            r.close>r.vwap,
            r.rsi>cfg.rsi_long,
            r.ema20>r.ema50,
            r.vol_ratio>=cfg.volume_ratio,
        ]
        short_conds=[
            r.close<r.vwap,
            r.rsi<cfg.rsi_short,
            r.ema20<r.ema50,
            r.vol_ratio>=cfg.volume_ratio,
        ]
        if sum(long_conds)>=cfg.required_conditions:
            return r.timestamp,"CE"
        if sum(short_conds)>=cfg.required_conditions:
            return r.timestamp,"PE"
    return None


def run(data,out):
    spot=pd.read_excel(data,sheet_name="Spot_1min")
    opt=pd.read_excel(data,sheet_name="ATM_Options_1min")
    spot["timestamp"]=pd.to_datetime(spot["Date"].astype(str)+" "+spot["Time"].astype(str))
    opt["timestamp"]=pd.to_datetime(opt["Timestamp"],utc=True).dt.tz_convert("Asia/Kolkata").dt.tz_localize(None)
    spot=spot.rename(columns={"Open":"open","High":"high","Low":"low","Close":"close","Volume":"volume"}).dropna(subset=["timestamp","close"])
    opt=opt.rename(columns={"Open":"open","High":"high","Low":"low","Close":"close","Volume":"volume","Type":"option_type","Strike":"strike"}).dropna(subset=["timestamp","close","strike"])
    opt["option_type"]=opt.option_type.astype(str).str.upper().replace({"CALL":"CE","PUT":"PE","C":"CE","P":"PE"})
    for c in ["open","high","low","close","volume","strike"]: opt[c]=pd.to_numeric(opt[c],errors="coerce")

    spot_days={d:ds for d,ds in spot.groupby(spot.timestamp.dt.date)}
    opt_days={d:do for d,do in opt.groupby(opt.timestamp.dt.date)}
    cm=OptionCostModel()

    configs=[]
    for entry in (9*60+30,9*60+45,10*60,10*60+15):
        for req in (3,4):
            for rsi_long,rsi_short in ((55,45),(60,40)):
                for vol_ratio in (1.0,1.2,1.5):
                    for stop in (0.15,0.20,0.25):
                        for target in (0.30,0.40,0.50):
                            for hold in (30,60,90):
                                configs.append(Config(entry,req,rsi_long,rsi_short,vol_ratio,stop,target,hold,False))

    results=[]
    for cfg in configs:
        daily={}
        trade_records=[]
        for d,ds in spot_days.items():
            do=opt_days.get(d)
            if do is None:continue
            x=add_features(ds)
            sig=first_signal(x,cfg,d)
            if sig is None:continue
            st,typ=sig
            srow=ds[ds.timestamp>=st].head(1)
            if srow.empty:continue
            spot_px=float(srow.iloc[0].close)
            q=do[(do.option_type==typ)&(do.timestamp>=st+pd.Timedelta(minutes=1))&(do.timestamp<=st+pd.Timedelta(minutes=4))&(do.close>0)]
            if q.empty:continue
            strike=float(min(q.strike.dropna().unique(),key=lambda s:abs(s-spot_px)))
            q=q[q.strike==strike].sort_values("timestamp")
            if q.empty:continue
            entry_px=float(q.close.iloc[0]); et=q.timestamp.iloc[0]
            path=do[(do.option_type==typ)&(do.strike==strike)&(do.timestamp>et)&(do.timestamp<=et+pd.Timedelta(minutes=cfg.hold))].sort_values("timestamp")
            if path.empty:continue
            stop_px=entry_px*(1-cfg.stop); target_px=entry_px*(1+cfg.target)
            exit_px=None; xt=None; reason="time"
            peak=entry_px
            for _,r in path.iterrows():
                peak=max(peak,float(r.high))
                if float(r.low)<=stop_px:
                    exit_px=stop_px; xt=r.timestamp; reason="stop"; break
                if float(r.high)>=target_px:
                    exit_px=target_px; xt=r.timestamp; reason="target"; break
                if cfg.trailing and peak>entry_px*1.2:
                    stop_px=max(stop_px,peak*0.8)
            if exit_px is None:
                rr=path.iloc[-1]; exit_px=float(rr.close); xt=rr.timestamp
            lot=nifty_lot_size(d)
            net=cm.net_pnl(entry_px,exit_px,1,lot)
            daily[d]=daily.get(d,0)+net
            trade_records.append((d,net))
        if len(trade_records)<max(60,int(0.45*len(spot_days))):
            continue
        daily_series=pd.Series(0.0,index=sorted(spot_days.keys()))
        for d,v in daily.items():daily_series.loc[d]=v
        eq=daily_series.cumsum(); dd=eq-eq.cummax()
        wins=daily_series[daily_series>0].sum(); losses=-daily_series[daily_series<0].sum()
        results.append({
            "entry_minute":cfg.entry_minute,"required_conditions":cfg.required_conditions,
            "rsi_long":cfg.rsi_long,"rsi_short":cfg.rsi_short,"volume_ratio":cfg.volume_ratio,
            "stop":cfg.stop,"target":cfg.target,"hold":cfg.hold,
            "trades":len(trade_records),"mean_day_net":float(daily_series.mean()),
            "median_day_net":float(daily_series.median()),"p10_day_net":float(daily_series.quantile(.10)),
            "positive_day_rate":float((daily_series>0).mean()),"win_rate_trade":float(np.mean([n>0 for _,n in trade_records])),
            "profit_factor":float(wins/losses) if losses else 999.0,
            "max_drawdown":float(dd.min())
        })
    board=pd.DataFrame(results)
    if not board.empty:
        board=board.sort_values(["mean_day_net","positive_day_rate","profit_factor"],ascending=[False,False,False])
    out.mkdir(parents=True,exist_ok=True)
    board.head(300).to_csv(out/"vwap_rsi_momentum_leaderboard.csv",index=False)
    qualified=board[board.mean_day_net>=1000] if not board.empty else pd.DataFrame()
    summary={
        "calendar_days":len(spot_days),"variants_tested":len(configs),
        "target_daily_net_inr":1000.0,"target_qualified_count":int(len(qualified)),
        "best":board.iloc[0].to_dict() if not board.empty else None
    }
    (out/"vwap_rsi_momentum_summary.json").write_text(json.dumps(summary,indent=2,default=str))
    print(json.dumps(summary,indent=2,default=str))


if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--data",type=Path,required=True);ap.add_argument("--out",type=Path,default=Path("reports"));a=ap.parse_args();run(a.data,a.out)
