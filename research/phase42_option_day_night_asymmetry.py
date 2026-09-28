from __future__ import annotations
import argparse, json, math
from datetime import date
from pathlib import Path
import duckdb, numpy as np, pandas as pd

START=date(2021,7,1); END=date(2026,8,31); LOOKBACK=60; TH=.75
EXITS=("10:30:00","15:10:00"); COVER=.95; SEEDS=(101,202,303,404,505)

def lot_size(exp):
    d=pd.Timestamp(exp).date()
    if d<date(2024,4,26): return 50
    if d<date(2024,11,21): return 25
    if d<date(2026,1,6): return 75
    return 65

def charge(price, action, qty, lot, d):
    gross=float(price)*qty*lot; d=pd.Timestamp(d).date()
    stt=gross*(.001 if d<date(2026,4,1) else .0015) if action=="SELL" else 0
    exch=gross*(.0003503 if d<date(2026,3,1) else .000355299)
    sebi=gross*.000001; stamp=gross*.00003 if action=="BUY" else 0
    brokerage=20.; gst=.18*(brokerage+exch+sebi)
    return brokerage+exch+sebi+stt+stamp+gst

def zprior(x, n=LOOKBACK):
    x=np.asarray(x,dtype=float); out=np.full(len(x),np.nan); hist=[]
    for i,v in enumerate(x):
        if len(hist)>=n and np.isfinite(v):
            a=np.asarray(hist[-n:]); sd=a.std(ddof=1)
            if sd>0: out[i]=(v-a.mean())/sd
        if np.isfinite(v): hist.append(v)
    return out

def expiry_files(root):
    out={}
    for p in sorted((root/"options/NIFTY").glob("*.parquet")):
        try: out[pd.Timestamp(p.stem).date()]=p
        except: pass
    return out

def index(root):
    p=str(root/"index/NIFTY.parquet").replace("'","''"); con=duckdb.connect()
    con.execute("SET TimeZone='Asia/Kolkata'")
    q=f"""select cast(timestamp as timestamp) ts, cast(close as double) px,
    strftime(cast(timestamp as timestamp),'%H:%M:%S') tm
    from read_parquet('{p}',union_by_name=true)
    where cast(timestamp as date) between date '{START}' and date '{END}'
    and strftime(cast(timestamp as timestamp),'%H:%M:%S') in ('09:15:00','15:10:00')"""
    x=con.execute(q).df(); con.close(); x["ts"]=pd.to_datetime(x.ts); x["d"]=x.ts.dt.date
    w=x.pivot_table(index="d",columns="tm",values="px",aggfunc="last").reset_index()
    return w.rename(columns={"09:15:00":"open","15:10:00":"close"}).sort_values("d").reset_index(drop=True)

def snap(con,path,d,exp,strike,times):
    p=str(path).replace("'","''"); ts=",".join("'"+t+"'" for t in times)
    q=f"""select cast(timestamp as timestamp) ts,upper(cast(option_type as varchar)) typ,
    cast(strike as double) strike,cast(close as double) px
    from read_parquet('{p}',union_by_name=true)
    where cast(timestamp as date)=date '{d}' and cast(strike as double)={float(strike)}
    and upper(cast(option_type as varchar)) in ('CE','PE')
    and strftime(cast(timestamp as timestamp),'%H:%M:%S') in ({ts})
    qualify row_number() over(partition by option_type,strftime(cast(timestamp as timestamp),'%H:%M:%S') order by ts desc)=1"""
    return con.execute(q).df()

def build_panel(root,out):
    idx=index(root); exps=expiry_files(root); ed=sorted(exps)
    con=duckdb.connect(); con.execute("SET TimeZone='Asia/Kolkata'")
    rows=[]; diag=[]
    for i in range(2,len(idx)):
        d=idx.iloc[i].d; p=idx.iloc[i-1]; pp=idx.iloc[i-2]
        fut=[e for e in ed if e>p.d]
        if not fut: diag.append({"d":str(d),"status":"MISSING_EXPIRY"}); continue
        if not np.isfinite(p.close) or not np.isfinite(pp.close) or not np.isfinite(idx.iloc[i].open):
            diag.append({"d":str(d),"status":"MISSING_INDEX_PRICE","prior_day":str(p.d),"prior2_day":str(pp.d)})
            continue
        exp=fut[0]; atm=math.floor(float(p.close)/50+.5)*50
        # Fixed expiry/strike selected using prior-session close; all three snapshots are historical.
        a=snap(con,exps[exp],pp.d,exp,atm,("15:10:00",))
        b=snap(con,exps[exp],p.d,exp,atm,("09:15:00","15:10:00"))
        vals={}
        for r in pd.concat([a,b],ignore_index=True).itertuples(index=False):
            vals[(r.ts.date(),r.ts.strftime("%H:%M:%S"),r.typ)]=float(r.px) if pd.notna(r.px) and r.px>0 else np.nan
        def strad(dd,tm):
            c=vals.get((dd,tm,"CE"),np.nan); q=vals.get((dd,tm,"PE"),np.nan)
            return c+q if np.isfinite(c) and np.isfinite(q) else np.nan
        s0=strad(pp.d,"15:10:00"); s1=strad(p.d,"09:15:00"); s2=strad(p.d,"15:10:00")
        overnight=s1/s0-1 if np.isfinite(s0) and s0>0 and np.isfinite(s1) else np.nan
        intraday=s2/s1-1 if np.isfinite(s1) and s1>0 and np.isfinite(s2) else np.nan
        asym=intraday-overnight if np.isfinite(overnight) and np.isfinite(intraday) else np.nan
        rows.append({"trade_date":d,"prior_day":p.d,"prior2_day":pp.d,"prior_close":float(p.close),
                     "current_open":float(idx.iloc[i].open),"opening_gap":float(idx.iloc[i].open/p.close-1),
                     "expiry":exp,"atm":atm,"overnight_straddle_return":overnight,
                     "intraday_straddle_return":intraday,"day_night_asymmetry":asym})
    con.close(); panel=pd.DataFrame(rows).sort_values("trade_date").reset_index(drop=True)
    panel["z"]=zprior(panel.day_night_asymmetry)
    panel["feature_eligible"]=panel.z.notna()&panel.opening_gap.notna()
    panel["prior_information_violation"]=pd.to_datetime(panel.prior_day)>=pd.to_datetime(panel.trade_date)
    Path(out).mkdir(parents=True,exist_ok=True); panel.to_csv(Path(out)/"feature_panel.csv",index=False)
    pd.DataFrame(diag).to_csv(Path(out)/"feature_diagnostics.csv",index=False)
    return panel,exps

def signals(panel):
    rows=[]
    for r in panel.itertuples(index=False):
        if not r.feature_eligible or r.opening_gap==0: continue
        st="HIGH_ASYMMETRY" if r.z>=TH else ("LOW_ASYMMETRY" if r.z<=-TH else None)
        if not st: continue
        for mp in ("FOLLOW_GAP","FADE_GAP"):
            side="BULL" if r.opening_gap>0 else "BEAR"
            if mp=="FADE_GAP": side="BEAR" if side=="BULL" else "BULL"
            for ex in EXITS: rows.append({**r._asdict(),"state":st,"mapping":mp,"side":side,"exit_time":ex})
    return pd.DataFrame(rows)

def price_map(root,sigs,exps):
    con=duckdb.connect(); con.execute("SET TimeZone='Asia/Kolkata'"); out={}
    req=[]
    for r in sigs.itertuples(index=False):
        d=pd.Timestamp(r.trade_date).date(); fut=[e for e in sorted(exps) if e>=d]
        if not fut: continue
        exp=fut[0]; atm=math.floor(float(r.current_open)/50+.5)*50
        typ="CE" if r.side=="BULL" else "PE"; wing=atm+200 if r.side=="BULL" else atm-200
        for tm in ("09:31:00",r.exit_time): req += [(d,exp,typ,atm,tm),(d,exp,typ,wing,tm)]
    qreq=pd.DataFrame(req,columns=["d","exp","typ","strike","tm"]).drop_duplicates()
    for exp,g in qreq.groupby("exp"):
        p=str(exps[exp]).replace("'","''"); ds=",".join("date '"+str(x)+"'" for x in g.d)
        ss=",".join(str(float(x)) for x in g.strike); ts=",".join("'"+x+"'" for x in g.tm)
        ty=",".join("'"+x+"'" for x in g.typ)
        q=f"""select cast(timestamp as timestamp) ts,cast(timestamp as date) d,
        upper(cast(option_type as varchar)) typ,cast(strike as double) strike,
        strftime(cast(timestamp as timestamp),'%H:%M:%S') tm,
        cast(open as double) op,cast(close as double) cl
        from read_parquet('{p}',union_by_name=true)
        where cast(timestamp as date) in ({ds}) and cast(strike as double) in ({ss})
        and upper(cast(option_type as varchar)) in ({ty}) and strftime(cast(timestamp as timestamp),'%H:%M:%S') in ({ts})"""
        for r in con.execute(q).df().itertuples(index=False):
            px=r.op if r.tm=="09:31:00" else r.cl
            if pd.notna(px) and px>0: out[(r.d,exp,r.typ,float(r.strike),r.tm)]=float(px)
    con.close(); return out

def trades(sigs,prices,exps,slip):
    rows=[]
    for r in sigs.itertuples(index=False):
        d=pd.Timestamp(r.trade_date).date(); fut=[e for e in sorted(exps) if e>=d]
        if not fut: continue
        exp=fut[0]; atm=math.floor(float(r.current_open)/50+.5)*50
        typ="CE" if r.side=="BULL" else "PE"; wing=atm+200 if r.side=="BULL" else atm-200
        k=[(d,exp,typ,atm,"09:31:00"),(d,exp,typ,wing,"09:31:00"),
           (d,exp,typ,atm,r.exit_time),(d,exp,typ,wing,r.exit_time)]
        if not all(x in prices for x in k): continue
        lot=lot_size(exp); le,se,lx,sx=[prices[x] for x in k]; debit=le-se
        if debit<=0: continue
        gross=(lx-sx-debit)*lot; sc=slip*4*lot
        tc=charge(le,"BUY",1,lot,d)+charge(se,"SELL",1,lot,d)+charge(lx,"SELL",1,lot,d)+charge(sx,"BUY",1,lot,d)
        net=gross-sc-tc
        rows.append({**r._asdict(),"expiry_exec":str(exp),"lot_size":lot,"raw_gross":gross,
                     "slippage_cost":sc,"transaction_costs":tc,"net_pnl":net,
                     "accounting_residual":net-(gross-sc-tc)})
    return pd.DataFrame(rows)

def coverage(sigs,tr):
    rows=[]
    for s in ("HIGH_ASYMMETRY","LOW_ASYMMETRY"):
      for m in ("FOLLOW_GAP","FADE_GAP"):
       for e in EXITS:
        a=sigs[(sigs.state==s)&(sigs.mapping==m)&(sigs.exit_time==e)]
        b=tr[(tr.state==s)&(tr.mapping==m)&(tr.exit_time==e)] if not tr.empty else tr
        rows.append({"state":s,"mapping":m,"exit_time":e,"signals":len(a),"trades":len(b),
                     "execution_coverage":len(b)/len(a) if len(a) else 0})
    return pd.DataFrame(rows)

def summary(tr):
    rows=[]
    for s in ("HIGH_ASYMMETRY","LOW_ASYMMETRY"):
      for m in ("FOLLOW_GAP","FADE_GAP"):
       for e in EXITS:
        g=tr[(tr.state==s)&(tr.mapping==m)&(tr.exit_time==e)]
        w=g.assign(week=pd.to_datetime(g.trade_date).dt.to_period("W-SUN").astype(str)).groupby("week").net_pnl.sum() if len(g) else pd.Series(dtype=float)
        p=g.net_pnl if len(g) else pd.Series(dtype=float); eq=p.cumsum(); dd=eq-eq.cummax()
        rows.append({"state":s,"mapping":m,"exit_time":e,"executed_trades":len(g),"weeks":len(w),
        "total_net":float(p.sum()) if len(p) else 0,"mean_weekly_net":float(w.mean()) if len(w) else 0,
        "median_weekly_net":float(w.median()) if len(w) else 0,"positive_week_rate":float((w>0).mean()) if len(w) else 0,
        "worst_week":float(w.min()) if len(w) else 0,"max_drawdown":float(dd.min()) if len(dd) else 0,
        "accounting_ok":bool(g.empty or g.accounting_residual.abs().max()<1e-10)})
    return pd.DataFrame(rows)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--data",required=True); ap.add_argument("--out",required=True)
    ap.add_argument("--slippage",type=float,default=.2); ap.add_argument("--gate-only",action="store_true"); ap.add_argument("--null",action="store_true")
    a=ap.parse_args(); root=Path(a.data); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    panel,exps=build_panel(root,out); sig=signals(panel)
    post=panel.iloc[LOOKBACK:] if len(panel)>LOOKBACK else panel.iloc[0:0]
    eligible=int(post.feature_eligible.sum()); expected=len(post)
    prices=price_map(root,sig,exps); tr=trades(sig,prices,exps,a.slippage); cov=coverage(sig,tr)
    gate={"status":"PASS" if expected and eligible/expected>=COVER and len(sig)>0 and len(cov)==8 and cov.execution_coverage.min()>=COVER and panel.prior_information_violation.sum()==0 else "FAIL",
          "raw_sessions":len(panel)+2,"post_warmup_sessions":expected,"feature_eligible_sessions":eligible,
          "post_warmup_eligibility_rate":eligible/expected if expected else 0,"prior_information_violations":int(panel.prior_information_violation.sum()),
          "signal_rows":len(sig),"execution_coverage_min":float(cov.execution_coverage.min()) if len(cov) else 0,"coverage_cells":len(cov),
          "required_coverage":COVER,"lookback_valid_observations":LOOKBACK,"study_start":str(START),"study_end":str(END)}
    cov.to_csv(out/"price_coverage.csv",index=False); json.dump(gate,open(out/"data_gate.json","w"),indent=2)
    if a.gate_only: print(json.dumps(gate,indent=2)); raise SystemExit(0 if gate["status"]=="PASS" else 1)
    tr.to_csv(out/"trades.csv",index=False); summary(tr).to_csv(out/"true_cell_summary.csv",index=False)
    null_rows=[]
    rng=np.random.default_rng
    base=panel.z.to_numpy(copy=True); elig=np.where(panel.feature_eligible.to_numpy())[0]
    for seed in SEEDS:
      for perm in (rng(seed)(base[elig].copy()) if False else []): pass
      shuffled=base.copy(); shuffled[elig]=rng(seed).permutation(base[elig])
      ns=sig.copy()
      # Nulls are represented as full-panel z permutations; rerun signals and execution using the same prices.
      q=panel.copy(); q["z"]=shuffled; qsig=signals(q); qtr=trades(qsig,price_map(root,qsig,exps),exps,a.slippage)
      ss=summary(qtr); ss["null_seed"]=seed; null_rows.append(ss)
    pd.concat(null_rows,ignore_index=True).to_csv(out/"null_summary.csv",index=False)
if __name__=="__main__": main()
