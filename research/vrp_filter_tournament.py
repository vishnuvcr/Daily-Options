from __future__ import annotations
import argparse, json, math
from pathlib import Path
import numpy as np
import pandas as pd
from research.cost_model import OptionCostModel

LOT=65
RISK_FREE=0.06
MINUTES_PER_YEAR=252*375

def norm_cdf(x):
    return 0.5*(1.0+math.erf(x/math.sqrt(2.0)))

def bs_call(S,K,T,r,sigma):
    if T<=0: return max(S-K,0.0)
    if sigma<=0: return max(S-K*math.exp(-r*T),0.0)
    d1=(math.log(S/K)+(r+0.5*sigma*sigma)*T)/(sigma*math.sqrt(T))
    d2=d1-sigma*math.sqrt(T)
    return S*norm_cdf(d1)-K*math.exp(-r*T)*norm_cdf(d2)

def bs_put(S,K,T,r,sigma):
    return bs_call(S,K,T,r,sigma)-S+K*math.exp(-r*T)

def implied_straddle_vol(S,K,T,r,price):
    intrinsic=max(S-K,0.0)+max(K-S,0.0)
    if not np.isfinite(price) or price<=intrinsic: return np.nan
    lo,hi=1e-4,5.0
    for _ in range(80):
        mid=(lo+hi)/2
        model=bs_call(S,K,T,r,mid)+bs_put(S,K,T,r,mid)
        if model>price: hi=mid
        else: lo=mid
    return (lo+hi)/2

def load(path):
    spot=pd.read_excel(path,sheet_name="Spot_1min")
    opt=pd.read_excel(path,sheet_name="ATM_Options_1min")
    spot["timestamp"]=pd.to_datetime(spot["Date"].astype(str)+" "+spot["Time"].astype(str))
    opt["timestamp"]=pd.to_datetime(opt["Timestamp"],utc=True).dt.tz_convert("Asia/Kolkata").dt.tz_localize(None)
    spot=spot.rename(columns={"Open":"open","High":"high","Low":"low","Close":"close","Volume":"volume"})
    opt=opt.rename(columns={"Open":"open","High":"high","Low":"low","Close":"close","Volume":"volume","Type":"option_type","Strike":"strike","Expiry":"expiry"})
    opt["option_type"]=opt.option_type.astype(str).str.upper().replace({"CALL":"CE","PUT":"PE"})
    opt["expiry"]=pd.to_datetime(opt["expiry"],errors="coerce")
    for c in ["open","high","low","close","volume","strike"]: opt[c]=pd.to_numeric(opt[c],errors="coerce")
    return spot.dropna(subset=["timestamp","close"]),opt.dropna(subset=["timestamp","close","strike","expiry"])

def signal(day):
    x=day.sort_values("timestamp").copy()
    d=x.timestamp.dt.normalize().iloc[0]
    start=d+pd.Timedelta(hours=9,minutes=15)
    end=start+pd.Timedelta(minutes=15)
    x["ema8"]=x.close.ewm(span=8,adjust=False).mean()
    x["ema24"]=x.close.ewm(span=24,adjust=False).mean()
    x=x[(x.timestamp>=end+pd.Timedelta(minutes=1))&(x.timestamp<=d+pd.Timedelta(hours=14,minutes=45))].copy()
    up=x[(x.ema8>x.ema24)&(x.close>x.ema8)]
    dn=x[(x.ema8<x.ema24)&(x.close<x.ema8)]
    if up.empty and dn.empty:return None
    if dn.empty or (not up.empty and up.iloc[0].timestamp<dn.iloc[0].timestamp):return up.iloc[0].timestamp,"CE"
    return dn.iloc[0].timestamp,"PE"

def vrp_at_signal(ds,do,t):
    srow=ds[ds.timestamp<=t].tail(1)
    if srow.empty:return None
    S=float(srow.iloc[0].close)
    hist=ds[(ds.timestamp<t)&(ds.timestamp>=t-pd.Timedelta(minutes=30))].close
    if len(hist)<15:return None
    rv=float(hist.pct_change().dropna().std()*math.sqrt(MINUTES_PER_YEAR))
    q=do[(do.timestamp==t)&(do.close>0)]
    if q.empty:q=do[(do.timestamp>t)&(do.timestamp<=t+pd.Timedelta(minutes=1))&(do.close>0)].sort_values("timestamp")
    if q.empty:return None
    strike=float(q.strike.iloc[0])
    row={}
    for typ in ("CE","PE"):
        z=q[q.option_type==typ]
        if z.empty:
            z=do[(do.timestamp==q.timestamp.iloc[0])&(do.option_type==typ)&(do.strike==strike)]
        if z.empty:return None
        row[typ]=float(z.close.iloc[0]); expiry=pd.Timestamp(z.iloc[0].expiry)
    T=max((expiry.to_pydatetime()-t.to_pydatetime()).total_seconds()/31557600.0,1/3650)
    iv=implied_straddle_vol(S,strike,T,RISK_FREE,row["CE"]+row["PE"])
    return {"iv":iv,"rv":rv,"vrp":iv-rv,"strike":strike}

def simulate(option_path,entry,stop=0.25,target=0.50,hold=60):
    path=option_path.sort_values("timestamp")
    st=entry*(1-stop); tg=entry*(1+target)
    exit_px=None; reason="time"; xt=None
    for _,r in path.iterrows():
        ls=float(r.low)<=st; lt=float(r.high)>=tg
        if ls and lt: exit_px=st; reason="stop_first"; xt=r.timestamp; break
        if ls: exit_px=st; reason="stop"; xt=r.timestamp; break
        if lt: exit_px=tg; reason="target"; xt=r.timestamp; break
        exit_px=float(r.close); xt=r.timestamp
    return (xt,float(exit_px),reason) if exit_px is not None else (None,None,"no_forward_bar")

def main(data,out):
    spot,opt=load(data); out.mkdir(parents=True,exist_ok=True); cm=OptionCostModel()
    days={d:ds for d,ds in spot.groupby(spot.timestamp.dt.date)}
    odays={d:do for d,do in opt.groupby(opt.timestamp.dt.date)}
    rows=[]
    for threshold in (0.00,0.02,0.04,0.06,0.08):
        trades=[]
        for d,ds in days.items():
            do=odays.get(d)
            if do is None:continue
            sig=signal(ds)
            if not sig:continue
            st,typ=sig
            vrp=vrp_at_signal(ds,do,st)
            if not vrp or not np.isfinite(vrp["vrp"]) or vrp["vrp"]<threshold:continue
            q=do[(do.option_type==typ)&(do.timestamp>=st+pd.Timedelta(minutes=1))&(do.timestamp<=st+pd.Timedelta(minutes=5))&(do.strike==vrp["strike"])&(do.close>0)].sort_values("timestamp")
            if q.empty:continue
            entry=float(q.close.iloc[0]); et=q.timestamp.iloc[0]
            path=do[(do.option_type==typ)&(do.strike==vrp["strike"])&(do.timestamp>et)&(do.timestamp<=et+pd.Timedelta(minutes=60))]
            xt,exit_px,reason=simulate(path,entry)
            if xt is None:continue
            net=cm.net_pnl(entry,exit_px,1,LOT)
            trades.append({"date":str(d),"entry_time":et.isoformat(),"exit_time":xt.isoformat(),"vrp":float(vrp["vrp"]),"iv":float(vrp["iv"]),"rv":float(vrp["rv"]),"type":typ,"strike":float(vrp["strike"]),"entry":entry,"exit":exit_px,"net_pnl":net,"reason":reason})
        if trades:
            df=pd.DataFrame(trades); daily=df.groupby("date").net_pnl.sum(); wins=df.loc[df.net_pnl>0,"net_pnl"].sum(); losses=-df.loc[df.net_pnl<0,"net_pnl"].sum()
            rows.append({"vrp_threshold":threshold,"trades":len(df),"win_rate":float((df.net_pnl>0).mean()),"mean_active_day":float(daily.mean()),"mean_all_day":float(df.net_pnl.sum()/len(days)),"profit_factor":float(wins/losses) if losses else 999.0,"total_net":float(df.net_pnl.sum())})
    board=pd.DataFrame(rows).sort_values("mean_all_day",ascending=False) if rows else pd.DataFrame()
    board.to_csv(out/"vrp_filter_leaderboard.csv",index=False)
    result={"dataset":str(data),"trading_days":len(days),"variants_tested":5,"lot_size":LOT,"target_inr_per_day":1000.0,"top":board.iloc[0].to_dict() if len(board) else None,"gate":"PASS_PRELIMINARY" if len(board) and board.iloc[0].mean_all_day>=1000 else "FAIL_PRELIMINARY"}
    (out/"vrp_filter_summary.json").write_text(json.dumps(result,indent=2,default=str))
    print(json.dumps(result,indent=2,default=str))

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--data",type=Path,required=True); ap.add_argument("--out",type=Path,default=Path("reports")); a=ap.parse_args(); main(a.data,a.out)
