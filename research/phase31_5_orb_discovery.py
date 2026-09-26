#!/usr/bin/env python3
from pathlib import Path
import json
from datetime import date
import duckdb
import pandas as pd

START=date(2021,7,1); END=date(2026,8,31)
OR_WINDOWS=(5,15,30); MULTIPLIERS=(0.25,0.50,1.00)

def lot_size(expiry):
    d=pd.Timestamp(expiry).date()
    if d<date(2024,4,26): return 50
    if d<date(2024,11,21): return 25
    if d<date(2026,1,6): return 75
    return 65

def nearest50(x): return int(round(float(x)/50)*50)

def charge(price, action, qty, lot, d):
    gross=float(price)*qty*lot
    stt=gross*(0.001 if d<date(2026,4,1) else 0.0015) if action=="SELL" else 0
    exch=gross*(0.0003503 if d<date(2026,3,1) else 0.000355299)
    sebi=gross*0.000001
    stamp=gross*0.00003 if action=="BUY" else 0
    brokerage=20.0
    gst=.18*(brokerage+exch+sebi)
    return brokerage+exch+sebi+stt+stamp+gst

def opt(con,p,strike,typ,ts):
    ps=str(p).replace("'","''")
    q=f"""SELECT CAST(open AS DOUBLE) px FROM read_parquet('{ps}')
          WHERE CAST(timestamp AS TIMESTAMP)=TIMESTAMP '{ts}'
          AND CAST(strike AS DOUBLE)={float(strike)}
          AND UPPER(CAST(option_type AS VARCHAR))='{typ}' AND open>0 LIMIT 1"""
    x=con.execute(q).df()
    return None if x.empty or pd.isna(x.iloc[0].px) else float(x.iloc[0].px)

def simulate(con, idx, path, expiry, day, window, mult, slip):
    bars=idx[(idx["date"]==day) & (idx["time"]>="09:15:00") & (idx["time"]<="15:10:00")].copy()
    or_end=pd.Timestamp(f"{day} 09:{15+window:02d}:00")
    orbars=bars[bars.ts<or_end]
    if len(orbars)<window: return None
    hi=float(orbars.high_px.max()); lo=float(orbars.low_px.min()); width=hi-lo
    if width<=0: return None
    up=hi+mult*width; dn=lo-mult*width
    post=bars[bars.ts>=or_end]
    sig=None; direction=None
    for _,r in post.iterrows():
        c=float(r.close_px)
        if c>=up: sig=r; direction="UP"; break
        if c<=dn: sig=r; direction="DOWN"; break
    if sig is None: return {"status":"NO_SIGNAL"}
    spot=float(sig.close); atm=nearest50(spot); lot=lot_size(expiry)
    legs=[("CE",atm,"BUY"),("CE",atm+200,"SELL")] if direction=="UP" else [("PE",atm,"BUY"),("PE",atm-200,"SELL")]
    et=sig.ts; xt=pd.Timestamp(f"{day} 15:10:00")
    gross=slip_cost=tc=0
    legrows=[]
    for typ,strike,action in legs:
        ep=opt(con,path,strike,typ,et); xp=opt(con,path,strike,typ,xt)
        if ep is None or xp is None: return {"status":"MISSING_OPTION","signal":str(et),"strike":strike,"type":typ}
        if action=="BUY":
            ee=ep+slip; xx=max(0,xp-slip); raw=(xp-ep)*lot; ex=(xx-ee)*lot; exit_action="SELL"
        else:
            ee=max(0,ep-slip); xx=xp+slip; raw=(ep-xp)*lot; ex=(ee-xx)*lot; exit_action="BUY"
        sc=raw-ex; costs=charge(ee,action,1,lot,day)+charge(xx,exit_action,1,lot,day)
        gross+=ex; slip_cost+=sc; tc+=costs
        legrows.append({"type":typ,"strike":strike,"action":action,"entry":ep,"exit":xp,"raw":raw,"exec":ex})
    return {"day":str(day),"window":window,"multiplier":mult,"direction":direction,"signal_time":str(et),
            "spot":spot,"atm":atm,"expiry":str(expiry),"lot_size":lot,"raw_gross":gross+slip_cost,
            "execution_gross":gross,"slippage_cost":slip_cost,"transaction_costs":tc,
            "net_pnl":gross-tc,"legs":json.dumps(legrows,separators=(",",":"))}

def main():
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument("--data",default="data/cache/phase31_trademarkk"); ap.add_argument("--out",default="reports/phase31_5"); args=ap.parse_args()
    root=Path(args.data); out=Path(args.out); out.mkdir(parents=True,exist_ok=True)
    con=duckdb.connect(); con.execute("SET TimeZone='Asia/Kolkata'")
    ip=root/"index/NIFTY.parquet"
    idx=con.execute(f"""SELECT CAST(timestamp AS TIMESTAMP) ts, CAST(open AS DOUBLE) open_px,
        CAST(high AS DOUBLE) high_px, CAST(low AS DOUBLE) low_px, CAST(close AS DOUBLE) close_px
        FROM read_parquet('{ip}') ORDER BY ts""").df()
    idx["ts"]=pd.to_datetime(idx.ts); idx["date"]=idx.ts.dt.date; idx["time"]=idx.ts.dt.strftime("%H:%M:%S")
    idx=idx[(idx.date>=START)&(idx.date<=END)]
    files={}
    for p in (root/"options/NIFTY").glob("*.parquet"):
        try: pd.Timestamp(p.stem); files[p.stem]=p
        except: pass
    expiries=sorted(pd.to_datetime(list(files)).date)
    rows=[]; diagnostics=[]
    sessions=sorted(idx.date.unique())
    for w in OR_WINDOWS:
      for m in MULTIPLIERS:
        for slip,label in [(0.20,"base"),(0.40,"stress")]:
          for day in sessions:
            fut=[e for e in expiries if e>=day]
            if not fut: continue
            expiry=fut[0]; res=simulate(con,idx,files[str(expiry)],expiry,day,w,m,slip)
            if res is None: diagnostics.append({"day":str(day),"window":w,"multiplier":m,"friction":label,"status":"INSUFFICIENT_OR"})
            elif "net_pnl" in res: res["friction"]=label; rows.append(res)
            else: diagnostics.append({"day":str(day),"window":w,"multiplier":m,"friction":label,**res})
    con.close()
    trades=pd.DataFrame(rows); trades.to_csv(out/"cell_trades.csv",index=False)
    if trades.empty: raise SystemExit("No executable ORB trades")
    summaries=[]
    for keys,g in trades.groupby(["window","multiplier","friction"]):
        wk=g.assign(week=pd.to_datetime(g.day).dt.to_period("W-SUN").astype(str)).groupby("week").net_pnl.sum()
        summaries.append({"window":int(keys[0]),"multiplier":float(keys[1]),"friction":keys[2],"trades":int(len(g)),
           "mean_daily_net":float(g.net_pnl.mean()),"median_daily_net":float(g.net_pnl.median()),
           "mean_weekly_net":float(wk.mean()),"median_weekly_net":float(wk.median()),
           "positive_week_rate":float((wk>0).mean()),"total_net":float(g.net_pnl.sum()),
           "worst_trade":float(g.net_pnl.min()),"worst_week":float(wk.min()),
           "total_slippage":float(g.slippage_cost.sum()),"total_transaction_costs":float(g.transaction_costs.sum())})
    pd.DataFrame(summaries).sort_values(["friction","mean_weekly_net"],ascending=[True,False]).to_csv(out/"cell_summary.csv",index=False)
    pd.DataFrame(diagnostics).to_csv(out/"diagnostics.csv",index=False)
    (out/"final_result.md").write_text("# Phase 31.5 discovery result\n\nFinite ORB grid completed. Discovery results do not authorize OOS promotion.\n")
if __name__=="__main__": main()
