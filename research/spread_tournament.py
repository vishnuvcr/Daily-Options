from __future__ import annotations
import argparse,json
from pathlib import Path
import pandas as pd
from research.cost_model import OptionCostModel

LOT=65

def load(path):
    spot=pd.read_excel(path,sheet_name="Spot_1min")
    opt=pd.read_excel(path,sheet_name="ATM_Options_1min")
    spot["timestamp"]=pd.to_datetime(spot["Date"].astype(str)+" "+spot["Time"].astype(str))
    opt["timestamp"]=pd.to_datetime(opt["Timestamp"],utc=True).dt.tz_convert("Asia/Kolkata").dt.tz_localize(None)
    spot=spot.rename(columns={"High":"high","Low":"low","Close":"close","Volume":"volume"})
    opt=opt.rename(columns={"Open":"open","High":"high","Low":"low","Close":"close","Volume":"volume","Type":"option_type","Strike":"strike"})
    opt["option_type"]=opt.option_type.astype(str).str.upper().replace({"CALL":"CE","PUT":"PE"})
    for c in ["open","high","low","close","volume","strike"]: opt[c]=pd.to_numeric(opt[c],errors="coerce")
    return spot.dropna(subset=["timestamp","close"]),opt.dropna(subset=["timestamp","close","strike"])

def signal(day):
    x=day.sort_values("timestamp").copy()
    d=x.timestamp.dt.normalize().iloc[0]
    start=d+pd.Timedelta(hours=9,minutes=15); end=start+pd.Timedelta(minutes=15)
    x["typical"]=(x.high+x.low+x.close)/3
    den=x.volume.cumsum().astype(float).replace(0,float("nan"))
    x["vwap"]=(x.typical*x.volume).cumsum()/den
    x["ema8"]=x.close.ewm(span=8,adjust=False).mean()
    x["ema24"]=x.close.ewm(span=24,adjust=False).mean()
    oh=x.loc[(x.timestamp>=start)&(x.timestamp<end),"high"].max()
    ol=x.loc[(x.timestamp>=start)&(x.timestamp<end),"low"].min()
    x=x[(x.timestamp>=end+pd.Timedelta(minutes=1))&(x.timestamp<=d+pd.Timedelta(hours=14,minutes=45))].copy()
    up=x[(x.close>oh)&(x.close>x.vwap)|(x.ema8>x.ema24)&(x.close>x.ema8)]
    dn=x[(x.close<ol)&(x.close<x.vwap)|(x.ema8<x.ema24)&(x.close<x.ema8)]
    if up.empty and dn.empty:return None
    if dn.empty or (not up.empty and up.iloc[0].timestamp<dn.iloc[0].timestamp): return up.iloc[0].timestamp,"CE"
    return dn.iloc[0].timestamp,"PE"

def spread_trade(ds,do,sig,width_steps,target=0.50,stop=0.25,hold=60,cm=None):
    st,side=sig
    row=ds[ds.timestamp>=st].head(1)
    if row.empty:return None
    spot=float(row.iloc[0].close)
    typ=side
    q=do[(do.option_type==typ)&(do.timestamp>=st+pd.Timedelta(minutes=1))&(do.timestamp<=st+pd.Timedelta(minutes=5))&(do.close>0)].copy()
    if q.empty:return None
    strikes=sorted(q.strike.dropna().unique())
    if len(strikes)<2:return None
    atm=min(strikes,key=lambda s:abs(s-spot))
    if typ=="CE":
        candidates=[s for s in strikes if s>atm]; candidates.sort()
    else:
        candidates=[s for s in strikes if s<atm]; candidates.sort(reverse=True)
    if len(candidates)<width_steps:return None
    short_strike=candidates[width_steps-1]
    both=do[(do.option_type==typ)&(do.strike.isin([atm,short_strike]))&(do.timestamp>=st+pd.Timedelta(minutes=1))&(do.timestamp<=st+pd.Timedelta(minutes=5))].copy()
    piv=both.pivot_table(index="timestamp",columns="strike",values=["open","high","low","close"],aggfunc="last")
    if atm not in piv["close"].columns or short_strike not in piv["close"].columns:return None
    piv=piv.dropna(subset=[("close",atm),("close",short_strike)])
    if piv.empty:return None
    et=piv.index[0]
    le=float(piv.loc[et,("close",atm)]); se=float(piv.loc[et,("close",short_strike)])
    entry=le-se
    if entry<=0:return None
    stop_px=entry*(1-stop); target_px=entry*(1+target)
    path=do[(do.option_type==typ)&(do.strike.isin([atm,short_strike]))&(do.timestamp>et)&(do.timestamp<=et+pd.Timedelta(minutes=hold))]
    p=path.pivot_table(index="timestamp",columns="strike",values=["high","low","close"],aggfunc="last").dropna(subset=[("close",atm),("close",short_strike)])
    exit_time=et; exit_val=float(p.loc[et,("close",atm)]-p.loc[et,("close",short_strike)]) if et in p.index else entry; reason="time"
    for t,r in p.iterrows():
        spr_hi=float(r[("high",atm)]-r[("low",short_strike)])
        spr_lo=float(r[("low",atm)]-r[("high",short_strike)])
        if spr_lo<=stop_px:
            exit_time=t; exit_val=stop_px; reason="stop"; break
        if spr_hi>=target_px:
            exit_time=t; exit_val=target_px; reason="target"; break
        exit_time=t; exit_val=float(r[("close",atm)]-r[("close",short_strike)])
    if cm is None: cm=OptionCostModel()
    le2=float(p.loc[exit_time,("close",atm)]) if exit_time in p.index else exit_val
    se2=float(p.loc[exit_time,("close",short_strike)]) if exit_time in p.index else 0.0
    net=cm.vertical_debit_spread_net_pnl(le,se,le2,se2,LOT)
    return {"date":str(et.date()),"entry_time":et.isoformat(),"exit_time":exit_time.isoformat(),"type":typ,"atm":float(atm),"short":float(short_strike),"entry_spread":entry,"exit_spread":float(exit_val),"net_pnl":float(net),"reason":reason}

def main(data,out):
    spot,opt=load(data); out.mkdir(parents=True,exist_ok=True); cm=OptionCostModel()
    days={d:ds for d,ds in spot.groupby(spot.timestamp.dt.date)}
    odays={d:do for d,do in opt.groupby(opt.timestamp.dt.date)}
    rows=[]; alltrades=[]
    for width in (1,2):
        trades=[]
        for d,ds in days.items():
            do=odays.get(d)
            if do is None:continue
            sig=signal(ds)
            if not sig:continue
            t=spread_trade(ds,do,sig,width,cm=cm)
            if t: trades.append(t)
        if trades:
            df=pd.DataFrame(trades); alltrades.append(df)
            wins=df.loc[df.net_pnl>0,"net_pnl"].sum(); losses=-df.loc[df.net_pnl<0,"net_pnl"].sum()
            rows.append({"width_steps":width,"trades":len(df),"win_rate":float((df.net_pnl>0).mean()),"mean_active_day":float(df.groupby("date").net_pnl.sum().mean()),"mean_all_day":float(df.net_pnl.sum()/len(days)),"profit_factor":float(wins/losses) if losses else 999.0,"total_net":float(df.net_pnl.sum())})
    board=pd.DataFrame(rows).sort_values("mean_all_day",ascending=False) if rows else pd.DataFrame()
    board.to_csv(out/"phase3_spread_leaderboard.csv",index=False)
    if alltrades: pd.concat(alltrades,ignore_index=True).to_csv(out/"phase3_spread_trades.csv",index=False)
    result={"dataset":str(data),"trading_days":len(days),"chain_days_testable":int(sum(len(odays[d].strike.unique())>=3 for d in days if d in odays)),"variants_tested":2,"lot_size":LOT,"target_inr_per_day":1000.0,"top":board.iloc[0].to_dict() if len(board) else None,"gate":"PASS" if len(board) and board.iloc[0].mean_all_day>=1000 else "FAIL_PRELIMINARY"}
    (out/"phase3_summary.json").write_text(json.dumps(result,indent=2,default=str))
    print(json.dumps(result,indent=2,default=str))

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--data",type=Path,required=True); ap.add_argument("--out",type=Path,default=Path("reports")); a=ap.parse_args(); main(a.data,a.out)
