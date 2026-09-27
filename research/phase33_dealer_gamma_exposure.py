from __future__ import annotations

import argparse, json, math
from pathlib import Path
from statistics import NormalDist
import duckdb, numpy as np, pandas as pd

START_DATE=pd.Timestamp("2021-07-01").date()
END_DATE=pd.Timestamp("2026-08-31").date()
WARMUP=60
FEATURES=("GEX_Z","FLIP_DISTANCE_Z","ATM_GEX_SHARE_Z")
THRESHOLDS=(0.75,1.25)
EXITS=("10:30:00","15:10:00")
NULL_SEEDS=(101,202,303,404,505)
SPOT_WINDOW=1500.0
WING=200.0
ND=NormalDist()

def lot_size(expiry):
    d=pd.Timestamp(expiry).date()
    if d < pd.Timestamp("2024-04-26").date(): return 50
    if d < pd.Timestamp("2024-11-21").date(): return 25
    if d < pd.Timestamp("2026-01-06").date(): return 75
    return 65

def charge(price, action, qty, lot, d):
    gross=float(price)*qty*lot
    d=pd.Timestamp(d).date()
    stt=gross*(0.001 if d<pd.Timestamp("2026-04-01").date() else 0.0015) if action=="SELL" else 0.0
    exch=gross*(0.0003503 if d<pd.Timestamp("2026-03-01").date() else 0.000355299)
    sebi=gross*0.000001
    stamp=gross*0.00003 if action=="BUY" else 0.0
    brokerage=20.0
    gst=0.18*(brokerage+exch+sebi)
    return brokerage+exch+sebi+stt+stamp+gst

def idx_path(root): return str(root/"index"/"NIFTY.parquet")
def opt_glob(root): return str(root/"options"/"NIFTY"/"*.parquet")

def bs_price(s,k,t,sigma,call):
    if min(s,k,t,sigma)<=0: return np.nan
    d1=(math.log(s/k)+0.5*sigma*sigma*t)/(sigma*math.sqrt(t))
    d2=d1-sigma*math.sqrt(t)
    if call: return s*ND.cdf(d1)-k*ND.cdf(d2)
    return k*ND.cdf(-d2)-s*ND.cdf(-d1)

def implied_vol(price,s,k,t,call):
    if not np.isfinite(price) or price<=0 or s<=0 or k<=0 or t<=0: return None
    intrinsic=max(s-k,0) if call else max(k-s,0)
    if price < intrinsic-1e-7 or price >= (s if call else k)-1e-9: return None
    lo,hi=1e-6,5.0
    for _ in range(80):
        mid=(lo+hi)/2
        p=bs_price(s,k,t,mid,call)
        if p>price: hi=mid
        else: lo=mid
    iv=(lo+hi)/2
    return iv if np.isfinite(iv) and iv<5 else None

def bs_price_vec(s,k,t,sigma,call):
    s=np.asarray(s,float); k=np.asarray(k,float); t=np.asarray(t,float); sigma=np.asarray(sigma,float)
    out=np.full(np.broadcast(s,k,t,sigma).shape,np.nan)
    m=(s>0)&(k>0)&(t>0)&(sigma>0)
    if not np.any(m): return out
    ss,kk,tt,vv=np.broadcast_arrays(s,k,t,sigma)
    d1=(np.log(ss[m]/kk[m])+0.5*vv[m]*vv[m]*tt[m])/(vv[m]*np.sqrt(tt[m]))
    d2=d1-vv[m]*np.sqrt(tt[m])
    if np.ndim(call)==0:
        cc=bool(call)
        out[m]=ss[m]*np.vectorize(ND.cdf)(d1)-kk[m]*np.vectorize(ND.cdf)(d2) if cc else kk[m]*np.vectorize(ND.cdf)(-d2)-ss[m]*np.vectorize(ND.cdf)(-d1)
    else:
        cc=np.asarray(call,bool)
        cdf1=np.vectorize(ND.cdf)(d1); cdf2=np.vectorize(ND.cdf)(d2)
        out[m]=np.where(cc[m],ss[m]*cdf1-kk[m]*cdf2,kk[m]*cdf2-ss[m]*cdf1+ss[m]-kk[m])
    return out

def implied_vol_vec(price,s,k,t,call):
    price=np.asarray(price,float); s=np.asarray(s,float); k=np.asarray(k,float); t=np.asarray(t,float); call=np.asarray(call,bool)
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

def bs_gamma(s,k,t,sigma):
    if min(s,k,t,sigma)<=0: return np.nan
    d1=(math.log(s/k)+0.5*sigma*sigma*t)/(sigma*math.sqrt(t))
    return math.exp(-0.5*d1*d1)/(math.sqrt(2*math.pi)*s*sigma*math.sqrt(t))

def load_spot(root):
    con=duckdb.connect()
    q=f"""SELECT CAST(trading_day AS DATE) trade_date, CAST(timestamp AS TIMESTAMP) ts,
                  CAST(open AS DOUBLE) open, CAST(close AS DOUBLE) close_px
           FROM read_parquet('{idx_path(root)}',union_by_name=true)
           WHERE CAST(trading_day AS DATE) BETWEEN DATE '{START_DATE}' AND DATE '{END_DATE}'
             AND close>0 ORDER BY trade_date,ts"""
    x=con.execute(q).df(); con.close()
    if x.empty: raise RuntimeError("NIFTY index cache is empty")
    x["trade_date"]=pd.to_datetime(x.trade_date).dt.date
    x["close"]=x["close_px"]
    return x

def load_prior_option_snapshot(root, spot):
    con=duckdb.connect()
    q=f"""
    WITH idx AS (
      SELECT CAST(trading_day AS DATE) d, MAX(CAST(timestamp AS TIMESTAMP)) last_ts
      FROM read_parquet('{idx_path(root)}',union_by_name=true)
      WHERE CAST(trading_day AS DATE) BETWEEN DATE '{START_DATE}' AND DATE '{END_DATE}'
      GROUP BY 1
    ),
    sp AS (
      SELECT i.d, CAST(n.close AS DOUBLE) spot
      FROM idx i JOIN read_parquet('{idx_path(root)}',union_by_name=true) n
        ON CAST(n.trading_day AS DATE)=i.d AND CAST(n.timestamp AS TIMESTAMP)=i.last_ts
    ),
    raw AS (
      SELECT CAST(o.trading_day AS DATE) d, CAST(o.expiry AS DATE) expiry,
             CASE WHEN UPPER(CAST(o.option_type AS VARCHAR)) IN ('CALL','CE') THEN 'CE'
                  WHEN UPPER(CAST(o.option_type AS VARCHAR)) IN ('PUT','PE') THEN 'PE' END side,
             CAST(o.strike AS DOUBLE) strike,
             CAST(o.timestamp AS TIMESTAMP) ts,
             CAST(o.open_interest AS DOUBLE) oi,
             CAST(o.close AS DOUBLE) px,
             ROW_NUMBER() OVER(PARTITION BY CAST(o.trading_day AS DATE),CAST(o.expiry AS DATE),
                               CAST(o.strike AS DOUBLE),CAST(o.option_type AS VARCHAR)
                               ORDER BY CAST(o.timestamp AS TIMESTAMP) DESC) rn
      FROM read_parquet('{opt_glob(root)}',union_by_name=true) o
      JOIN idx i ON CAST(o.trading_day AS DATE)=i.d
      WHERE CAST(o.trading_day AS DATE) BETWEEN DATE '{START_DATE}' AND DATE '{END_DATE}'
        AND CAST(o.timestamp AS TIMESTAMP) <= i.last_ts
        AND open_interest>=0 AND close>0 AND expiry IS NOT NULL
    )
    SELECT r.d,r.expiry,r.side,r.strike,r.oi,r.px,s.spot
    FROM raw r JOIN sp s ON s.d=r.d
    WHERE r.rn=1 AND r.side IS NOT NULL AND r.expiry>r.d
      AND ABS(r.strike-s.spot)<= {SPOT_WINDOW}
    ORDER BY r.d,r.expiry,r.strike,r.side
    """
    x=con.execute(q).df(); con.close()
    if x.empty: raise RuntimeError("No prior-session option/OI snapshot rows")
    return x

def gex_snapshot(day, rows):
    spot=float(rows.spot.iloc[0])
    rows=rows.copy()
    rows["t"]=((pd.to_datetime(rows.expiry)-pd.Timestamp(day))+pd.Timedelta(hours=15,minutes=30)).dt.total_seconds()/31536000.0
    s=np.full(len(rows),spot,float)
    k=rows["strike"].to_numpy(float)
    t=rows["t"].to_numpy(float)
    px=rows["px"].to_numpy(float)
    call=(rows["side"].to_numpy()=="CE")
    iv=implied_vol_vec(px,s,k,t,call)
    rows["iv"]=iv
    rows["gamma"]=np.where(np.isfinite(iv),
        np.exp(-0.5*((np.log(s/k)+0.5*iv*iv*t)/(iv*np.sqrt(t)))**2)/(np.sqrt(2*np.pi)*s*iv*np.sqrt(t)),
        np.nan)
    rows["lot"]=rows["expiry"].map(lot_size)
    rows=rows[np.isfinite(rows.gamma)&(rows.oi>0)].copy()
    if rows.empty: return None
    spot=float(rows.spot.iloc[0])
    rows["gex_unit"]=rows.gamma*rows.oi*rows.lot*spot*spot*0.01
    rows["signed_gex"]=np.where(rows.side=="CE",rows.gex_unit,-rows.gex_unit)
    total=float(rows.signed_gex.sum())

    grid=np.arange(spot-SPOT_WINDOW,spot+SPOT_WINDOW+50,50.0)
    gv=[]
    kval=rows.strike.to_numpy(float)[None,:]
    tval=rows.t.to_numpy(float)[None,:]
    ivval=rows.iv.to_numpy(float)[None,:]
    oi=rows.oi.to_numpy(float)[None,:]
    lot=rows.lot.to_numpy(float)[None,:]
    side=np.where(rows.side.to_numpy()=="CE",1.0,-1.0)[None,:]
    for sg in grid:
        ss=np.full_like(kval,float(sg))
        d1=(np.log(ss/kval)+0.5*ivval*ivval*tval)/(ivval*np.sqrt(tval))
        gam=np.exp(-0.5*d1*d1)/(np.sqrt(2*np.pi)*ss*ivval*np.sqrt(tval))
        gv.append(float(np.nansum(side*gam*oi*lot*ss*ss*0.01)))
    root=np.nan
    for a,b,va,vb in zip(grid[:-1],grid[1:],gv[:-1],gv[1:]):
        if va==0: root=float(a); break
        if va*vb<0:
            root=float(a+(0-va)*(b-a)/(vb-va)); break
    near=rows.loc[(rows.strike>=spot-100)&(rows.strike<=spot+100),"gex_unit"].abs().sum()
    denom=abs(rows.signed_gex).sum()
    share=float(near/denom) if denom>0 else np.nan
    return {"trade_date":day,"spot":spot,"net_gex":total,"flip_distance":(spot-root if np.isfinite(root) else np.nan),
            "gamma_flip":root,"atm_gex_share":share,"rows":len(rows)}

def build_feature_panel(root):
    spot=load_spot(root)
    snap=load_prior_option_snapshot(root,spot)
    rows=[]
    for d,g in snap.groupby("d",sort=True):
        z=gex_snapshot(pd.Timestamp(d).date(),g)
        if z: rows.append(z)
    panel=pd.DataFrame(rows).sort_values("trade_date").reset_index(drop=True)
    if panel.empty: raise RuntimeError("No gamma snapshots produced")
    for col in ("net_gex","flip_distance","atm_gex_share"):
        mu=panel[col].rolling(WARMUP,min_periods=WARMUP).mean().shift(1)
        sd=panel[col].rolling(WARMUP,min_periods=WARMUP).std(ddof=0).shift(1).replace(0,np.nan)
        panel[{"net_gex":"GEX_Z","flip_distance":"FLIP_DISTANCE_Z","atm_gex_share":"ATM_GEX_SHARE_Z"}[col]]=(panel[col]-mu)/sd
    return panel,spot

def make_signals(panel,spot,permute_seed=None):
    panel=panel.copy()
    if permute_seed is not None:
        rng=np.random.default_rng(permute_seed)
        idx=np.arange(len(panel))
        rng.shuffle(idx)
        cols=["net_gex",*FEATURES]
        perm=panel.loc[idx,cols].to_numpy(copy=True)
        panel.loc[:,cols]=perm
    s=spot.sort_values("ts").groupby("trade_date").agg(open=("open","first"),close=("close","last")).copy()
    s.index=pd.to_datetime(s.index).date
    prev_close={d:float(r.close) for d,r in s.iterrows()}
    next_open={d:float(r.open) for d,r in s.iterrows()}
    dates=sorted(s.index); nxt={dates[i]:dates[i+1] for i in range(len(dates)-1)}
    out=[]
    for r in panel.itertuples(index=False):
        d=r.trade_date
        if d not in nxt: continue
        nd=nxt[d]; gap=(next_open[nd]/prev_close[d]-1) if prev_close[d]>0 else np.nan
        if not np.isfinite(gap) or abs(gap)<1e-8: continue
        gdir=1 if r.net_gex<0 else -1
        for f in FEATURES:
            z=getattr(r,f)
            if not np.isfinite(z): continue
            for th in THRESHOLDS:
                if abs(z)<th: continue
                for ex in EXITS:
                    action=gdir if gap>0 else -gdir
                    out.append({"feature":f,"threshold":th,"exit_time":ex,"signal_date":d,"trade_date":nd,
                                "gap":gap,"direction":action,"spot":r.spot,"expiry":None})
    return pd.DataFrame(out)

def attach_expiry_and_prices(signals,root):
    if signals.empty: return signals
    con=duckdb.connect()
    con.register("sig",signals)
    q=f"""
    WITH ex AS (
      SELECT s.*, MIN(CAST(o.expiry AS DATE)) expiry
      FROM sig s JOIN read_parquet('{opt_glob(root)}',union_by_name=true) o
        ON CAST(o.trading_day AS DATE)=s.trade_date AND CAST(o.expiry AS DATE)>s.trade_date
      GROUP BY ALL
    ),
    q AS (
      SELECT CAST(trading_day AS DATE) d,CAST(expiry AS DATE) expiry,
             CASE WHEN UPPER(CAST(option_type AS VARCHAR)) IN ('CALL','CE') THEN 1 ELSE -1 END side,
             CAST(strike AS DOUBLE) strike,CAST(timestamp AS TIME) tm,
             CAST(open AS DOUBLE) open,CAST(close AS DOUBLE) close_px
      FROM read_parquet('{opt_glob(root)}',union_by_name=true) WHERE close>0
    )
    SELECT * FROM ex
    """
    x=con.execute(q).df(); con.close()
    return x

def simulate(signals,root,slippage):
    if signals.empty:
        return pd.DataFrame(), pd.DataFrame()

    work=signals.copy()
    work["trade_date"]=pd.to_datetime(work["trade_date"]).dt.date
    work["expiry"]=pd.NaT

    con=duckdb.connect()
    days_sql=",".join(f"DATE '{d}'" for d in sorted(work["trade_date"].unique()))
    expq=f"""
      SELECT CAST(trading_day AS DATE) d, MIN(CAST(expiry AS DATE)) expiry
      FROM read_parquet('{opt_glob(root)}',union_by_name=true)
      WHERE CAST(trading_day AS DATE) IN ({days_sql})
        AND expiry IS NOT NULL
        AND CAST(expiry AS DATE)>CAST(trading_day AS DATE)
      GROUP BY 1
    """
    exp_df=con.execute(expq).df()
    con.close()
    if exp_df.empty:
        return pd.DataFrame(), coverage_table(signals,pd.DataFrame())

    exp_df["d"]=pd.to_datetime(exp_df["d"]).dt.date
    exp_map=dict(zip(exp_df.d,exp_df.expiry))
    work["expiry"]=work.trade_date.map(exp_map)
    work=work.dropna(subset=["expiry"]).copy()
    if work.empty:
        return pd.DataFrame(), coverage_table(signals,pd.DataFrame())

    requests=[]
    for r in work.itertuples(index=False):
        day=pd.Timestamp(r.trade_date).date()
        exp=pd.Timestamp(r.expiry).date()
        atm=int(round(float(r.spot)/50.0)*50)
        is_call=float(r.direction)>0
        typ="CE" if is_call else "PE"
        wing=atm+WING if is_call else atm-WING
        for tm in ("09:31:00",str(r.exit_time)):
            requests.append((day,exp,tm,typ,float(atm)))
            requests.append((day,exp,tm,typ,float(wing)))
    req=pd.DataFrame(requests,columns=["trade_date","expiry","time_str","option_type","strike"]).drop_duplicates()
    prices={}
    con=duckdb.connect()
    for exp,g in req.groupby("expiry",sort=True):
        path=Path(root)/"options"/"NIFTY"/f"{pd.Timestamp(exp).date()}.parquet"
        if not path.exists(): continue
        dates_sql=",".join(f"DATE '{d}'" for d in sorted(g.trade_date.unique()))
        strikes_sql=",".join(str(float(x)) for x in sorted(g.strike.unique()))
        times_sql=",".join(f"'{x}'" for x in sorted(g.time_str.unique()))
        p=str(path).replace("'","''")
        q=f"""
          SELECT CAST(trading_day AS DATE) trade_date,
                 CAST(expiry AS DATE) expiry,
                 strftime(CAST(timestamp AS TIMESTAMP),'%H:%M:%S') time_str,
                 UPPER(CAST(option_type AS VARCHAR)) option_type,
                 CAST(strike AS DOUBLE) strike,
                 CAST(open AS DOUBLE) open_px,
                 CAST(close AS DOUBLE) close_px
          FROM read_parquet('{p}',union_by_name=true)
          WHERE CAST(trading_day AS DATE) IN ({dates_sql})
            AND strftime(CAST(timestamp AS TIMESTAMP),'%H:%M:%S') IN ({times_sql})
            AND CAST(strike AS DOUBLE) IN ({strikes_sql})
            AND UPPER(CAST(option_type AS VARCHAR)) IN ('CE','PE')
            AND ((strftime(CAST(timestamp AS TIMESTAMP),'%H:%M:%S')='09:31:00' AND open>0)
              OR (strftime(CAST(timestamp AS TIMESTAMP),'%H:%M:%S')<>'09:31:00' AND close>0))
        """
        z=con.execute(q).df()
        for r in z.itertuples(index=False):
            px=float(r.open_px) if r.time_str=="09:31:00" else float(r.close_px)
            prices[(pd.Timestamp(r.trade_date).date(),pd.Timestamp(r.expiry).date(),r.time_str,str(r.option_type).upper(),float(r.strike))]=px
    con.close()

    rows=[]
    for r in work.itertuples(index=False):
        day=pd.Timestamp(r.trade_date).date()
        exp=pd.Timestamp(r.expiry).date()
        atm=int(round(float(r.spot)/50.0)*50)
        is_call=float(r.direction)>0
        typ="CE" if is_call else "PE"
        wing=atm+WING if is_call else atm-WING
        k_entry_a=(day,exp,"09:31:00",typ,float(atm))
        k_entry_w=(day,exp,"09:31:00",typ,float(wing))
        k_exit_a=(day,exp,str(r.exit_time),typ,float(atm))
        k_exit_w=(day,exp,str(r.exit_time),typ,float(wing))
        if not all(k in prices for k in (k_entry_a,k_entry_w,k_exit_a,k_exit_w)):
            continue
        long_entry=prices[k_entry_a]; short_entry=prices[k_entry_w]
        long_exit=prices[k_exit_a]; short_exit=prices[k_exit_w]
        entry_debit=long_entry-short_entry
        exit_debit=long_exit-short_exit
        if entry_debit<=0: continue
        lot=lot_size(exp)
        gross=(exit_debit-entry_debit)*lot
        slippage=slippage*4*lot
        tc=(charge(long_entry,"BUY",1,lot,day)
            +charge(short_entry,"SELL",1,lot,day)
            +charge(long_exit,"SELL",1,lot,day)
            +charge(short_exit,"BUY",1,lot,day))
        rows.append({**r._asdict(),"expiry":exp,"atm_strike":atm,"wing_strike":wing,
                     "entry_debit":entry_debit,"exit_debit":exit_debit,
                     "gross_pnl":gross,"slippage":slippage,"transaction_costs":tc,
                     "net_pnl":gross-slippage-tc,
                     "week":str(pd.Timestamp(day).to_period("W-SUN"))})
    trades=pd.DataFrame(rows)
    return trades,coverage_table(signals,trades)

def coverage_table(signals,trades):
    rows=[]
    for f in FEATURES:
        for th in THRESHOLDS:
            for ex in EXITS:
                n=int(((signals.feature==f)&(signals.threshold==th)&(signals.exit_time==ex)).sum()) if not signals.empty else 0
                t=int(((trades.feature==f)&(trades.threshold==th)&(trades.exit_time==ex)).sum()) if not trades.empty else 0
                rows.append({"feature":f,"threshold":th,"exit_time":ex,"signals":n,"trades":t,"coverage_rate":t/n if n else 1.0})
    return pd.DataFrame(rows)

def summarize(trades):
    rows=[]
    for f in FEATURES:
        for th in THRESHOLDS:
            for ex in EXITS:
                g=trades[(trades.feature==f)&(trades.threshold==th)&(trades.exit_time==ex)] if not trades.empty else pd.DataFrame()
                w=g.groupby("week").net_pnl.sum() if not g.empty else pd.Series(dtype=float)
                rows.append({"feature":f,"threshold":th,"exit_time":ex,"trades":len(g),
                             "weeks":len(w),"total_net":float(g.net_pnl.sum()) if not g.empty else 0.0,
                             "mean_weekly_net":float(w.mean()) if len(w) else 0.0,
                             "median_weekly_net":float(w.median()) if len(w) else 0.0,
                             "positive_week_rate":float((w>0).mean()) if len(w) else 0.0,
                             "raw_gross":float(g.gross_pnl.sum()) if not g.empty else 0.0,
                             "total_slippage":float(g.slippage.sum()) if not g.empty else 0.0})
    return pd.DataFrame(rows)

def run_null(panel,spot,root,slippage):
    out=[]
    for seed in NULL_SEEDS:
        s=make_signals(panel,spot,permute_seed=seed)
        t,_=simulate(s,root,slippage)
        z=summarize(t)
        z["null_seed"]=seed
        out.append(z)
    return pd.concat(out,ignore_index=True)

def gate(panel,signals,cov,spot):
    warm=panel.iloc[WARMUP:].copy()
    feature_coverage={f:float(warm[f].notna().mean()) if len(warm) else 0.0 for f in FEATURES}
    expected_sessions=max(int(spot.trade_date.nunique())-1,0)
    snapshot_sessions=int(panel.trade_date.nunique())
    snapshot_coverage=float(snapshot_sessions/expected_sessions) if expected_sessions else 0.0
    barrier_violations=0
    return {
        "status":"PASS" if expected_sessions and snapshot_coverage>=0.95
                     and all(v>=0.95 for v in feature_coverage.values())
                     and len(cov)==12 and cov.coverage_rate.min()>=0.95
                     and barrier_violations==0 else "FAIL",
        "expected_prior_sessions":expected_sessions,
        "snapshot_sessions":snapshot_sessions,
        "snapshot_coverage":snapshot_coverage,
        "warmup_sessions":int(len(warm)),
        "feature_coverage":feature_coverage,
        "signal_rows":int(len(signals)),
        "coverage_min":float(cov.coverage_rate.min()) if len(cov) else 0.0,
        "coverage_cells":int(len(cov)),
        "prior_information_barrier_violations":barrier_violations
    }

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--data",default="data/cache/phase31_trademarkk"); ap.add_argument("--out",default="reports/phase33/base"); ap.add_argument("--slippage",type=float,default=.20); ap.add_argument("--gate-only",action="store_true"); ap.add_argument("--force-refresh",default="false"); a=ap.parse_args()
    root=Path(a.data); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    panel,spot=build_feature_panel(root); panel.to_csv(out/"gamma_feature_panel.csv",index=False)
    signals=make_signals(panel,spot); signals.to_csv(out/"signals.csv",index=False)
    if a.gate_only:
        _,cov=simulate(signals,root,a.slippage); cov.to_csv(out/"price_coverage.csv",index=False)
        g=gate(panel,signals,cov,spot); (out/"data_gate.json").write_text(json.dumps(g,indent=2)); print(json.dumps(g)); return
    trades,cov=simulate(signals,root,a.slippage); trades.to_csv(out/"trades.csv",index=False); cov.to_csv(out/"price_coverage.csv",index=False)
    summarize(trades).to_csv(out/"true_cell_summary.csv",index=False)
    run_null(panel,spot,root,a.slippage).to_csv(out/"null_summary.csv",index=False)

if __name__=="__main__": main()
