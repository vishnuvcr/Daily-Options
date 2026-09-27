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
      SELECT CAST(trading_day AS DATE) d, CAST(expiry AS DATE) expiry,
             CASE WHEN UPPER(CAST(option_type AS VARCHAR)) IN ('CALL','CE') THEN 'CE'
                  WHEN UPPER(CAST(option_type AS VARCHAR)) IN ('PUT','PE') THEN 'PE' END side,
             CAST(strike AS DOUBLE) strike,
             CAST(timestamp AS TIMESTAMP) ts,
             CAST(open_interest AS DOUBLE) oi,
             CAST(close AS DOUBLE) px,
             ROW_NUMBER() OVER(PARTITION BY CAST(trading_day AS DATE),CAST(expiry AS DATE),
                               CAST(strike AS DOUBLE),CAST(option_type AS VARCHAR)
                               ORDER BY CAST(timestamp AS TIMESTAMP) DESC) rn
      FROM read_parquet('{opt_glob(root)}',union_by_name=true)
      WHERE CAST(trading_day AS DATE) BETWEEN DATE '{START_DATE}' AND DATE '{END_DATE}'
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
    ivs=[]; gs=[]
    for r in rows.itertuples(index=False):
        iv=implied_vol(float(r.px),spot,float(r.strike),float(r.t),r.side=="CE")
        ivs.append(iv)
        gs.append(bs_gamma(spot,float(r.strike),float(r.t),iv) if iv else np.nan)
    rows["iv"]=ivs; rows["gamma"]=gs
    rows=rows[np.isfinite(rows.gamma)&(rows.oi>0)].copy()
    if rows.empty: return None
    rows["lot"]=rows.expiry.map(lot_size)
    rows["gex_unit"]=rows.gamma*rows.oi*rows.lot*spot*spot*0.01
    rows["signed_gex"]=np.where(rows.side=="CE",rows.gex_unit,-rows.gex_unit)
    total=float(rows.signed_gex.sum())
    byk=rows.groupby("strike",as_index=False).signed_gex.sum().sort_values("strike")
    # zero-gamma root from the frozen chain, evaluated on a fixed 50-point grid.
    grid=np.arange(spot-SPOT_WINDOW,spot+SPOT_WINDOW+50,50.0)
    vals=[]
    for s in grid:
        z=0.0
        for r in rows.itertuples(index=False):
            gg=bs_gamma(float(s),float(r.strike),float(r.t),float(r.iv))
            z += (1 if r.side=="CE" else -1)*gg*float(r.oi)*lot_size(r.expiry)*s*s*0.01
        vals.append(z)
    root=np.nan
    for a,b,va,vb in zip(grid[:-1],grid[1:],vals[:-1],vals[1:]):
        if va==0: root=float(a); break
        if va*vb<0:
            root=float(a+(0-va)*(b-a)/(vb-va)); break
    near=rows.loc[(rows.strike>=spot-100)&(rows.strike<=spot+100),"gex_unit"].abs().sum()
    share=float(near/abs(rows.signed_gex).sum()) if abs(rows.signed_gex).sum()>0 else np.nan
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
        for f in FEATURES:
            idx=panel[f].dropna().index.to_numpy()
            vals=panel.loc[idx,f].to_numpy().copy()
            rng.shuffle(vals)
            panel.loc[idx,f]=vals
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
             CAST(open AS DOUBLE) open,CAST(close AS DOUBLE) close
      FROM read_parquet('{opt_glob(root)}',union_by_name=true) WHERE close>0
    )
    SELECT * FROM ex
    """
    x=con.execute(q).df(); con.close()
    return x

def simulate(signals,root,slippage):
    # This phase deliberately uses a fixed ATM±200 debit spread. Missing legs are dropped,
    # and coverage is reported rather than filled.
    if signals.empty: return pd.DataFrame(),pd.DataFrame()
    con=duckdb.connect()
    rows=[]
    for r in signals.itertuples(index=False):
        day=pd.Timestamp(r.trade_date).date()
        spot=float(r.spot); strike=round(spot/50)*50
        side=1 if r.direction>0 else -1
        typ="CE" if side>0 else "PE"
        wing=strike+WING if side>0 else strike-WING
        expq=f"""SELECT MIN(CAST(expiry AS DATE)) e FROM read_parquet('{opt_glob(root)}',union_by_name=true)
                 WHERE CAST(trading_day AS DATE)=DATE '{day}' AND CAST(expiry AS DATE)>DATE '{day}'"""
        exp=con.execute(expq).fetchone()[0]
        if exp is None: continue
        tm_entry=pd.Timestamp(f"{day} 09:31:00")
        tm_exit=pd.Timestamp(f"{r.trade_date} {r.exit_time}")
        q=f"""SELECT CAST(strike AS DOUBLE) strike,CAST(timestamp AS TIMESTAMP) ts,
                     CAST(open AS DOUBLE) open,CAST(close AS DOUBLE) close
              FROM read_parquet('{opt_glob(root)}',union_by_name=true)
              WHERE CAST(trading_day AS DATE)=DATE '{day}' AND CAST(expiry AS DATE)=DATE '{exp}'
                AND CAST(timestamp AS TIMESTAMP) IN (TIMESTAMP '{tm_entry}',TIMESTAMP '{tm_exit}')
                AND UPPER(CAST(option_type AS VARCHAR)) IN ({repr(typ)},{repr('CALL' if typ=='CE' else 'PUT')})
                AND CAST(strike AS DOUBLE) IN ({strike},{wing}) AND close>0"""
        qd=con.execute(q).df()
        if len(qd)<4: continue
        ent=qd[qd.ts==tm_entry].set_index("strike").open.to_dict()
        ex=qd[qd.ts==tm_exit].set_index("strike").close.to_dict()
        if strike not in ent or wing not in ent or strike not in ex or wing not in ex: continue
        debit=ent[strike]-ent[wing]
        exitv=ex[strike]-ex[wing]
        gross=(exitv-debit)*lot_size(exp)*side
        orders=4
        net=gross-slippage*orders*lot_size(exp)
        rows.append({**r._asdict(),"expiry":exp,"atm_strike":strike,"wing_strike":wing,
                     "gross_pnl":gross,"slippage":slippage*orders*lot_size(exp),
                     "net_pnl":net,"week":str(pd.Timestamp(day).to_period("W-SUN"))})
    con.close()
    trades=pd.DataFrame(rows)
    cov=[]
    for f in FEATURES:
        for th in THRESHOLDS:
            for ex in EXITS:
                n=int(((signals.feature==f)&(signals.threshold==th)&(signals.exit_time==ex)).sum()) if not signals.empty else 0
                t=int(((trades.feature==f)&(trades.threshold==th)&(trades.exit_time==ex)).sum()) if not trades.empty else 0
                cov.append({"feature":f,"threshold":th,"exit_time":ex,"signals":n,"trades":t,
                             "coverage_rate":t/n if n else 1.0})
    return trades,pd.DataFrame(cov)

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

def gate(panel,signals,cov):
    feature_ok=int(panel[["GEX_Z","FLIP_DISTANCE_Z","ATM_GEX_SHARE_Z"]].notna().any(axis=1).sum())
    return {"status":"PASS" if len(panel)>0 and feature_ok>WARMUP and len(cov)==12 and cov.coverage_rate.min()>=0.95 else "FAIL",
            "snapshot_sessions":int(len(panel)),"feature_eligible_sessions":feature_ok,
            "signal_rows":int(len(signals)),"coverage_min":float(cov.coverage_rate.min()) if len(cov) else 0.0,
            "coverage_cells":int(len(cov))}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--data",default="data/cache/phase31_trademarkk"); ap.add_argument("--out",default="reports/phase33/base"); ap.add_argument("--slippage",type=float,default=.20); ap.add_argument("--gate-only",action="store_true"); ap.add_argument("--force-refresh",default="false"); a=ap.parse_args()
    root=Path(a.data); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    panel,spot=build_feature_panel(root); panel.to_csv(out/"gamma_feature_panel.csv",index=False)
    signals=make_signals(panel,spot); signals.to_csv(out/"signals.csv",index=False)
    if a.gate_only:
        _,cov=simulate(signals,root,a.slippage); cov.to_csv(out/"price_coverage.csv",index=False)
        g=gate(panel,signals,cov); (out/"data_gate.json").write_text(json.dumps(g,indent=2)); print(json.dumps(g)); return
    trades,cov=simulate(signals,root,a.slippage); trades.to_csv(out/"trades.csv",index=False); cov.to_csv(out/"price_coverage.csv",index=False)
    summarize(trades).to_csv(out/"true_cell_summary.csv",index=False)
    run_null(panel,spot,root,a.slippage).to_csv(out/"null_summary.csv",index=False)

if __name__=="__main__": main()
