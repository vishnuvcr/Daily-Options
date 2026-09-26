#!/usr/bin/env python3
from pathlib import Path
from datetime import date
import argparse, math, json
import duckdb, pandas as pd

START=date(2021,7,1); END=date(2026,8,31)
THRESHOLDS=(2.0,4.0,6.0); WINGS=(200,); EXPIRY_BUCKETS=(0,1)

def lot_size(expiry):
    d=pd.Timestamp(expiry).date()
    if d<date(2024,4,26): return 50
    if d<date(2024,11,21): return 25
    if d<date(2026,1,6): return 75
    return 65

def charge(price, action, qty, lot, d):
    gross=float(price)*qty*lot
    stt=gross*(0.001 if d<date(2026,4,1) else 0.0015) if action=="SELL" else 0
    exch=gross*(0.0003503 if d<date(2026,3,1) else 0.000355299)
    sebi=gross*0.000001; stamp=gross*0.00003 if action=="BUY" else 0
    brokerage=20.0; gst=.18*(brokerage+exch+sebi)
    return brokerage+exch+sebi+stt+stamp+gst

def norm_cdf(x): return 0.5*(1.0+math.erf(x/math.sqrt(2.0)))

def bs_call(s,k,t,r,sigma):
    if t<=0: return max(s-k,0.0)
    if sigma<=0: return max(s-k,0.0)
    d1=(math.log(s/k)+(r+0.5*sigma*sigma)*t)/(sigma*math.sqrt(t)); d2=d1-sigma*math.sqrt(t)
    return s*norm_cdf(d1)-k*math.exp(-r*t)*norm_cdf(d2)

def implied_vol(s,k,t,target):
    if min(s,k,t,target)<=0: return None
    lo,hi=1e-6,5.0
    if target<max(s-k*math.exp(-0.0*t),0.0) or target>s: return None
    for _ in range(80):
        mid=(lo+hi)/2; v=bs_call(s,k,t,0.0,mid)
        if v<target: lo=mid
        else: hi=mid
    return (lo+hi)/2

def yz_vol(g):
    if len(g)<20: return None
    x=g.tail(20).copy()
    o,h,l,c=[x[z].astype(float) for z in ("open","high","low","close")]
    rs=(math.log(h/l)*math.log(h/o)+math.log(l/o)*math.log(l/c)).mean()
    oc=(c/o).apply(math.log); co=(o/c.shift(1)).dropna().apply(math.log)
    if len(co)<19: return None
    k=0.34/(1.34+(21/19))
    var=co.var(ddof=1)+k*oc.var(ddof=1)+(1-k)*rs
    return math.sqrt(max(var,0.0)*252)*100.0

def opt(con,path,strike,typ,ts):
    p=str(path).replace("'","''")
    q=f"""SELECT CAST(open AS DOUBLE) px FROM read_parquet('{p}')
          WHERE CAST(timestamp AS TIMESTAMP)=TIMESTAMP '{ts}'
          AND CAST(strike AS DOUBLE)={float(strike)}
          AND UPPER(CAST(option_type AS VARCHAR))='{typ}' AND open>0 LIMIT 1"""
    x=con.execute(q).df()
    return None if x.empty or pd.isna(x.iloc[0].px) else float(x.iloc[0].px)

def execute(con,path,day,expiry,signal_ts,exit_ts,spot,atm,side,wing,slip):
    lot=lot_size(expiry); specs=[]
    if side=="SHORT_CONDOR":
        specs=[("CE",atm,"SELL"),("PE",atm,"SELL"),("CE",atm+wing,"BUY"),("PE",atm-wing,"BUY")]
    else:
        specs=[("CE",atm,"BUY"),("PE",atm,"BUY")]
    net=raw=slip_total=tc=0.0
    legs=[]
    for typ,strike,action in specs:
        ep=opt(con,path,strike,typ,signal_ts); xp=opt(con,path,strike,typ,exit_ts)
        if ep is None or xp is None: return None
        if action=="BUY":
            ee=ep+slip; xx=max(0,xp-slip); ex=(xx-ee)*lot
        else:
            ee=max(0,ep-slip); xx=xp+slip; ex=(ee-xx)*lot
        rp=(xp-ep)*lot if action=="BUY" else (ep-xp)*lot
        sc=rp-ex; exit_action="SELL" if action=="BUY" else "BUY"
        costs=charge(ee,action,1,lot,day)+charge(xx,exit_action,1,lot,day)
        raw+=rp; net+=ex-costs; slip_total+=sc; tc+=costs
        legs.append({"type":typ,"strike":strike,"action":action,"entry":ep,"exit":xp})
    return {"day":str(day),"expiry":str(expiry),"atm":atm,"side":side,"wing":wing,
            "raw_gross":raw,"execution_gross":net+tc,"slippage_cost":slip_total,
            "transaction_costs":tc,"net_pnl":net,"legs":json.dumps(legs,separators=(",",":"))}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--data",default="data/cache/phase31_trademarkk"); ap.add_argument("--out",default="reports/phase31_6"); ap.add_argument("--slippage",type=float,default=.20); args=ap.parse_args()
    root=Path(args.data); out=Path(args.out); out.mkdir(parents=True,exist_ok=True)
    con=duckdb.connect(); con.execute("SET TimeZone='Asia/Kolkata'")
    ip=root/"index/NIFTY.parquet"
    idx=con.execute(f"""SELECT CAST(timestamp AS TIMESTAMP) ts,CAST(open AS DOUBLE) open,CAST(high AS DOUBLE) high,CAST(low AS DOUBLE) low,CAST(close AS DOUBLE) close
                        FROM read_parquet('{ip}') ORDER BY ts""").df()
    idx.ts=pd.to_datetime(idx.ts); idx["date"]=idx.ts.dt.date; idx["time"]=idx.ts.dt.strftime("%H:%M:%S")
    idx=idx[(idx.date>=START)&(idx.date<=END)]
    files={}
    for p in (root/"options/NIFTY").glob("*.parquet"):
        try: pd.Timestamp(p.stem); files[p.stem]=p
        except: pass
    expiries=sorted(pd.to_datetime(list(files)).date)
    sessions=sorted(idx.date.unique()); rows=[]; diag=[]
    for day in sessions:
        ddf=idx[idx.date<day].drop_duplicates("date")
        rv=yz_vol(ddf)
        bars=idx[(idx.date==day)&(idx.time>="09:30:00")&(idx.time<="15:10:00")]
        srow=bars[bars.time=="09:30:00"]
        entryrow=bars[bars.time=="09:31:00"]; exitrow=bars[bars.time=="15:10:00"]
        if rv is None or srow.empty or entryrow.empty or exitrow.empty: diag.append({"day":str(day),"status":"MISSING_RV_OR_BAR"}); continue
        spot=float(srow.iloc[0].close); atm=int(round(spot/50)*50)
        avail=[e for e in expiries if e>=day]
        if len(avail)<2: diag.append({"day":str(day),"status":"MISSING_EXPIRY"}); continue
        for bucket in EXPIRY_BUCKETS:
          expiry=avail[bucket]; p=files[str(expiry)]
          t=max((pd.Timestamp(f"{expiry} 15:30:00")-pd.Timestamp(srow.iloc[0].ts)).total_seconds()/31536000,1/31536000)
          ce=opt(con,p,atm,"CE",srow.iloc[0].ts); pe=opt(con,p,atm,"PE",srow.iloc[0].ts)
          if ce is None or pe is None: diag.append({"day":str(day),"bucket":bucket,"status":"MISSING_ATM_IV"}); continue
          iv=implied_vol(spot,atm,t,(ce+pe)/2.0)
          if iv is None: diag.append({"day":str(day),"bucket":bucket,"status":"IV_FAIL"}); continue
          spread=iv*100-rv
          for thr in THRESHOLDS:
            side="SHORT_CONDOR" if spread>=thr else ("LONG_STRADDLE" if spread<=-thr else None)
            if side is None: continue
            for wing in WINGS:
              if side=="LONG_STRADDLE" and wing!=WINGS[0]: continue
              res=execute(con,p,day,expiry,entryrow.iloc[0].ts,exitrow.iloc[0].ts,spot,atm,side,wing,args.slippage)
              if res is None: diag.append({"day":str(day),"bucket":bucket,"threshold":thr,"side":side,"wing":wing,"status":"MISSING_LEG"}); continue
              res.update({"friction":"base" if args.slippage==.20 else "stress","threshold":thr,"bucket":bucket,"iv":iv*100,"rv":rv,"iv_rv":spread})
              rows.append(res)
    con.close()
    trades=pd.DataFrame(rows); trades.to_csv(out/"trades.csv",index=False); pd.DataFrame(diag).to_csv(out/"diagnostics.csv",index=False)
    if trades.empty: raise SystemExit("No executable IV-RV trades")
    summaries=[]
    for keys,g in trades.groupby(["threshold","side","wing","bucket","friction"]):
        wk=g.assign(week=pd.to_datetime(g.day).dt.to_period("W-SUN").astype(str)).groupby("week").net_pnl.sum()
        summaries.append({"threshold":float(keys[0]),"side":keys[1],"wing":int(keys[2]),"bucket":int(keys[3]),"friction":keys[4],
          "trades":len(g),"total_net":g.net_pnl.sum(),"mean_weekly_net":wk.mean(),"median_weekly_net":wk.median(),
          "positive_week_rate":(wk>0).mean(),"worst_trade":g.net_pnl.min(),"worst_week":wk.min(),
          "total_slippage":g.slippage_cost.sum(),"total_transaction_costs":g.transaction_costs.sum()})
    pd.DataFrame(summaries).to_csv(out/"cell_summary.csv",index=False)
if __name__=="__main__": main()
