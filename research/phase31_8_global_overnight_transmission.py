#!/usr/bin/env python3
from pathlib import Path
from datetime import date
import argparse, json
import duckdb
import numpy as np
import pandas as pd

from research.phase31_7_oi_volume_microstructure import lot_size, charge, price_key

START=date(2021,7,1)
END=date(2026,8,31)
MARKETS=("GSPC","IXIC","N225","HSI","GDAXI","KS11")
FEATURES=("US_LEAD","ASIA_LEAD","GLOBAL_LEAD")
THRESHOLDS=(0.50,1.00)
HORIZONS=("H10_30","H15_10")
HORIZON_TIMES={"H10_30":"10:30:00","H15_10":"15:10:00"}
NULL_SEEDS=(101,202,303,404,505)
WING=200

def load_index(root):
    con=duckdb.connect()
    con.execute("SET TimeZone='Asia/Kolkata'")
    q=f"""SELECT CAST(timestamp AS TIMESTAMP) ts,
                 CAST(open AS DOUBLE) open_px,
                 CAST(close AS DOUBLE) close_px
          FROM read_parquet('{str(root/'index/NIFTY.parquet').replace("'","''")}')
          WHERE CAST(timestamp AS DATE) BETWEEN DATE '{START}' AND DATE '{END}'
          ORDER BY ts"""
    idx=con.execute(q).df()
    con.close()
    idx.ts=pd.to_datetime(idx.ts)
    idx["date"]=idx.ts.dt.normalize()
    idx["time"]=idx.ts.dt.strftime("%H:%M:%S")
    return idx.drop_duplicates("ts")

def load_global(root):
    out={}
    for m in MARKETS:
        p=root/f"{m}.parquet"
        if not p.exists():
            raise FileNotFoundError(p)
        df=pd.read_parquet(p)
        df["date"]=pd.to_datetime(df["date"]).dt.normalize()
        df=df.sort_values("date").drop_duplicates("date")
        r=df["close"].pct_change()
        mu=r.shift(1).rolling(60,min_periods=60).mean()
        sd=r.shift(1).rolling(60,min_periods=60).std(ddof=1)
        z=(r-mu)/sd
        out[m]=pd.DataFrame({"date":df["date"],"ret":r,"z":z})
    return out

def build_panel(global_data, nifty):
    sessions=nifty[nifty.time=="09:30:00"][["date","open_px","close_px"]].drop_duplicates("date").sort_values("date").copy()
    for m,df in global_data.items():
        g=df.dropna(subset=["z"]).sort_values("date")
        cols=g[["date","z"]].rename(columns={"date":"global_date","z":f"z_{m}"})
        sessions=pd.merge_asof(
            sessions.sort_values("date"),
            cols.sort_values("global_date"),
            left_on="date",right_on="global_date",
            direction="backward",allow_exact_matches=False
        )
        sessions[f"prior_date_{m}"]=sessions["global_date"]
        sessions=sessions.drop(columns=["global_date"])
    sessions["US_LEAD"]=sessions[[f"z_GSPC",f"z_IXIC"]].mean(axis=1)
    sessions["ASIA_LEAD"]=sessions[[f"z_N225",f"z_HSI",f"z_KS11"]].mean(axis=1)
    sessions["GLOBAL_LEAD"]=sessions[[f"z_{m}" for m in MARKETS]].mean(axis=1)
    sessions["all_global_available"]=sessions[[f"z_{m}" for m in MARKETS]].notna().all(axis=1)
    prior_cols=[f"prior_date_{m}" for m in MARKETS]
    sessions["all_prior"]=sessions[prior_cols].apply(lambda r: all(pd.notna(x) and x < sessions.loc[r.name,"date"] for x in r),axis=1)
    return sessions

def data_gate(panel, root):
    manifest=json.loads((root/"manifest.json").read_text()) if (root/"manifest.json").exists() else {}
    eligible=len(panel)
    complete=int(panel.all_global_available.sum()) if eligible else 0
    prior_ok=int(panel.all_prior.sum()) if eligible else 0
    return {
        "status":"PASS" if eligible and complete/eligible>=0.95 and prior_ok==complete else "FAIL",
        "eligible_nifty_sessions":int(eligible),
        "complete_global_feature_sessions":complete,
        "complete_global_feature_coverage":float(complete/eligible) if eligible else 0.0,
        "all_prior_sessions_ok":prior_ok==complete,
        "required_global_coverage":0.95,
        "standardization_lookback":60,
        "study_start":str(START),
        "study_end":str(END),
        "global_manifest":manifest,
    }

def expiry_files(root):
    files={}
    for p in sorted((root/"options/NIFTY").glob("*.parquet")):
        try: d=pd.Timestamp(p.stem).date()
        except Exception: continue
        files[d]=p
    return files

def build_signals(panel, null_seed=None):
    x=panel.copy()
    if null_seed is not None:
        rng=np.random.default_rng(null_seed)
        for feature in FEATURES:
            vals=x[feature].to_numpy(copy=True)
            rng.shuffle(vals)
            x[feature]=vals
    rows=[]
    for feature in FEATURES:
        for threshold in THRESHOLDS:
            for horizon in HORIZONS:
                z=x[x[feature].abs()>=threshold].copy()
                if z.empty: continue
                z["feature"]=feature
                z["threshold"]=threshold
                z["horizon"]=horizon
                z["signal_value"]=z[feature]
                z["side"]=np.where(z["signal_value"]>0,"CALL","PUT")
                rows.append(z)
    return pd.concat(rows,ignore_index=True) if rows else pd.DataFrame()

def load_prices(root, expiry_map, signals):
    prices={}
    if signals.empty: return prices
    wanted=signals[["date","atm","exit_ts","expiry"]].copy() if "expiry" in signals.columns else signals[["date","atm","exit_ts"]].copy()
    con=duckdb.connect()
    con.execute("SET TimeZone='Asia/Kolkata'")
    sig=signals.copy()
    sig["expiry_key"]=pd.to_datetime(sig["expiry"]).dt.date
    for expiry,path in sorted(expiry_map.items()):
        active=sig[sig["expiry_key"]==expiry].copy()
        if active.empty: continue
        dates=sorted(pd.to_datetime(active.date).dt.date.unique().tolist())
        date_sql=",".join(f"DATE '{d}'" for d in dates)
        strikes=sorted(set(float(x) for x in active.atm.tolist())|set(float(x)+WING for x in active.atm.tolist())|set(float(x)-WING for x in active.atm.tolist()))
        strike_sql=",".join(str(x) for x in strikes)
        horizon_times=",".join(f"TIME '{x}'" for x in HORIZON_TIMES.values())
        p=str(path).replace("'","''")
        q=f"""
        SELECT
          CAST(o.timestamp AS TIMESTAMP) ts,
          CAST(CAST(o.timestamp AS TIMESTAMP) AS DATE) trade_date,
          strftime(CAST(o.timestamp AS TIMESTAMP),'%H:%M:%S') local_time,
          UPPER(CAST(o.option_type AS VARCHAR)) option_type,
          CAST(o.strike AS DOUBLE) strike,
          CAST(o.open AS DOUBLE) open_px,
          CAST(o.close AS DOUBLE) close_px
        FROM read_parquet('{p}') o
        WHERE CAST(CAST(o.timestamp AS TIMESTAMP) AS DATE) IN ({date_sql})
          AND CAST(o.strike AS DOUBLE) IN ({strike_sql})
          AND UPPER(CAST(o.option_type AS VARCHAR)) IN ('CE','PE')
          AND CAST(CAST(o.timestamp AS TIMESTAMP) AS TIME) IN (TIME '09:31:00',{horizon_times})
          AND ((strftime(CAST(o.timestamp AS TIMESTAMP),'%H:%M:%S')='09:31:00' AND o.open>0)
            OR (strftime(CAST(o.timestamp AS TIMESTAMP),'%H:%M:%S') IN ({",".join(repr(x) for x in HORIZON_TIMES.values())}) AND o.close>0))
        """
        z=con.execute(q).df()
        for r in z.itertuples(index=False):
            px=float(r.open_px) if r.local_time=="09:31:00" else float(r.close_px)
            prices[price_key(r.trade_date,expiry,r.option_type,float(r.strike),pd.Timestamp(r.ts))]=px
    con.close()
    return prices

def attach_expiry(panel, expiry_map):
    x=panel.copy()
    x["date"]=pd.to_datetime(x["date"]).dt.normalize()
    future=[]
    exps=sorted(expiry_map)
    for d in x.date:
        ds=sorted(e for e in exps if e>=d)
        future.append(ds[0] if ds else None)
    x["expiry"]=future
    x["atm"]=(x.open_px/50.0).round()*50
    return x

def trade_from_signal(row, prices, slip):
    d=pd.Timestamp(row.date).date()
    expiry=pd.Timestamp(row.expiry).date()
    atm=int(row.atm)
    side=row.side
    exit_time=HORIZON_TIMES[row.horizon]
    entry_ts=pd.Timestamp(f"{d} 09:31:00")
    exit_ts=pd.Timestamp(f"{d} {exit_time}")
    typ="CE" if side=="CALL" else "PE"
    wing=atm+WING if side=="CALL" else atm-WING
    legs=[(typ,atm,"BUY"),(typ,wing,"SELL")]
    raw=exec_gross=slippage_cost=tc=0.0
    lot=lot_size(expiry)
    for opt,strike,action in legs:
        ep=prices.get(price_key(d,expiry,opt,float(strike),entry_ts))
        xp=prices.get(price_key(d,expiry,opt,float(strike),exit_ts))
        if ep is None or xp is None: return None
        if action=="BUY":
            ee=ep+slip; xx=max(0.0,xp-slip); rp=(xp-ep)*lot; epnl=(xx-ee)*lot; exit_action="SELL"
        else:
            ee=max(0.0,ep-slip); xx=xp+slip; rp=(ep-xp)*lot; epnl=(ee-xx)*lot; exit_action="BUY"
        raw+=rp; exec_gross+=epnl
        slippage_cost+=rp-epnl
        tc+=charge(ee,action,1,lot,d)+charge(xx,exit_action,1,lot,d)
    return {
        "day":str(d),"expiry":str(expiry),"feature":row.feature,"threshold":float(row.threshold),"horizon":row.horizon,
        "side":side,"friction":"base" if slip==0.20 else "stress",
        "raw_gross":raw,"execution_gross":exec_gross,"slippage_cost":slippage_cost,"transaction_costs":tc,
        "net_pnl":exec_gross-tc
    }

def weekly_ledger(trades):
    if trades.empty:
        return pd.DataFrame()
    return (trades.assign(week=pd.to_datetime(trades.day).dt.to_period("W-SUN").astype(str))
            .groupby(["feature","threshold","horizon","friction","week"],as_index=False)
            .net_pnl.sum())

def summary(trades):
    rows=[]
    for feat in FEATURES:
        for thr in THRESHOLDS:
            for hor in HORIZONS:
                g=trades[(trades.feature==feat)&(trades.threshold==thr)&(trades.horizon==hor)] if not trades.empty else trades.iloc[0:0]
                if g.empty:
                    rows.append({"feature":feat,"threshold":thr,"horizon":hor,"friction":None,"trades":0,"weeks":0,
                                 "total_net":0.0,"mean_weekly_net":0.0,"median_weekly_net":0.0,"positive_week_rate":0.0,
                                 "worst_trade":np.nan,"worst_week":np.nan,"max_drawdown":np.nan,"total_slippage":0.0,
                                 "total_transaction_costs":0.0,"raw_gross":0.0})
                    continue
                wk=g.assign(week=pd.to_datetime(g.day).dt.to_period("W-SUN").astype(str)).groupby("week").net_pnl.sum()
                eq=wk.sort_index().cumsum()
                dd=eq-eq.cummax()
                rows.append({"feature":feat,"threshold":thr,"horizon":hor,"friction":g.friction.iloc[0],"trades":len(g),
                             "weeks":len(wk),"total_net":g.net_pnl.sum(),"mean_weekly_net":wk.mean(),
                             "median_weekly_net":wk.median(),"positive_week_rate":(wk>0).mean(),
                             "worst_trade":g.net_pnl.min(),"worst_week":wk.min(),"max_drawdown":dd.min(),
                             "total_slippage":g.slippage_cost.sum(),"total_transaction_costs":g.transaction_costs.sum(),
                             "raw_gross":g.raw_gross.sum()})
    return pd.DataFrame(rows)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--data",default="data/cache/phase31_trademarkk")
    ap.add_argument("--global-data",default="data/cache/phase31_8_global")
    ap.add_argument("--out",default="reports/phase31_8")
    ap.add_argument("--slippage",type=float,default=0.20)
    ap.add_argument("--gate-only",action="store_true")
    args=ap.parse_args()
    root=Path(args.data); global_root=Path(args.global_data); out=Path(args.out); out.mkdir(parents=True,exist_ok=True)
    idx=load_index(root)
    sessions=idx[idx.time=="09:30:00"][["date","open_px","close_px"]].drop_duplicates("date")
    g=load_global(global_root)
    panel=build_panel(g,sessions)
    gate=data_gate(panel,global_root)
    (out/"data_gate.json").write_text(json.dumps(gate,indent=2,default=str),encoding="utf-8")
    panel.to_csv(out/"feature_panel.csv",index=False)
    if args.gate_only or gate["status"]!="PASS":
        print(json.dumps(gate,indent=2,default=str)); return
    expiry_map=expiry_files(root)
    panel=attach_expiry(panel,expiry_map)
    panel=panel.dropna(subset=["expiry","atm"])
    signals=build_signals(panel)
    signals.to_csv(out/"true_signals.csv",index=False)
    (signals.groupby(["feature","threshold","horizon","side"]).size().reset_index(name="signals")
     if not signals.empty else pd.DataFrame()).to_csv(out/"signal_counts.csv",index=False)
    prices=load_prices(root,expiry_map,signals)
    all_base=[]; all_stress=[]
    for friction,slip in (("base",0.20),("stress",0.40)):
        rows=[]
        for r in signals.itertuples(index=False):
            x=trade_from_signal(r,prices,slip)
            if x: rows.append(x)
        td=pd.DataFrame(rows)
        td.to_csv(out/f"trades_{friction}.csv",index=False)
        weekly_ledger(td).to_csv(out/f"weekly_{friction}.csv",index=False)
        summary(td).to_csv(out/f"true_cell_summary_{friction}.csv",index=False)
        if friction=="base": all_base=td
        else: all_stress=td
        null_rows=[]
        for seed in NULL_SEEDS:
            ns=build_signals(panel,null_seed=seed)
            for r in ns.itertuples(index=False):
                x=trade_from_signal(r,prices,slip)
                if x:
                    x["null_seed"]=seed
                    null_rows.append(x)
        nd=pd.DataFrame(null_rows)
        nd.to_csv(out/f"null_trades_{friction}.csv",index=False)
        weekly_ledger(nd).to_csv(out/f"null_weekly_{friction}.csv",index=False)
        parts=[]
        if not nd.empty:
            for seed in NULL_SEEDS:
                gseed=nd[nd.null_seed==seed].copy()
                q=summary(gseed)
                q.insert(1,"null_seed",seed)
                parts.append(q)
        pd.concat(parts,ignore_index=True).to_csv(out/f"null_summary_{friction}.csv",index=False) if parts else pd.DataFrame().to_csv(out/f"null_summary_{friction}.csv",index=False)
    # Price coverage diagnostics across true signals
    cov=[]
    for keys,gx in signals.groupby(["feature","threshold","horizon"]):
        complete=0
        for r in gx.itertuples(index=False):
            d=pd.Timestamp(r.date).date(); e=pd.Timestamp(r.expiry).date(); typ="CE" if r.side=="CALL" else "PE"
            wing=r.atm+WING if r.side=="CALL" else r.atm-WING
            req=[(typ,r.atm,pd.Timestamp(f"{d} 09:31:00")),(typ,r.atm,pd.Timestamp(f"{d} {HORIZON_TIMES[r.horizon]}")),
                 (typ,wing,pd.Timestamp(f"{d} 09:31:00")),(typ,wing,pd.Timestamp(f"{d} {HORIZON_TIMES[r.horizon]}"))]
            complete += int(all(price_key(d,e,o,float(k),ts) in prices for o,k,ts in req))
        cov.append({"feature":keys[0],"threshold":float(keys[1]),"horizon":keys[2],"signals":len(gx),"complete_price_coverage":complete,
                    "coverage_rate":complete/len(gx) if len(gx) else 0.0})
    pd.DataFrame(cov).to_csv(out/"price_coverage.csv",index=False)
    print(json.dumps(gate,indent=2,default=str))
if __name__=="__main__":
    main()
