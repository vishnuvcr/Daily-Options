#!/usr/bin/env python3
from pathlib import Path
import argparse,json
import numpy as np,pandas as pd
from research.phase31_8_global_overnight_transmission import (
    START,END,MARKETS,load_index,load_global,build_panel,data_gate,expiry_files,
)
from research.phase31_7_oi_volume_microstructure import lot_size,charge,price_key
THRESHOLDS=(1.0,1.5)
STRUCTURES=("STRADDLE","STRANGLE")
HORIZONS=("H10_30","H15_10")
HORIZON_TIMES={"H10_30":"10:30:00","H15_10":"15:10:00"}
FEATURES=("GLOBAL_ABS","US_ASIA_DISPERSION")
NULL_SEEDS=(101,202,303,404,505)
WING=200

def enrich(panel):
    x=panel.copy()
    x["GLOBAL_ABS"]=x["GLOBAL_LEAD"].abs()
    x["US_ASIA_DISPERSION"]=(x["US_LEAD"]-x["ASIA_LEAD"]).abs()
    return x

def build_signals(panel,null_seed=None):
    x=panel.copy()
    if null_seed is not None:
        rng=np.random.default_rng(null_seed)
        for f in FEATURES:
            v=x[f].to_numpy(copy=True); rng.shuffle(v); x[f]=v
    rows=[]
    for f in FEATURES:
        for t in THRESHOLDS:
            for s in STRUCTURES:
                for h in HORIZONS:
                    z=x[x[f]>=t].copy()
                    z["feature"]=f; z["threshold"]=t; z["structure"]=s; z["horizon"]=h
                    rows.append(z)
    return pd.concat(rows,ignore_index=True) if rows else pd.DataFrame()

def attach(panel,expiry_map):
    x=panel.copy(); x["date"]=pd.to_datetime(x.date).dt.normalize()
    exps=sorted(expiry_map); x["expiry"]=[next((e for e in exps if e>=pd.Timestamp(d).date()),None) for d in x.date]
    x["atm"]=(x.open_px/50).round()*50
    return x.dropna(subset=["expiry","atm"])

def load_prices(root,expiry_map,signals):
    import duckdb
    prices={}; con=duckdb.connect(); con.execute("SET TimeZone='Asia/Kolkata'")
    for e,pth in sorted(expiry_map.items()):
        a=signals[pd.to_datetime(signals.expiry).dt.date==e]
        if a.empty: continue
        dates=",".join("DATE '%s'"%d for d in sorted(pd.to_datetime(a.date).dt.date.unique()))
        strikes=set()
        for r in a.itertuples():
            strikes.add(float(r.atm))
            strikes.add(float(r.atm)-WING); strikes.add(float(r.atm)+WING)
        ss=",".join(str(x) for x in sorted(strikes)); p=str(pth).replace("'","''")
        q=f"""SELECT CAST(o.timestamp AS TIMESTAMP) ts,CAST(CAST(o.timestamp AS TIMESTAMP) AS DATE) trade_date,
        strftime(CAST(o.timestamp AS TIMESTAMP),'%H:%M:%S') local_time,UPPER(CAST(o.option_type AS VARCHAR)) option_type,
        CAST(o.strike AS DOUBLE) strike,CAST(o.open AS DOUBLE) open_px,CAST(o.close AS DOUBLE) close_px
        FROM read_parquet('{p}') o WHERE CAST(CAST(o.timestamp AS TIMESTAMP) AS DATE) IN ({dates})
        AND CAST(o.strike AS DOUBLE) IN ({ss}) AND UPPER(CAST(o.option_type AS VARCHAR)) IN ('CE','PE')
        AND strftime(CAST(o.timestamp AS TIMESTAMP),'%H:%M:%S') IN ('09:31:00','10:30:00','15:10:00')"""
        for r in con.execute(q).df().itertuples():
            px=float(r.open_px) if r.local_time=="09:31:00" else float(r.close_px)
            if px>0: prices[price_key(r.trade_date,e,r.option_type,float(r.strike),pd.Timestamp(r.ts))]=px
    con.close(); return prices

def trade(r,prices,slip):
    d=pd.Timestamp(r.date).date(); e=pd.Timestamp(r.expiry).date(); atm=float(r.atm)
    if r.structure=="STRADDLE": legs=[("CE",atm,"BUY"),("PE",atm,"BUY")]
    else: legs=[("CE",atm+WING,"BUY"),("PE",atm-WING,"BUY")]
    ex=HORIZON_TIMES[r.horizon]; lot=lot_size(e); raw=eg=tc=0.0; sc=0.0
    for typ,k,act in legs:
        ep=prices.get(price_key(d,e,typ,k,pd.Timestamp(f"{d} 09:31:00")))
        xp=prices.get(price_key(d,e,typ,k,pd.Timestamp(f"{d} {ex}")))
        if ep is None or xp is None: return None
        ee=ep+slip; xx=max(0,xp-slip); raw+=(xp-ep)*lot; eg+=(xx-ee)*lot; sc+=((xp-ep)-(xx-ee))*lot
        tc+=charge(ee,"BUY",1,lot,d)+charge(xx,"SELL",1,lot,d)
    return dict(day=str(d),expiry=str(e),feature=r.feature,threshold=float(r.threshold),structure=r.structure,horizon=r.horizon,
                friction="base" if slip==.20 else "stress",raw_gross=raw,execution_gross=eg,slippage_cost=sc,transaction_costs=tc,net_pnl=eg-tc)

def summarize(td):
    rows=[]
    for f in FEATURES:
      for t in THRESHOLDS:
       for s in STRUCTURES:
        for h in HORIZONS:
         g=td[(td.feature==f)&(td.threshold==t)&(td.structure==s)&(td.horizon==h)]
         if g.empty: continue
         wk=g.assign(week=pd.to_datetime(g.day).dt.to_period("W-SUN").astype(str)).groupby("week").net_pnl.sum()
         eq=wk.sort_index().cumsum(); dd=eq-eq.cummax()
         rows.append(dict(feature=f,threshold=t,structure=s,horizon=h,friction=g.friction.iloc[0],trades=len(g),weeks=len(wk),
             total_net=g.net_pnl.sum(),mean_weekly_net=wk.mean(),median_weekly_net=wk.median(),positive_week_rate=(wk>0).mean(),
             worst_trade=g.net_pnl.min(),worst_week=wk.min(),max_drawdown=dd.min(),total_slippage=g.slippage_cost.sum(),
             total_transaction_costs=g.transaction_costs.sum(),raw_gross=g.raw_gross.sum()))
    return pd.DataFrame(rows)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--data",default="data/cache/phase31_trademarkk"); ap.add_argument("--global-data",default="data/cache/phase31_8_global")
    ap.add_argument("--out",default="reports/phase35"); ap.add_argument("--slippage",type=float,default=.20); ap.add_argument("--gate-only",action="store_true")
    a=ap.parse_args(); root=Path(a.data); gr=Path(a.global_data); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    panel=enrich(build_panel(load_global(gr),load_index(root))); gate=data_gate(panel,gr)
    gate["phase"]="35"; (out/"data_gate.json").write_text(json.dumps(gate,indent=2,default=str)); panel.to_csv(out/"feature_panel.csv",index=False)
    if a.gate_only or gate["status"]!="PASS": print(json.dumps(gate,indent=2,default=str)); return
    em=expiry_files(root); sig=build_signals(attach(panel,em)); sig.to_csv(out/"true_signals.csv",index=False); prices=load_prices(root,em,sig)
    for friction,slip in (("base",.20),("stress",.40)):
        rows=[x for r in sig.itertuples(index=False) if (x:=trade(r,prices,slip))]
        td=pd.DataFrame(rows); td.to_csv(out/f"trades_{friction}.csv",index=False); summarize(td).to_csv(out/f"true_cell_summary_{friction}.csv",index=False)
        null=[]
        for seed in NULL_SEEDS:
            for r in build_signals(attach(panel,em),seed).itertuples(index=False):
                x=trade(r,prices,slip)
                if x: x["null_seed"]=seed; null.append(x)
        nd=pd.DataFrame(null); nd.to_csv(out/f"null_trades_{friction}.csv",index=False)
        if not nd.empty:
            ns=pd.concat([summarize(nd[nd.null_seed==seed]).assign(null_seed=seed) for seed in NULL_SEEDS],ignore_index=True)
        else: ns=pd.DataFrame()
        ns.to_csv(out/f"null_summary_{friction}.csv",index=False)
    print(json.dumps(gate,indent=2,default=str))
if __name__=="__main__": main()
