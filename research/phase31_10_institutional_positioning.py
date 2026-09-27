#!/usr/bin/env python3
from pathlib import Path
import argparse, json
from datetime import date
import duckdb
import numpy as np
import pandas as pd

from research.phase31_7_oi_volume_microstructure import lot_size, charge, price_key

START=date(2021,7,1)
END=date(2026,8,31)
FEATURES=("FII_IDX_NET_Z","DII_IDX_NET_Z","FII_DII_DIVERGENCE_Z")
THRESHOLDS=(0.50,1.00)
HORIZONS=("H10_30","H15_10")
HORIZON_TIMES={"H10_30":"10:30:00","H15_10":"15:10:00"}
NULL_SEEDS=(101,202,303,404,505)
WING=200

def load_nifty(root:Path)->pd.DataFrame:
    con=duckdb.connect()
    q=f"""
      SELECT CAST(timestamp AS TIMESTAMP) ts,
             CAST(open AS DOUBLE) open_px,
             CAST(close AS DOUBLE) close_px
      FROM read_parquet('{str(root/'index/NIFTY.parquet').replace("'","''")}')
      WHERE CAST(timestamp AS DATE) BETWEEN DATE '{START}' AND DATE '{END}'
      ORDER BY ts
    """
    x=con.execute(q).df(); con.close()
    x.ts=pd.to_datetime(x.ts)
    x["date"]=x.ts.dt.date
    x["time"]=x.ts.dt.strftime("%H:%M:%S")
    return x.drop_duplicates("ts")

def feature_panel(nifty:pd.DataFrame, oi:pd.DataFrame)->pd.DataFrame:
    s=nifty[nifty.time=="09:30:00"][["date","open_px","close_px"]].drop_duplicates("date").sort_values("date").copy()
    prev_close=nifty[nifty.time=="15:10:00"][["date","close_px"]].drop_duplicates("date").sort_values("date").rename(columns={"close_px":"prev_close"})
    # previous completed NIFTY close for the opening gap
    s=s.merge(prev_close,left_on=s["date"].map(lambda d: d),right_on=prev_close["date"],how="left").drop(columns=["key_0"],errors="ignore") if False else s
    close_by_date=prev_close.set_index("date")["prev_close"]
    s["prev_close"]=s["date"].map(close_by_date.shift(1))
    s["gap_pct"]=(s["open_px"]-s["prev_close"])/s["prev_close"]

    oi=oi.copy()
    oi["trade_date"]=pd.to_datetime(oi["trade_date"]).dt.date
    piv=oi.pivot_table(index="trade_date",columns="participant",values="idx_net_ratio",aggfunc="first")
    for p in ("FII","DII"):
        if p not in piv: piv[p]=np.nan
    raw=piv[["FII","DII"]].rename(columns={"FII":"fii_raw","DII":"dii_raw"}).sort_index()
    raw["div_raw"]=raw["fii_raw"]-raw["dii_raw"]
    # Positioning used for NIFTY date t is t-1; no current-day positioning.
    s["position_date"]=s["date"].map(lambda d: pd.Timestamp(d).date()-pd.Timedelta(days=1))
    # map to the latest participant report strictly before the trade date
    pos=raw.reset_index().rename(columns={"trade_date":"position_date"})
    pos["position_date"]=pd.to_datetime(pos["position_date"])
    left=pd.DataFrame({"date":pd.to_datetime(s["date"])})
    left=left.sort_values("date")
    left=pd.merge_asof(left,pos.sort_values("position_date"),left_on="date",right_on="position_date",
                       direction="backward",allow_exact_matches=False)
    left["position_date"]=left["position_date"].dt.date
    s=s.reset_index(drop=True)
    left=left.reset_index(drop=True)
    s["position_date"]=left["position_date"]
    s["fii_raw"]=left["fii_raw"]
    s["dii_raw"]=left["dii_raw"]
    s["div_raw"]=left["div_raw"]

    for raw_col, zcol in [("fii_raw","FII_IDX_NET_Z"),("dii_raw","DII_IDX_NET_Z"),("div_raw","FII_DII_DIVERGENCE_Z")]:
        prior=s[raw_col].shift(1)
        mu=prior.rolling(60,min_periods=60).mean()
        sd=prior.rolling(60,min_periods=60).std(ddof=1)
        s[zcol]=(s[raw_col]-mu)/sd
    s["feature_eligible"]=s[list(FEATURES)].notna().all(axis=1)
    s["barrier_ok"]=s["position_date"].notna() & (pd.to_datetime(s["position_date"]) < pd.to_datetime(s["date"]))
    return s

def data_gate(panel:pd.DataFrame, manifest:dict)->dict:
    raw_sessions=len(panel)
    eligible=int(panel.feature_eligible.sum())
    complete=int(panel[panel.feature_eligible].notna().all(axis=1).sum()) if eligible else 0
    barrier_violations=int((~panel.barrier_ok & panel.feature_eligible).sum())
    missing_files=len(manifest.get("missing_files",[]))
    return {
        "status":"PASS" if eligible and complete/eligible>=0.95 and barrier_violations==0 else "FAIL",
        "raw_nifty_sessions":raw_sessions,
        "feature_eligible_sessions":eligible,
        "complete_feature_sessions":complete,
        "feature_coverage":float(complete/eligible) if eligible else 0.0,
        "required_feature_coverage":0.95,
        "prior_barrier_violations":barrier_violations,
        "participant_missing_file_count":missing_files,
        "study_start":str(START),"study_end":str(END),
        "source_manifest":manifest,
    }

def expiry_files(root:Path):
    out={}
    for p in sorted((root/"options/NIFTY").glob("*.parquet")):
        try: out[pd.Timestamp(p.stem).date()]=p
        except Exception: pass
    return out

def attach_expiry(panel, expiry_map):
    x=panel.copy(); exps=sorted(expiry_map); ys=[]
    for d in x["date"]:
        dd=pd.Timestamp(d).date()
        ys.append(next((e for e in exps if e>=dd),None))
    x["expiry"]=ys
    x["atm"]=(x["open_px"]/50.0).round()*50
    return x

def build_signals(panel, null_seed=None):
    x=panel.copy()
    if null_seed is not None:
        rng=np.random.default_rng(null_seed)
        for f in FEATURES:
            vals=x[f].to_numpy(copy=True); rng.shuffle(vals); x[f]=vals
    out=[]
    for f in FEATURES:
        for th in THRESHOLDS:
            for h in HORIZONS:
                z=x[x[f].abs()>=th].copy()
                if z.empty: continue
                z["feature"]=f; z["threshold"]=th; z["horizon"]=h
                z["signal_value"]=z[f]
                z["side"]=np.where(z["signal_value"]>0,"CALL","PUT")
                out.append(z)
    return pd.concat(out,ignore_index=True) if out else pd.DataFrame()

def load_prices(root, expiry_map, signals):
    prices={}; con=duckdb.connect(); con.execute("SET TimeZone='Asia/Kolkata'")
    if signals.empty: con.close(); return prices
    sig=signals.copy(); sig["expiry_key"]=pd.to_datetime(sig["expiry"]).dt.date
    for expiry,path in sorted(expiry_map.items()):
        a=sig[sig.expiry_key==expiry]
        if a.empty: continue
        dates=sorted(pd.to_datetime(a.date).dt.date.unique().tolist())
        date_sql=",".join(f"DATE '{d}'" for d in dates)
        strikes=sorted(set(float(v) for v in a.atm)|set(float(v)+WING for v in a.atm)|set(float(v)-WING for v in a.atm))
        strike_sql=",".join(str(v) for v in strikes)
        htimes=",".join(f"'{v}'" for v in HORIZON_TIMES.values())
        p=str(path).replace("'","''")
        q=f"""
        WITH src AS (
          SELECT CAST(o.timestamp AS TIMESTAMP) ts,
                 CAST(CAST(o.timestamp AS TIMESTAMP) AS DATE) trade_date,
                 strftime(CAST(o.timestamp AS TIMESTAMP),'%H:%M:%S') local_time,
                 UPPER(CAST(o.option_type AS VARCHAR)) option_type,
                 CAST(o.strike AS DOUBLE) strike,
                 CAST(o.open AS DOUBLE) open_px,
                 CAST(o.close AS DOUBLE) close_px
          FROM read_parquet('{p}') o
        )
        SELECT * FROM src
        WHERE trade_date IN ({date_sql})
          AND strike IN ({strike_sql})
          AND option_type IN ('CE','PE')
          AND local_time IN ('09:31:00',{htimes})
          AND ((local_time='09:31:00' AND open_px>0)
            OR (local_time IN ({",".join("'"+v+"'" for v in HORIZON_TIMES.values())}) AND close_px>0))
        """
        z=con.execute(q).df()
        for r in z.itertuples(index=False):
            px=float(r.open_px) if r.local_time=="09:31:00" else float(r.close_px)
            prices[price_key(r.trade_date,expiry,r.option_type,float(r.strike),pd.Timestamp(r.ts))]=px
    con.close(); return prices

def trade_from_signal(r,prices,slip):
    d=pd.Timestamp(r.date).date(); expiry=pd.Timestamp(r.expiry).date(); atm=int(r.atm)
    typ="CE" if r.side=="CALL" else "PE"
    wing=atm+WING if r.side=="CALL" else atm-WING
    entry=pd.Timestamp(f"{d} 09:31:00"); exit_ts=pd.Timestamp(f"{d} {HORIZON_TIMES[r.horizon]}")
    lot=lot_size(expiry); raw=execgross=slipcost=tc=0.0
    for opt,strike,action in [(typ,atm,"BUY"),(typ,wing,"SELL")]:
        ep=prices.get(price_key(d,expiry,opt,float(strike),entry)); xp=prices.get(price_key(d,expiry,opt,float(strike),exit_ts))
        if ep is None or xp is None: return None
        if action=="BUY":
            ee=ep+slip; xx=max(0,xp-slip); rp=(xp-ep)*lot; epnl=(xx-ee)*lot; exit_action="SELL"
        else:
            ee=max(0,ep-slip); xx=xp+slip; rp=(ep-xp)*lot; epnl=(ee-xx)*lot; exit_action="BUY"
        raw+=rp; execgross+=epnl; slipcost+=rp-epnl
        tc+=charge(ee,action,1,lot,d)+charge(xx,exit_action,1,lot,d)
    gap=float(r.gap_pct) if pd.notna(r.gap_pct) else np.nan
    gap_align = ("ALIGNED" if ((r.signal_value>0 and gap>0) or (r.signal_value<0 and gap<0))
                 else "OPPOSED" if ((r.signal_value>0 and gap<0) or (r.signal_value<0 and gap>0))
                 else "FLAT")
    return {"day":str(d),"position_date":str(pd.Timestamp(r.position_date).date()),
            "feature":r.feature,"threshold":float(r.threshold),"horizon":r.horizon,"side":r.side,
            "gap_pct":gap,"gap_alignment":gap_align,
            "friction":"base" if slip==0.20 else "stress",
            "raw_gross":raw,"execution_gross":execgross,"slippage_cost":slipcost,
            "transaction_costs":tc,"net_pnl":execgross-tc}

def summary(trades):
    rows=[]
    for f in FEATURES:
        for th in THRESHOLDS:
            for h in HORIZONS:
                g=trades[(trades.feature==f)&(trades.threshold==th)&(trades.horizon==h)] if not trades.empty else trades.iloc[0:0]
                if g.empty:
                    rows.append({"feature":f,"threshold":th,"horizon":h,"friction":None,"trades":0,"weeks":0,"total_net":0.0,"mean_weekly_net":0.0,"median_weekly_net":0.0,"positive_week_rate":0.0,"worst_trade":np.nan,"worst_week":np.nan,"max_drawdown":np.nan,"raw_gross":0.0,"total_slippage":0.0,"total_transaction_costs":0.0})
                    continue
                wk=g.assign(week=pd.to_datetime(g.day).dt.to_period("W-SUN").astype(str)).groupby("week").net_pnl.sum()
                eq=wk.sort_index().cumsum(); dd=eq-eq.cummax()
                rows.append({"feature":f,"threshold":th,"horizon":h,"friction":g.friction.iloc[0],"trades":len(g),"weeks":len(wk),
                             "total_net":g.net_pnl.sum(),"mean_weekly_net":wk.mean(),"median_weekly_net":wk.median(),
                             "positive_week_rate":(wk>0).mean(),"worst_trade":g.net_pnl.min(),"worst_week":wk.min(),
                             "max_drawdown":dd.min(),"raw_gross":g.raw_gross.sum(),"total_slippage":g.slippage_cost.sum(),
                             "total_transaction_costs":g.transaction_costs.sum()})
    return pd.DataFrame(rows)

def null_summary(trades):
    rows=[]
    for seed in NULL_SEEDS:
        g=trades[trades.null_seed==seed] if not trades.empty else trades.iloc[0:0]
        q=summary(g); q.insert(1,"null_seed",seed); rows.append(q)
    return pd.concat(rows,ignore_index=True) if rows else pd.DataFrame()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--data",default="data/cache/phase31_trademarkk")
    ap.add_argument("--institutional",default="data/cache/phase31_10_institutional/participant_oi_normalized.parquet")
    ap.add_argument("--manifest",default="data/cache/phase31_10_institutional/manifest.json")
    ap.add_argument("--out",default="reports/phase31_10")
    ap.add_argument("--slippage",type=float,default=0.20)
    ap.add_argument("--gate-only",action="store_true")
    args=ap.parse_args()
    root=Path(args.data); out=Path(args.out); out.mkdir(parents=True,exist_ok=True)
    nifty=load_nifty(root); oi=pd.read_parquet(args.institutional)
    manifest=json.loads(Path(args.manifest).read_text()) if Path(args.manifest).exists() else {}
    panel=feature_panel(nifty,oi)
    gate=data_gate(panel,manifest)
    panel.to_csv(out/"feature_panel.csv",index=False)
    (out/"data_gate.json").write_text(json.dumps(gate,indent=2,default=str),encoding="utf-8")
    if args.gate_only or gate["status"]!="PASS":
        print(json.dumps(gate,indent=2,default=str)); return
    expiry_map=expiry_files(root); panel=attach_expiry(panel,expiry_map)
    panel=panel.dropna(subset=["expiry","atm"])
    sig=build_signals(panel); sig.to_csv(out/"true_signals.csv",index=False)
    prices=load_prices(root,expiry_map,sig)
    cov=[]
    for key,g in sig.groupby(["feature","threshold","horizon"]):
        complete=0
        for r in g.itertuples(index=False):
            d=pd.Timestamp(r.date).date(); e=pd.Timestamp(r.expiry).date(); typ="CE" if r.side=="CALL" else "PE"; wing=r.atm+(WING if r.side=="CALL" else -WING)
            req=[(typ,r.atm,pd.Timestamp(f"{d} 09:31:00")),(typ,r.atm,pd.Timestamp(f"{d} {HORIZON_TIMES[r.horizon]}")),(typ,wing,pd.Timestamp(f"{d} 09:31:00")),(typ,wing,pd.Timestamp(f"{d} {HORIZON_TIMES[r.horizon]}"))]
            complete+=int(all(price_key(d,e,o,float(k),ts) in prices for o,k,ts in req))
        cov.append({"feature":key[0],"threshold":float(key[1]),"horizon":key[2],"signals":len(g),"complete_price_coverage":complete,"coverage_rate":complete/len(g) if len(g) else 0.0})
    pd.DataFrame(cov).to_csv(out/"price_coverage.csv",index=False)
    for friction,slip in (("base",0.20),("stress",0.40)):
        rows=[]
        for r in sig.itertuples(index=False):
            t=trade_from_signal(r,prices,slip)
            if t: rows.append(t)
        td=pd.DataFrame(rows)
        td.to_csv(out/f"trades_{friction}.csv",index=False)
        summary(td).to_csv(out/f"true_cell_summary_{friction}.csv",index=False)
        td.assign(week=pd.to_datetime(td.day).dt.to_period("W-SUN").astype(str)).groupby(["feature","threshold","horizon","friction","week"],as_index=False).net_pnl.sum().to_csv(out/f"weekly_{friction}.csv",index=False)
        null_rows=[]
        for seed in NULL_SEEDS:
            ns=build_signals(panel,null_seed=seed)
            for r in ns.itertuples(index=False):
                t=trade_from_signal(r,prices,slip)
                if t: t["null_seed"]=seed; null_rows.append(t)
        nd=pd.DataFrame(null_rows)
        nd.to_csv(out/f"null_trades_{friction}.csv",index=False)
        null_summary(nd).to_csv(out/f"null_summary_{friction}.csv",index=False)
    print(json.dumps(gate,indent=2,default=str))

if __name__=="__main__":
    main()
