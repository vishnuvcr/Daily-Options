"""Baseline intraday option backtest (research only)."""
from pathlib import Path
import argparse, json
import numpy as np
import pandas as pd
from research.cost_model import OptionCostModel

LOT_SIZE=65

def load_data(path: Path):
    spot=pd.read_excel(path,sheet_name="Spot_1min")
    opt=pd.read_excel(path,sheet_name="ATM_Options_1min")
    spot["timestamp"]=pd.to_datetime(spot["Date"].astype(str)+" "+spot["Time"].astype(str),errors="coerce")
    opt["timestamp"]=pd.to_datetime(opt["Timestamp"],errors="coerce",utc=True).dt.tz_convert("Asia/Kolkata").dt.tz_localize(None)
    spot=spot.rename(columns={"Open":"open","High":"high","Low":"low","Close":"close","Volume":"volume"})
    opt=opt.rename(columns={"Open":"open","High":"high","Low":"low","Close":"close","Volume":"volume","OI":"oi","Type":"option_type","Strike":"strike"})
    spot=spot[["timestamp","open","high","low","close","volume"]].dropna().sort_values("timestamp")
    opt=opt[["timestamp","open","high","low","close","volume","option_type","strike"]].dropna(subset=["timestamp","close","option_type","strike"]).sort_values("timestamp")
    opt["option_type"]=opt["option_type"].astype(str).str.upper().replace({"CALL":"CE","PUT":"PE"})
    for c in ["open","high","low","close","volume","strike"]:
        opt[c]=pd.to_numeric(opt[c],errors="coerce")
    return spot,opt

def add_features(day):
    x=day.sort_values("timestamp").copy()
    x["typical"]=(x.high+x.low+x.close)/3
    x["vwap"]=(x.typical*x.volume.cumsum()*0 + x.typical*x.volume).cumsum()/x.volume.cumsum().replace(0,np.nan)
    x["ema8"]=x.close.ewm(span=8,adjust=False).mean()
    x["ema24"]=x.close.ewm(span=24,adjust=False).mean()
    x["vol_ratio"]=x.volume/x.volume.rolling(20,min_periods=10).mean().replace(0,np.nan)
    return x

def first_signal(day,family,orb_minutes=15,vwap_filter=True,volume_filter=False):
    x=add_features(day)
    d=x.timestamp.dt.normalize().iloc[0]
    start=d+pd.Timedelta(hours=9,minutes=15)
    after=start+pd.Timedelta(minutes=orb_minutes)
    x["orb_high"]=x.loc[(x.timestamp>=start)&(x.timestamp<after),"high"].max()
    x["orb_low"]=x.loc[(x.timestamp>=start)&(x.timestamp<after),"low"].min()
    x=x[(x.timestamp>=after+pd.Timedelta(minutes=1))&(x.timestamp<=d+pd.Timedelta(hours=14,minutes=45))].copy()
    if x.empty:return None
    if family=="orb":
        long=x.close>x.orb_high; short=x.close<x.orb_low
    elif family=="vwap":
        prev=x.close.shift(1); pv=x.vwap.shift(1)
        long=(prev<=pv)&(x.close>x.vwap); short=(prev>=pv)&(x.close<x.vwap)
    elif family=="ema":
        long=(x.ema8>x.ema24)&(x.close>x.ema8); short=(x.ema8<x.ema24)&(x.close<x.ema8)
    else: raise ValueError(family)
    if vwap_filter:
        long &= x.close>x.vwap; short &= x.close<x.vwap
    if volume_filter:
        long &= x.vol_ratio>=1.2; short &= x.vol_ratio>=1.2
    candidates=[(r.timestamp,"CE") for _,r in x[long].iterrows()]+[(r.timestamp,"PE") for _,r in x[short].iterrows()]
    return min(candidates) if candidates else None

def trade_one(day_spot,day_opt,signal,cost_model,stop=0.25,target=0.50,hold=60):
    signal_time,otype=signal
    srow=day_spot[day_spot.timestamp>=signal_time].head(1)
    if srow.empty:return None
    spot_px=float(srow.iloc[0].close)
    q=day_opt[(day_opt.option_type==otype)&(day_opt.timestamp>=signal_time+pd.Timedelta(minutes=1))&(day_opt.timestamp<=signal_time+pd.Timedelta(minutes=5))&(day_opt.close>0)].copy()
    if q.empty:return None
    strike=q.assign(dist=(q.strike-spot_px).abs()).sort_values(["timestamp","dist"]).iloc[0].strike
    path=day_opt[(day_opt.option_type==otype)&(day_opt.strike==strike)&(day_opt.timestamp>q.timestamp.min())&(day_opt.timestamp<=q.timestamp.min()+pd.Timedelta(minutes=hold))].sort_values("timestamp")
    entry=float(q.sort_values("timestamp").iloc[0].close); et=q.sort_values("timestamp").iloc[0].timestamp
    stop_px=entry*(1-stop); target_px=entry*(1+target); exit_px=None; reason="time"; xt=et
    for _,r in path.iterrows():
        ls=float(r.low)<=stop_px; lt=float(r.high)>=target_px
        if ls and lt: exit_px=stop_px; xt=r.timestamp; reason="stop_first"; break
        if ls: exit_px=stop_px; xt=r.timestamp; reason="stop"; break
        if lt: exit_px=target_px; xt=r.timestamp; reason="target"; break
        exit_px=float(r.close); xt=r.timestamp
    if exit_px is None:return None
    net=cost_model.net_pnl(entry,float(exit_px),1,LOT_SIZE)
    return {"date":str(et.date()),"entry_time":et.isoformat(),"exit_time":xt.isoformat(),"option_type":otype,"strike":float(strike),"entry":entry,"exit":float(exit_px),"net_pnl":float(net),"reason":reason}

def run(path:Path,out:Path):
    spot,opt=load_data(path)
    out.mkdir(parents=True,exist_ok=True)
    cm=OptionCostModel()
    configs=[(family,vf,vol) for family in ("orb","vwap","ema") for vf in (False,True) for vol in (False,True)]
    spot_days={d:ds for d,ds in spot.groupby(spot.timestamp.dt.date)}
    opt_days={d:do for d,do in opt.groupby(opt.timestamp.dt.date)}
    days=len(spot_days)
    rows=[]
    for family,vf,vol in configs:
        trades=[]
        for d,ds in spot_days.items():
            do=opt_days.get(d)
            if do is None:
                continue
            sig=first_signal(ds,family,15,vf,vol)
            if sig:
                t=trade_one(ds,do,sig,cm)
                if t: trades.append(t)
        if trades:
            df=pd.DataFrame(trades)
            daily=df.groupby("date").net_pnl.sum()
            wins=df.loc[df.net_pnl>0,"net_pnl"].sum()
            losses=-df.loc[df.net_pnl<0,"net_pnl"].sum()
            rows.append({
                "family":family,"vwap_filter":vf,"volume_filter":vol,
                "trades":len(df),"win_rate":float((df.net_pnl>0).mean()),
                "mean_active_day":float(daily.mean()),
                "mean_all_day":float(df.net_pnl.sum()/days),
                "profit_factor":float(wins/losses) if losses else 999.0,
                "total_net":float(df.net_pnl.sum())
            })
    board=pd.DataFrame(rows)
    if not board.empty:
        board=board.sort_values(["mean_all_day","mean_active_day"],ascending=False)
    board.to_csv(out/"phase2_leaderboard.csv",index=False)
    result={
        "dataset":str(path),"trading_days":days,"variants_tested":len(configs),
        "lot_size":LOT_SIZE,"target_inr_per_day":1000.0,
        "top":board.iloc[0].to_dict() if len(board) else None,
        "gate":"PASS" if len(board) and board.iloc[0].mean_all_day>=1000 else "FAIL"
    }
    (out/"phase2_summary.json").write_text(json.dumps(result,indent=2,default=str),encoding="utf-8")
    print(json.dumps(result,indent=2,default=str))

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--data",type=Path,required=True); ap.add_argument("--out",type=Path,default=Path("reports")); a=ap.parse_args(); run(a.data,a.out)
