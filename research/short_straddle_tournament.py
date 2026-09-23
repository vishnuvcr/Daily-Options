from __future__ import annotations
import argparse,json,math
from pathlib import Path
import numpy as np
import pandas as pd
from research.cost_model import OptionCostModel
from research.contracts import nifty_lot_size

LOT=65

def load(path):
    spot=pd.read_excel(path,sheet_name="Spot_1min")
    opt=pd.read_excel(path,sheet_name="ATM_Options_1min")
    spot["timestamp"]=pd.to_datetime(spot["Date"].astype(str)+" "+spot["Time"].astype(str))
    opt["timestamp"]=pd.to_datetime(opt["Timestamp"],utc=True).dt.tz_convert("Asia/Kolkata").dt.tz_localize(None)
    spot=spot.rename(columns={"Open":"open","High":"high","Low":"low","Close":"close","Volume":"volume"})
    opt=opt.rename(columns={"Open":"open","High":"high","Low":"low","Close":"close","Volume":"volume","Type":"option_type","Strike":"strike","Expiry":"expiry"})
    opt["option_type"]=opt.option_type.astype(str).str.upper().replace({"CALL":"CE","PUT":"PE"})
    for c in ["open","high","low","close","volume","strike"]: opt[c]=pd.to_numeric(opt[c],errors="coerce")
    return spot.dropna(subset=["timestamp","close"]),opt.dropna(subset=["timestamp","close","strike"])

def entry_pair(do,start):
    q=do[(do.timestamp>=start)&(do.timestamp<=start+pd.Timedelta(minutes=5))&(do.close>0)].copy()
    if q.empty:return None
    strikes=sorted(q.strike.dropna().unique())
    if not strikes:return None
    # Prefer the strike nearest the underlying spot proxy recorded in the option chain.
    strike=strikes[len(strikes)//2]
    ce=q[(q.option_type=="CE")&(q.strike==strike)].sort_values("timestamp")
    pe=q[(q.option_type=="PE")&(q.strike==strike)].sort_values("timestamp")
    if ce.empty or pe.empty:return None
    # Use the first timestamp at which both legs have a price.
    common=sorted(set(ce.timestamp)&set(pe.timestamp))
    if not common:return None
    t=common[0]
    return t,float(ce.loc[ce.timestamp==t,"close"].iloc[0]),float(pe.loc[pe.timestamp==t,"close"].iloc[0]),float(strike)

def run(data,out):
    spot,opt=load(data); out.mkdir(parents=True,exist_ok=True); cm=OptionCostModel()
    days={d:ds for d,ds in spot.groupby(spot.timestamp.dt.date)}
    odays={d:do for d,do in opt.groupby(opt.timestamp.dt.date)}
    rows=[]
    for stop_mult,target_decay,hold in ((1.50,0.30,60),(1.75,0.40,120),(2.00,0.50,180)):
        trades=[]
        for d,ds in days.items():
            do=odays.get(d)
            if do is None:continue
            start=pd.Timestamp(d)+pd.Timedelta(hours=9,minutes=30)
            pair=entry_pair(do,start)
            if not pair:continue
            et,ce0,pe0,strike=pair; entry=ce0+pe0
            stop=entry*stop_mult; target=entry*(1-target_decay)
            path=do[(do.timestamp>et)&(do.timestamp<=et+pd.Timedelta(minutes=hold))&(do.strike==strike)]
            piv=path.pivot_table(index="timestamp",columns="option_type",values=["high","low","close"],aggfunc="last")
            piv=piv.dropna(subset=[("close","CE"),("close","PE")])
            if piv.empty:continue
            xt=et; exit_strad=entry; reason="time"
            for t,r in piv.iterrows():
                hi=float(r[("high","CE")]+r[("high","PE")])
                lo=float(r[("low","CE")]+r[("low","PE")])
                close=float(r[("close","CE")]+r[("close","PE")])
                if hi>=stop:
                    xt=t; exit_strad=stop; reason="stop"; break
                if lo<=target:
                    xt=t; exit_strad=target; reason="target"; break
                xt=t; exit_strad=close
            er=piv.loc[xt] if xt in piv.index else None
            if er is None:continue
            ce_exit=float(er[("close","CE")]); pe_exit=float(er[("close","PE")])
            net=cm.short_straddle_net_pnl(ce0,pe0,ce_exit,pe_exit,nifty_lot_size(d))
            trades.append({"date":str(d),"entry_time":et.isoformat(),"exit_time":xt.isoformat(),"strike":strike,"entry_straddle":entry,"exit_straddle":exit_strad,"net_pnl":net,"reason":reason})
        if trades:
            df=pd.DataFrame(trades); daily=df.groupby("date").net_pnl.sum(); wins=df.loc[df.net_pnl>0,"net_pnl"].sum(); losses=-df.loc[df.net_pnl<0,"net_pnl"].sum()
            rows.append({"stop_mult":stop_mult,"target_decay":target_decay,"hold_min":hold,"trades":len(df),"win_rate":float((df.net_pnl>0).mean()),"mean_active_day":float(daily.mean()),"mean_all_day":float(df.net_pnl.sum()/len(days)),"profit_factor":float(wins/losses) if losses else 999.0,"total_net":float(df.net_pnl.sum())})
    board=pd.DataFrame(rows).sort_values("mean_all_day",ascending=False) if rows else pd.DataFrame()
    board.to_csv(out/"short_straddle_leaderboard.csv",index=False)
    result={"dataset":str(data),"trading_days":len(days),"variants_tested":3,"lot_size":"date-aware","target_inr_per_day":1000.0,"top":board.iloc[0].to_dict() if len(board) else None,"gate":"PASS_PRELIMINARY" if len(board) and board.iloc[0].mean_all_day>=1000 else "FAIL_PRELIMINARY"}
    (out/"short_straddle_summary.json").write_text(json.dumps(result,indent=2,default=str))
    print(json.dumps(result,indent=2,default=str))

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--data",type=Path,required=True); ap.add_argument("--out",type=Path,default=Path("reports")); a=ap.parse_args(); run(a.data,a.out)
