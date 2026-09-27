from __future__ import annotations

import argparse, json, math
from pathlib import Path
from datetime import date
from statistics import NormalDist

import duckdb
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

START=date(2021,7,1)
END=date(2026,8,31)
WARMUP=60
FEATURES=("ATM_TERM_Z","WING_TERM_Z")
THRESHOLDS=(0.75,1.25)
EXITS=("10:30:00","15:10:00")
NULL_SEEDS=(101,202,303,404,505)
STRIKE_STEP=50.0
WING=100.0
ND=NormalDist()

def lot_size(expiry):
    d=pd.Timestamp(expiry).date()
    if d<date(2024,4,26): return 50
    if d<date(2024,11,21): return 25
    if d<date(2026,1,6): return 75
    return 65

def charge(price, action, qty, lot, d):
    gross=float(price)*qty*lot
    d=pd.Timestamp(d).date()
    stt=gross*(0.001 if d<date(2026,4,1) else 0.0015) if action=="SELL" else 0.0
    exch=gross*(0.0003503 if d<date(2026,3,1) else 0.000355299)
    sebi=gross*0.000001
    stamp=gross*0.00003 if action=="BUY" else 0.0
    brokerage=20.0
    gst=0.18*(brokerage+exch+sebi)
    return brokerage+exch+sebi+stt+stamp+gst

def idx_path(root): return str(root/"index"/"NIFTY.parquet")
def opt_glob(root): return str(root/"options"/"NIFTY"/"*.parquet")

def norm_cdf(x):
    x=np.asarray(x,float)
    a=np.abs(x)
    t=1/(1+0.2316419*a)
    poly=((((1.330274429*t-1.821255978)*t+1.781477937)*t-0.356563782)*t+0.319381530)*t
    pdf=np.exp(-x*x/2)/np.sqrt(2*np.pi)
    out=1-pdf*poly
    out=np.where(x<0,1-out,out)
    return out

def bs_price_vec(s,k,t,sigma,call):
    s,k,t,sigma=np.broadcast_arrays(np.asarray(s,float),np.asarray(k,float),np.asarray(t,float),np.asarray(sigma,float))
    call=np.broadcast_to(np.asarray(call,bool),s.shape)
    out=np.full(s.shape,np.nan)
    m=(s>0)&(k>0)&(t>0)&(sigma>0)
    if not np.any(m): return out
    d1=(np.log(s[m]/k[m])+0.5*sigma[m]*sigma[m]*t[m])/(sigma[m]*np.sqrt(t[m]))
    d2=d1-sigma[m]*np.sqrt(t[m])
    c=norm_cdf(d1); c2=norm_cdf(d2)
    out[m]=np.where(call[m],s[m]*c-k[m]*c2,k[m]*(1-c2)-s[m]*(1-c))
    return out

def implied_vol_vec(price,s,k,t,call):
    price,s,k,t=np.broadcast_arrays(np.asarray(price,float),np.asarray(s,float),np.asarray(k,float),np.asarray(t,float))
    call=np.broadcast_to(np.asarray(call,bool),price.shape)
    lo=np.full(price.shape,1e-6); hi=np.full(price.shape,5.0)
    intrinsic=np.where(call,np.maximum(s-k,0),np.maximum(k-s,0))
    valid=np.isfinite(price)&(price>0)&np.isfinite(s)&(s>0)&np.isfinite(k)&(k>0)&np.isfinite(t)&(t>0)&(price>=intrinsic-1e-7)
    for _ in range(70):
        mid=(lo+hi)/2
        p=bs_price_vec(s,k,t,mid,call)
        hi=np.where(p>price,mid,hi)
        lo=np.where(p>price,lo,mid)
    iv=(lo+hi)/2
    iv[~valid]=np.nan
    return iv

def load_index(root):
    con=duckdb.connect()
    q=f"""SELECT CAST(trading_day AS DATE) trade_date,
                 CAST(timestamp AS TIMESTAMP) ts,
                 CAST(open AS DOUBLE) open_px,
                 CAST(close AS DOUBLE) close_px
          FROM read_parquet('{idx_path(root)}',union_by_name=true)
          WHERE CAST(trading_day AS DATE) BETWEEN DATE '{START}' AND DATE '{END}'
            AND close>0
          ORDER BY ts"""
    x=con.execute(q).df(); con.close()
    x["trade_date"]=pd.to_datetime(x.trade_date).dt.date
    x["ts"]=pd.to_datetime(x.ts)
    return x

def expiry_list(root):
    out=[]
    for p in sorted((root/"options"/"NIFTY").glob("*.parquet")):
        try: out.append((pd.Timestamp(p.stem).date(),p))
        except Exception: pass
    return out

def build_session_table(index):
    daily=index.sort_values("ts").groupby("trade_date").agg(last_ts=("ts","last"),close_px=("close_px","last"),open_px=("open_px","first")).reset_index()
    return daily.sort_values("trade_date").reset_index(drop=True)

def surface_panel(root):
    index=load_index(root)
    sessions=build_session_table(index)
    exps=expiry_list(root)
    exp_dates=[d for d,_ in exps]
    rows=[]
    for s in sessions.itertuples(index=False):
        d=s.trade_date
        future=[x for x in exps if x[0]>d]
        if len(future)<2: continue
        front,back=future[0],future[1]
        atm=round(float(s.close_px)/STRIKE_STEP)*STRIKE_STEP
        req=[]
        for exp,p in (front,back):
            for typ,strike,label in (
                ("CE",atm,"atm_ce"),("PE",atm,"atm_pe"),
                ("PE",atm-WING,"put100"),("CE",atm+WING,"call100")
            ):
                req.append((exp[0],p,typ,float(strike),label))
        by_exp={front[0]:[],back[0]:[]}
        for e,p,t,k,l in req: by_exp[e].append((p,t,k,l))
        vals={}
        for e,items in by_exp.items():
            p=items[0][0]
            strikes=",".join(str(x[2]) for x in items)
            types="'CE','PE'"
            ts=f"TIMESTAMP '{pd.Timestamp(s.last_ts)}'"
            ps=str(p).replace("'","''")
            q=f"""WITH src AS (
                    SELECT UPPER(CAST(option_type AS VARCHAR)) option_type,
                           CAST(strike AS DOUBLE) strike,
                           CAST(close AS DOUBLE) close_px,
                           CAST(expiry AS DATE) expiry,
                           CAST(timestamp AS TIMESTAMP) ts
                    FROM read_parquet('{ps}')
                    WHERE CAST(timestamp AS TIMESTAMP)<={ts}
                      AND CAST(strike AS DOUBLE) IN ({strikes})
                      AND UPPER(CAST(option_type AS VARCHAR)) IN ({types})
                      AND close>0
                  )
                  SELECT option_type,strike,close_px,expiry
                  FROM src
                  QUALIFY ROW_NUMBER() OVER (PARTITION BY option_type,strike ORDER BY ts DESC)=1
                  """
            con=duckdb.connect(); z=con.execute(q).df(); con.close()
            if z.empty: continue
            expiry_ts=pd.Timestamp(e)+pd.Timedelta(hours=15,minutes=30)
            t=(expiry_ts-pd.Timestamp(s.last_ts)).total_seconds()/31536000.0
            k=z.strike.to_numpy(float); px=z.close_px.to_numpy(float)
            call=(z.option_type.to_numpy()=="CE")
            iv=implied_vol_vec(px,np.full(len(z),float(s.close_px)),k,np.full(len(z),t),call)
            for r,ivv in zip(z.itertuples(index=False),iv):
                if np.isfinite(ivv):
                    vals[(e,r.option_type,float(r.strike))]=float(ivv*100)
        needed=[]
        for e,_ in (front,back):
            for typ,strike,label in (
                ("CE",atm,"atm_ce"),("PE",atm,"atm_pe"),
                ("PE",atm-WING,"put100"),("CE",atm+WING,"call100")
            ):
                if (e,typ,float(strike)) not in vals:
                    break
                needed.append((e,typ,float(strike),label))
        if len(needed)!=8: continue
        fce=vals[(front[0],"CE",atm)]; fpe=vals[(front[0],"PE",atm)]
        bce=vals[(back[0],"CE",atm)]; bpe=vals[(back[0],"PE",atm)]
        fw=(vals[(front[0],"PE",atm-WING)]+vals[(front[0],"CE",atm+WING)])/2
        bw=(vals[(back[0],"PE",atm-WING)]+vals[(back[0],"CE",atm+WING)])/2
        rows.append({"trade_date":d,"last_ts":s.last_ts,"spot":float(s.close_px),
                     "front_expiry":front[0],"back_expiry":back[0],
                     "atm_term_spread":(fce+fpe)/2-(bce+bpe)/2,
                     "wing_term_spread":fw-bw})
    panel=pd.DataFrame(rows).sort_values("trade_date").reset_index(drop=True)
    if panel.empty: raise RuntimeError("No two-expiry term-structure observations")
    for raw,zcol in [("atm_term_spread","ATM_TERM_Z"),("wing_term_spread","WING_TERM_Z")]:
        prior=panel[raw].shift(1)
        mu=prior.rolling(WARMUP,min_periods=WARMUP).mean()
        sd=prior.rolling(WARMUP,min_periods=WARMUP).std(ddof=1).replace(0,np.nan)
        panel[zcol]=(panel[raw]-mu)/sd
    return panel,sessions

def build_signals(panel,sessions):
    idx=sessions.set_index("trade_date").sort_index()
    dates=list(idx.index)
    nxt={dates[i]:dates[i+1] for i in range(len(dates)-1)}
    rows=[]
    for r in panel.itertuples(index=False):
        d=r.trade_date
        if d not in nxt: continue
        td=nxt[d]
        for f in FEATURES:
            z=getattr(r,f)
            if not np.isfinite(z): continue
            for th in THRESHOLDS:
                if z<th: continue
                for ex in EXITS:
                    rows.append({"feature":f,"threshold":th,"exit_time":ex,
                                 "signal_date":d,"trade_date":td,
                                 "front_expiry":r.front_expiry,"back_expiry":r.back_expiry,
                                 "spot":r.spot,"signal_value":z})
    return pd.DataFrame(rows)

def execution_price_map(signals,root):
    prices={}
    if signals.empty: return prices
    req=[]
    for r in signals.itertuples(index=False):
        for exp in (r.front_expiry,r.back_expiry):
            for tm in ("09:31:00",str(r.exit_time)):
                for typ in ("CE","PE"):
                    req.append((r.trade_date,exp,tm,typ))
    req=pd.DataFrame(req,columns=["trade_date","expiry","time","type"]).drop_duplicates()
    con=duckdb.connect()
    for exp,g in req.groupby("expiry"):
        path=root/"options"/"NIFTY"/f"{pd.Timestamp(exp).date()}.parquet"
        if not path.exists(): continue
        dates=",".join(f"DATE '{d}'" for d in sorted(pd.to_datetime(g.trade_date).dt.date.unique()))
        times=",".join(f"'{x}'" for x in sorted(g.time.unique()))
        ps=str(path).replace("'","''")
        q=f"""SELECT CAST(trading_day AS DATE) trade_date,
                     CAST(expiry AS DATE) expiry,
                     strftime(CAST(timestamp AS TIMESTAMP),'%H:%M:%S') time,
                     UPPER(CAST(option_type AS VARCHAR)) option_type,
                     CAST(strike AS DOUBLE) strike,
                     CAST(open AS DOUBLE) open_px,
                     CAST(close AS DOUBLE) close_px
              FROM read_parquet('{ps}')
              WHERE CAST(trading_day AS DATE) IN ({dates})
                AND strftime(CAST(timestamp AS TIMESTAMP),'%H:%M:%S') IN ({times})
                AND UPPER(CAST(option_type AS VARCHAR)) IN ('CE','PE')
                AND ((strftime(CAST(timestamp AS TIMESTAMP),'%H:%M:%S')='09:31:00' AND open>0)
                  OR (strftime(CAST(timestamp AS TIMESTAMP),'%H:%M:%S')<>'09:31:00' AND close>0)"""
        z=con.execute(q).df()
        if z.empty: continue
        for r in z.itertuples(index=False):
            key=(r.trade_date,r.expiry,r.time,r.option_type)
            prices[key]=float(r.open_px if r.time=="09:31:00" else r.close_px)
    con.close(); return prices

def trade_rows(signals,prices,slippage):
    rows=[]
    coverage_rows=[]
    debit_rows=[]
    for r in signals.itertuples(index=False):
        d=pd.Timestamp(r.trade_date).date()
        fe=pd.Timestamp(r.front_expiry).date(); be=pd.Timestamp(r.back_expiry).date(); lot=lot_size(fe)
        entry_tm="09:31:00"; exit_tm=str(r.exit_time)
        keys=[(d,fe,entry_tm,"CE"),(d,fe,entry_tm,"PE"),(d,be,entry_tm,"CE"),(d,be,entry_tm,"PE"),
              (d,fe,exit_tm,"CE"),(d,fe,exit_tm,"PE"),(d,be,exit_tm,"CE"),(d,be,exit_tm,"PE")]
        complete=all(k in prices for k in keys)
        if complete:
            fce=prices[keys[0]]; fpe=prices[keys[1]]; bce=prices[keys[2]]; bpe=prices[keys[3]]
            xfc=prices[keys[4]]; xfp=prices[keys[5]]; xbc=prices[keys[6]]; xbp=prices[keys[7]]
            entry_debit=(bce+bpe)-(fce+fpe)
            debit_ok=entry_debit>0
        else:
            entry_debit=np.nan; debit_ok=False
        coverage_rows.append((r.feature,r.threshold,r.exit_time,complete))
        debit_rows.append((r.feature,r.threshold,r.exit_time,complete and debit_ok))
        if not complete or not debit_ok:
            continue
        exit_value=(xbc+xbp)-(xfc+xfp)
        gross=(exit_value-entry_debit)*lot
        slip=slippage*8*lot
        tc=(charge(fce,"SELL",1,lot,d)+charge(fpe,"SELL",1,lot,d)+
            charge(bce,"BUY",1,lot,d)+charge(bpe,"BUY",1,lot,d)+
            charge(xfc,"BUY",1,lot,d)+charge(xfp,"BUY",1,lot,d)+
            charge(xbc,"SELL",1,lot,d)+charge(xbp,"SELL",1,lot,d))
        rows.append({**r._asdict(),"entry_debit":entry_debit,"exit_value":exit_value,
                     "gross_pnl":gross,"slippage":slip,"transaction_costs":tc,
                     "net_pnl":gross-slip-tc,"week":str(pd.Timestamp(d).to_period("W-SUN"))})
    cov_df=coverage_table(signals,coverage_rows)
    debit_df=debit_coverage_table(signals,debit_rows)
    return pd.DataFrame(rows),cov_df,debit_df

def coverage_table(signals,checks):
    out=[]
    checks_by={}
    for f,th,ex,ok in checks:
        checks_by.setdefault((f,th,ex),[]).append(ok)
    for f in FEATURES:
        for th in THRESHOLDS:
            for ex in EXITS:
                vals=checks_by.get((f,th,ex),[])
                n=int(((signals.feature==f)&(signals.threshold==th)&(signals.exit_time==ex)).sum()) if not signals.empty else 0
                ok=int(sum(vals))
                out.append({"feature":f,"threshold":th,"exit_time":ex,"signals":n,"execution_complete":ok,
                            "coverage_rate":ok/n if n else 1.0})
    return pd.DataFrame(out)

def debit_coverage_table(signals,checks):
    out=[]
    checks_by={}
    for f,th,ex,ok in checks:
        checks_by.setdefault((f,th,ex),[]).append(ok)
    for f in FEATURES:
        for th in THRESHOLDS:
            for ex in EXITS:
                vals=checks_by.get((f,th,ex),[])
                n=int(((signals.feature==f)&(signals.threshold==th)&(signals.exit_time==ex)).sum()) if not signals.empty else 0
                ok=int(sum(vals))
                out.append({"feature":f,"threshold":th,"exit_time":ex,"signals":n,"positive_debit":ok,
                            "debit_rate":ok/n if n else 1.0})
    return pd.DataFrame(out)

def summarize(trades):
    rows=[]
    for f in FEATURES:
        for th in THRESHOLDS:
            for ex in EXITS:
                g=trades[(trades.feature==f)&(trades.threshold==th)&(trades.exit_time==ex)] if not trades.empty else pd.DataFrame()
                w=g.groupby("week").net_pnl.sum() if not g.empty else pd.Series(dtype=float)
                rows.append({"feature":f,"threshold":th,"exit_time":ex,"trades":len(g),"weeks":len(w),
                             "total_net":float(g.net_pnl.sum()) if not g.empty else 0.0,
                             "mean_weekly_net":float(w.mean()) if len(w) else 0.0,
                             "median_weekly_net":float(w.median()) if len(w) else 0.0,
                             "positive_week_rate":float((w>0).mean()) if len(w) else 0.0,
                             "raw_gross":float(g.gross_pnl.sum()) if not g.empty else 0.0,
                             "slippage":float(g.slippage.sum()) if not g.empty else 0.0,
                             "transaction_costs":float(g.transaction_costs.sum()) if not g.empty else 0.0})
    return pd.DataFrame(rows)

def null_summary(panel,sessions,root,slippage):
    out=[]
    for seed in NULL_SEEDS:
        rng=np.random.default_rng(seed)
        x=panel.copy()
        idx=np.arange(len(x)); rng.shuffle(idx)
        x.loc[:,list(FEATURES)]=x.loc[idx,list(FEATURES)].to_numpy()
        sig=build_signals(x,sessions)
        tr,_,_=trade_rows(sig,execution_price_map(sig,root),slippage)
        z=summarize(tr); z["null_seed"]=seed; out.append(z)
    return pd.concat(out,ignore_index=True)

def gate(panel,signals,cov,sessions):
    warm=panel.iloc[WARMUP:].copy()
    expected=max(int(sessions.trade_date.nunique())-1,0)
    snapshot=int(panel.trade_date.nunique())
    feature_cov={f:float(warm[f].notna().mean()) if len(warm) else 0.0 for f in FEATURES}
    return {"status":"PASS" if expected and snapshot/expected>=0.95 and all(v>=0.95 for v in feature_cov.values())
            and len(cov)==8 and cov.coverage_rate.min()>=0.95 else "FAIL",
            "expected_prior_sessions":expected,"snapshot_sessions":snapshot,
            "snapshot_coverage":snapshot/expected if expected else 0.0,
            "warmup_sessions":len(warm),"feature_coverage":feature_cov,
            "signal_rows":len(signals),"coverage_min":float(cov.coverage_rate.min()) if len(cov) else 0.0,
            "coverage_cells":len(cov)}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--data",default="data/cache/phase31_trademarkk")
    ap.add_argument("--out",default="reports/phase34/gate")
    ap.add_argument("--slippage",type=float,default=.20)
    ap.add_argument("--gate-only",action="store_true")
    a=ap.parse_args()
    root=Path(a.data); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    panel,sessions=surface_panel(root); panel.to_csv(out/"term_structure_panel.csv",index=False)
    signals=build_signals(panel,sessions); signals.to_csv(out/"signals.csv",index=False)
    if a.gate_only:
        tr,cov,debit=trade_rows(signals,execution_price_map(signals,root),a.slippage)
        cov.to_csv(out/"price_coverage.csv",index=False)
        debit.to_csv(out/"debit_admissibility.csv",index=False)
        g=gate(panel,signals,cov,sessions); (out/"data_gate.json").write_text(json.dumps(g,indent=2)); print(json.dumps(g)); return
    prices=execution_price_map(signals,root)
    trades,cov,debit=trade_rows(signals,prices,a.slippage)
    trades.to_csv(out/"trades.csv",index=False)
    cov.to_csv(out/"price_coverage.csv",index=False)
    debit.to_csv(out/"debit_admissibility.csv",index=False)
    summarize(trades).to_csv(out/"true_cell_summary.csv",index=False)
    null_summary(panel,sessions,root,a.slippage).to_csv(out/"null_summary.csv",index=False)

if __name__=="__main__": main()
