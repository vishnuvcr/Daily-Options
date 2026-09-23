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


def build_bases(spot,opt,configs):
    cm=OptionCostModel()
    spot_days={d:ds for d,ds in spot.groupby(spot.timestamp.dt.date)}
    opt_days={d:do for d,do in opt.groupby(opt.timestamp.dt.date)}
    signal_keys=sorted({
        (cfg.entry_minute,cfg.required_conditions,cfg.rsi_long,cfg.rsi_short,cfg.volume_ratio)
        for cfg in configs
    })
    risk_keys=sorted({(cfg.stop,cfg.target,cfg.hold) for cfg in configs})
    bases=[]
    for d,ds in spot_days.items():
        x=add_features(ds)
        do=opt_days.get(d)
        if do is None:
            continue
        for entry,req,rsi_long,rsi_short,vol_ratio in signal_keys:
            start=pd.Timestamp(d)+pd.Timedelta(minutes=entry)
            end=start+pd.Timedelta(minutes=45)
            z=x[(x.timestamp>=start)&(x.timestamp<=end)].copy()
            z=z.replace([np.inf,-np.inf],np.nan).dropna(subset=["close","vwap","ema20","ema50","rsi","vol_ratio"])
            sig=None
            for _,r in z.iterrows():
                long_sum=sum([r.close>r.vwap,r.rsi>rsi_long,r.ema20>r.ema50,r.vol_ratio>=vol_ratio])
                short_sum=sum([r.close<r.vwap,r.rsi<rsi_short,r.ema20<r.ema50,r.vol_ratio>=vol_ratio])
                if long_sum>=req:
                    sig=(r.timestamp,"CE"); break
                if short_sum>=req:
                    sig=(r.timestamp,"PE"); break
            if sig is None:
                continue
            st,typ=sig
            srow=ds[ds.timestamp>=st].head(1)
            if srow.empty: continue
            spot_px=float(srow.iloc[0].close)
            q=do[(do.option_type==typ)&(do.timestamp>=st+pd.Timedelta(minutes=1))&(do.timestamp<=st+pd.Timedelta(minutes=4))&(do.close>0)]
            if q.empty: continue
            strike=float(min(q.strike.dropna().unique(),key=lambda s:abs(s-spot_px)))
            q=q[q.strike==strike].sort_values("timestamp")
            if q.empty: continue
            entry_px=float(q.close.iloc[0]); et=q.timestamp.iloc[0]
            path=do[(do.option_type==typ)&(do.strike==strike)&(do.timestamp>et)&(do.timestamp<=et+pd.Timedelta(minutes=90))].sort_values("timestamp")
            if path.empty: continue
            bases.append({
                "date":d,"entry_minute":entry,"required_conditions":req,
                "rsi_long":rsi_long,"rsi_short":rsi_short,"volume_ratio":vol_ratio,
                "entry":entry_px,"entry_time":et,"option_type":typ,"strike":strike,
                "lot":nifty_lot_size(d),"path":path,
            })
    return bases,len(spot_days)


def precompute_outcomes(bases,configs,cm):
    risk_keys=sorted({(cfg.stop,cfg.target,cfg.hold) for cfg in configs})
    out={}
    for i,b in enumerate(bases):
        path=b["path"]
        for stop,target,hold in risk_keys:
            p=path[path.timestamp<=b["entry_time"]+pd.Timedelta(minutes=hold)]
            if p.empty: continue
            stop_px=b["entry"]*(1-stop); target_px=b["entry"]*(1+target)
            exit_px=None
            for _,r in p.iterrows():
                hit_s=float(r.low)<=stop_px
                hit_t=float(r.high)>=target_px
                if hit_s and hit_t:
                    exit_px=stop_px; break
                if hit_s:
                    exit_px=stop_px; break
                if hit_t:
                    exit_px=target_px; break
            if exit_px is None:
                exit_px=float(p.iloc[-1].close)
            out[(i,stop,target,hold)]=float(cm.net_pnl(b["entry"],exit_px,1,b["lot"]))
    return out


def evaluate_bases(bases,all_days,configs,outcomes):
    results=[]
    for cfg in configs:
        daily={}
        trade_wins=trade_count=0
        for i,b in enumerate(bases):
            if (b["entry_minute"],b["required_conditions"],b["rsi_long"],b["rsi_short"],b["volume_ratio"]) != (
                cfg.entry_minute,cfg.required_conditions,cfg.rsi_long,cfg.rsi_short,cfg.volume_ratio
            ):
                continue
            key=(i,cfg.stop,cfg.target,cfg.hold)
            if key not in outcomes: continue
            net=outcomes[key]
            daily[b["date"]]=daily.get(b["date"],0)+net
            trade_count+=1
            trade_wins += int(net>0)
        if trade_count < max(60,int(0.45*all_days)): continue
        d=pd.Series(0.0,index=sorted({b["date"] for b in bases}))
        for day,val in daily.items(): d.loc[day]=val
        eq=d.cumsum(); dd=eq-eq.cummax()
        wins=d[d>0].sum(); losses=-d[d<0].sum()
        results.append({
            "entry_minute":cfg.entry_minute,"required_conditions":cfg.required_conditions,
            "rsi_long":cfg.rsi_long,"rsi_short":cfg.rsi_short,"volume_ratio":cfg.volume_ratio,
            "stop":cfg.stop,"target":cfg.target,"hold":cfg.hold,"trades":trade_count,
            "coverage":trade_count/all_days,"mean_day_net":float(d.mean()),
            "median_day_net":float(d.median()),"p10_day_net":float(d.quantile(.10)),
            "positive_day_rate":float((d>0).mean()),"win_rate_trade":trade_wins/trade_count,
            "profit_factor":float(wins/losses) if losses else 999.0,
            "max_drawdown":float(dd.min())
        })
    board=pd.DataFrame(results)
    if not board.empty:
        board=board.sort_values(["mean_day_net","positive_day_rate","profit_factor"],ascending=[False,False,False])
    return board


def run(data,out):
    spot=pd.read_excel(data,sheet_name="Spot_1min")
    opt=pd.read_excel(data,sheet_name="ATM_Options_1min")
    spot["timestamp"]=pd.to_datetime(spot["Date"].astype(str)+" "+spot["Time"].astype(str))
    opt["timestamp"]=pd.to_datetime(opt["Timestamp"],utc=True).dt.tz_convert("Asia/Kolkata").dt.tz_localize(None)
    spot=spot.rename(columns={"Open":"open","High":"high","Low":"low","Close":"close","Volume":"volume"}).dropna(subset=["timestamp","close"])
    opt=opt.rename(columns={"Open":"open","High":"high","Low":"low","Close":"close","Volume":"volume","Type":"option_type","Strike":"strike"}).dropna(subset=["timestamp","close","strike"])
    opt["option_type"]=opt.option_type.astype(str).str.upper().replace({"CALL":"CE","PUT":"PE","C":"CE","P":"PE"})
    for col in ["open","high","low","close","volume","strike"]: opt[col]=pd.to_numeric(opt[col],errors="coerce")
    configs=[
        Config(entry,req,rl,rs,vr,stop,target,hold,False)
        for entry in (9*60+30,9*60+45,10*60,10*60+15)
        for req in (3,4)
        for rl,rs in ((55,45),(60,40))
        for vr in (1.0,1.2,1.5)
        for stop in (0.15,0.20,0.25)
        for target in (0.30,0.40,0.50)
        for hold in (30,60,90)
    ]
    cm=OptionCostModel()
    bases,all_days=build_bases(spot,opt,configs)
    outcomes=precompute_outcomes(bases,configs,cm)
    board=evaluate_bases(bases,all_days,configs,outcomes)
    out.mkdir(parents=True,exist_ok=True)
    board.head(300).to_csv(out/"vwap_rsi_momentum_leaderboard.csv",index=False)
    qualified=board[board.mean_day_net>=1000] if not board.empty else pd.DataFrame()
    summary={
        "calendar_days":len(spot.timestamp.dt.date.unique()),"trade_bases":len(bases),
        "variants_tested":len(configs),"target_daily_net_inr":1000.0,
        "target_qualified_count":int(len(qualified)),
        "best":board.iloc[0].to_dict() if not board.empty else None
    }
    (out/"vwap_rsi_momentum_summary.json").write_text(json.dumps(summary,indent=2,default=str))
    print(json.dumps(summary,indent=2,default=str))


if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--data",type=Path,required=True);ap.add_argument("--out",type=Path,default=Path("reports"));a=ap.parse_args();run(a.data,a.out)
