from __future__ import annotations
from pathlib import Path
from datetime import date
import argparse, json
import duckdb
import numpy as np
import pandas as pd

from research.phase31_7_oi_volume_microstructure import lot_size, charge, price_key

START = date(2021,7,1)
END = date(2026,8,31)
REGIMES = ("LOW","MID","HIGH")
DIRECTIONS = ("FOLLOW_GAP","FADE_GAP")
HORIZONS = ("H10_30","H15_10")
HORIZON_TIMES = {"H10_30":"10:30:00","H15_10":"15:10:00"}
NULL_SEEDS = (101,202,303,404,505)
WING = 200

def load_index(root):
    con=duckdb.connect(); con.execute("SET TimeZone='Asia/Kolkata'")
    p=str(root/"index/NIFTY.parquet").replace("'","''")
    q=f"""SELECT CAST(timestamp AS TIMESTAMP) ts, CAST(open AS DOUBLE) open_px,
                  CAST(close AS DOUBLE) close_px
           FROM read_parquet('{p}')
           WHERE CAST(timestamp AS DATE) BETWEEN DATE '{START}' AND DATE '{END}'
           ORDER BY ts"""
    idx=con.execute(q).df(); con.close()
    idx.ts=pd.to_datetime(idx.ts)
    idx["date"]=idx.ts.dt.normalize()
    idx["time"]=idx.ts.dt.strftime("%H:%M:%S")
    return idx.drop_duplicates("ts")

def session_panel(idx, vix):
    d=idx.assign(date=pd.to_datetime(idx.date).dt.normalize())
    daily=(d.sort_values("ts").groupby("date",as_index=False)
             .agg(day_close=("close_px","last")))
    daily["prev_close"]=daily["day_close"].shift(1)
    opens=(d[d.time=="09:30:00"][["date","open_px"]]
           .drop_duplicates("date").sort_values("date"))
    s=opens.merge(daily[["date","prev_close"]],on="date",how="left")
    s["gap_ret"]=s["open_px"]/s["prev_close"]-1.0

    px=daily[["date","day_close"]].copy()
    r=np.log(px.day_close/px.day_close.shift(1))
    rv20=r.shift(1).rolling(20,min_periods=20).std(ddof=1)*np.sqrt(252)*100.0
    rv=pd.DataFrame({"rv_feature_date":px.date,"rv20_pct":rv})

    vx=vix.copy()
    vx["vix_feature_date"]=pd.to_datetime(vx.date).dt.normalize()
    vx=vx[["vix_feature_date","close"]].rename(columns={"close":"vix_close"}).sort_values("vix_feature_date")
    rv=rv.dropna().sort_values("rv_feature_date")
    s["date"]=pd.to_datetime(s["date"]).dt.normalize().astype("datetime64[ns]")
    vx["vix_feature_date"]=vx["vix_feature_date"].astype("datetime64[ns]")
    rv["rv_feature_date"]=rv["rv_feature_date"].astype("datetime64[ns]")

    s=pd.merge_asof(s.sort_values("date"),vx,left_on="date",right_on="vix_feature_date",
                    direction="backward",allow_exact_matches=False)
    s=pd.merge_asof(s.sort_values("date"),rv,left_on="date",right_on="rv_feature_date",
                    direction="backward",allow_exact_matches=False)
    s["ratio"]=s["vix_close"]/s["rv20_pct"]
    s["regime"]=pd.Series(np.select([s["ratio"].le(0.90),s["ratio"].le(1.10)],["LOW","MID"],default="HIGH"),index=s.index,dtype="object")
    s.loc[~np.isfinite(s["ratio"]),"regime"]=None
    s["vix_prior_ok"]=s["vix_feature_date"].notna() & (s["vix_feature_date"] < s["date"])
    s["rv_prior_ok"]=s["rv_feature_date"].notna() & (s["rv_feature_date"] < s["date"])
    s["all_prior"]=s["vix_prior_ok"] & s["rv_prior_ok"] & s["prev_close"].notna()
    return s

def data_gate(panel, root):
    manifest=json.loads((root/"manifest.json").read_text()) if (root/"manifest.json").exists() else {}
    raw=len(panel)
    ready=panel["all_prior"].astype(bool) & panel["ratio"].notna() & panel["gap_ret"].notna()
    eligible=int(ready.sum())
    complete=int((panel["all_prior"] & panel["ratio"].notna()).sum())
    warmup=raw-eligible
    prior_violations=int(((panel["vix_feature_date"].notna()) & (panel["vix_feature_date"]>=panel["date"])).sum()
                         + ((panel["rv_feature_date"].notna()) & (panel["rv_feature_date"]>=panel["date"])).sum())
    return {
        "status":"PASS" if eligible and complete/eligible>=0.95 and prior_violations==0 else "FAIL",
        "raw_nifty_sessions":raw,"feature_eligible_nifty_sessions":eligible,
        "warmup_or_missing_feature_sessions":warmup,
        "complete_feature_sessions":complete,
        "complete_feature_coverage":float(complete/eligible) if eligible else 0.0,
        "prior_barrier_violations":prior_violations,
        "required_feature_coverage":0.95,
        "rv_lookback":20,"study_start":str(START),"study_end":str(END),
        "vix_manifest":manifest
    }

def expiry_files(root):
    out={}
    for p in sorted((root/"options/NIFTY").glob("*.parquet")):
        try: out[pd.Timestamp(p.stem).date()]=p
        except Exception: pass
    return out

def build_signals(panel, null_seed=None):
    x=panel.copy()
    if null_seed is not None:
        rng=np.random.default_rng(null_seed)
        vals=x.loc[x.all_prior & x.ratio.notna(),"regime"].to_numpy(copy=True)
        rng.shuffle(vals)
        idx=x.index[x.all_prior & x.ratio.notna()]
        x.loc[idx,"regime"]=vals
    rows=[]
    base=x[x.all_prior & x.ratio.notna() & x.gap_ret.notna()].copy()
    for regime in REGIMES:
        for direction in DIRECTIONS:
            for horizon in HORIZONS:
                z=base[base.regime==regime].copy()
                z["regime"]=regime; z["direction"]=direction; z["horizon"]=horizon
                if z.empty: continue
                follow=np.where(z.gap_ret>0,"CALL","PUT")
                side=follow if direction=="FOLLOW_GAP" else np.where(z.gap_ret>0,"PUT","CALL")
                z["side"]=side
                z["feature"]="VIX_RV_"+regime
                z["threshold"]=direction
                z["signal_value"]=z.gap_ret
                rows.append(z)
    return pd.concat(rows,ignore_index=True) if rows else pd.DataFrame()

def load_prices(root, expiry_map, signals):
    prices={}
    if signals.empty: return prices
    con=duckdb.connect(); con.execute("SET TimeZone='Asia/Kolkata'")
    sig=signals.copy(); sig["expiry_key"]=pd.to_datetime(sig["expiry"]).dt.date
    for expiry,path in sorted(expiry_map.items()):
        active=sig[sig.expiry_key==expiry].copy()
        if active.empty: continue
        dates=sorted(pd.to_datetime(active.date).dt.date.unique().tolist())
        date_sql=",".join(f"DATE '{d}'" for d in dates)
        strikes=sorted(set(float(x) for x in active.atm.tolist())|set(float(x)+WING for x in active.atm.tolist())|set(float(x)-WING for x in active.atm.tolist()))
        strike_sql=",".join(str(x) for x in strikes)
        times=sorted({"09:31:00",*HORIZON_TIMES.values()})
        time_sql=",".join(f"TIME '{t}'" for t in times)
        p=str(path).replace("'","''")
        q=f"""SELECT CAST(o.timestamp AS TIMESTAMP) ts,
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
                AND CAST(CAST(o.timestamp AS TIMESTAMP) AS TIME) IN ({time_sql})
                AND ((strftime(CAST(o.timestamp AS TIMESTAMP),'%H:%M:%S')='09:31:00' AND o.open>0)
                  OR (strftime(CAST(o.timestamp AS TIMESTAMP),'%H:%M:%S') IN ({",".join(repr(x) for x in HORIZON_TIMES.values())}) AND o.close>0))"""
        z=con.execute(q).df()
        for r in z.itertuples(index=False):
            px=float(r.open_px) if r.local_time=="09:31:00" else float(r.close_px)
            prices[price_key(r.trade_date,expiry,r.option_type,float(r.strike),pd.Timestamp(r.ts))]=px
    con.close()
    return prices

def attach_expiry(panel, expiry_map):
    x=panel.copy(); x["date"]=pd.to_datetime(x.date).dt.normalize()
    exps=sorted(expiry_map)
    x["expiry"]=[next((e for e in exps if e>=pd.Timestamp(d).date()),None) for d in x.date]
    x["atm"]=(x.open_px/50.0).round()*50
    return x

def trade_from_signal(row, prices, slip):
    d=pd.Timestamp(row.date).date(); e=pd.Timestamp(row.expiry).date()
    typ="CE" if row.side=="CALL" else "PE"
    atm=int(row.atm); wing=atm+WING if row.side=="CALL" else atm-WING
    entry_ts=pd.Timestamp(f"{d} 09:31:00"); exit_ts=pd.Timestamp(f"{d} {HORIZON_TIMES[row.horizon]}")
    lot=lot_size(e); raw=exec_gross=slip_cost=tc=0.0
    for opt,strike,action in [(typ,atm,"BUY"),(typ,wing,"SELL")]:
        ep=prices.get(price_key(d,e,opt,float(strike),entry_ts)); xp=prices.get(price_key(d,e,opt,float(strike),exit_ts))
        if ep is None or xp is None: return None
        if action=="BUY":
            ee=ep+slip; xx=max(0.0,xp-slip); rp=(xp-ep)*lot; epnl=(xx-ee)*lot; exit_action="SELL"
        else:
            ee=max(0.0,ep-slip); xx=xp+slip; rp=(ep-xp)*lot; epnl=(ee-xx)*lot; exit_action="BUY"
        raw+=rp; exec_gross+=epnl; slip_cost+=rp-epnl
        tc+=charge(ee,action,1,lot,d)+charge(xx,exit_action,1,lot,d)
    return {"day":str(d),"expiry":str(e),"regime":row.regime,"direction":row.direction,
            "horizon":row.horizon,"side":row.side,"friction":"base" if slip==0.20 else "stress",
            "raw_gross":raw,"slippage_cost":slip_cost,"transaction_costs":tc,"net_pnl":exec_gross-tc}

def summary(trades):
    rows=[]
    for reg in REGIMES:
        for direction in DIRECTIONS:
            for hor in HORIZONS:
                g=trades[(trades.regime==reg)&(trades.direction==direction)&(trades.horizon==hor)] if not trades.empty else trades.iloc[0:0]
                if g.empty:
                    rows.append({"regime":reg,"direction":direction,"horizon":hor,"trades":0,"weeks":0,"total_net":0.0,"mean_weekly_net":0.0,"median_weekly_net":0.0,"positive_week_rate":0.0,"worst_trade":np.nan,"worst_week":np.nan,"max_drawdown":np.nan,"total_slippage":0.0,"total_transaction_costs":0.0,"raw_gross":0.0}); continue
                wk=g.assign(week=pd.to_datetime(g.day).dt.to_period("W-SUN").astype(str)).groupby("week").net_pnl.sum()
                eq=wk.sort_index().cumsum(); dd=eq-eq.cummax()
                rows.append({"regime":reg,"direction":direction,"horizon":hor,"trades":len(g),"weeks":len(wk),"total_net":g.net_pnl.sum(),"mean_weekly_net":wk.mean(),"median_weekly_net":wk.median(),"positive_week_rate":(wk>0).mean(),"worst_trade":g.net_pnl.min(),"worst_week":wk.min(),"max_drawdown":dd.min(),"total_slippage":g.slippage_cost.sum(),"total_transaction_costs":g.transaction_costs.sum(),"raw_gross":g.raw_gross.sum()})
    return pd.DataFrame(rows)

def weekly(trades):
    if trades.empty: return pd.DataFrame()
    return (trades.assign(week=pd.to_datetime(trades.day).dt.to_period("W-SUN").astype(str))
            .groupby(["regime","direction","horizon","friction","week"],as_index=False).net_pnl.sum())

def coverage(signals, prices):
    rows=[]
    for k,g in signals.groupby(["regime","direction","horizon"]):
        ok=0
        for r in g.itertuples(index=False):
            d=pd.Timestamp(r.date).date(); e=pd.Timestamp(r.expiry).date(); typ="CE" if r.side=="CALL" else "PE"; wing=r.atm+WING if r.side=="CALL" else r.atm-WING
            req=[(typ,r.atm,pd.Timestamp(f"{d} 09:31:00")),(typ,r.atm,pd.Timestamp(f"{d} {HORIZON_TIMES[r.horizon]}")),(typ,wing,pd.Timestamp(f"{d} 09:31:00")),(typ,wing,pd.Timestamp(f"{d} {HORIZON_TIMES[r.horizon]}"))]
            ok+=int(all(price_key(d,e,o,float(strike),ts) in prices for o,strike,ts in req))
        rows.append({"regime":k[0],"direction":k[1],"horizon":k[2],"signals":len(g),"complete_price_coverage":ok,"coverage_rate":ok/len(g) if len(g) else 0.0})
    return pd.DataFrame(rows)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--data",default="data/cache/phase31_trademarkk"); ap.add_argument("--vix",default="data/cache/phase31_9_india_vix"); ap.add_argument("--out",default="reports/phase31_9"); ap.add_argument("--slippage",type=float,default=0.20); ap.add_argument("--gate-only",action="store_true"); args=ap.parse_args()
    root=Path(args.data); vroot=Path(args.vix); out=Path(args.out); out.mkdir(parents=True,exist_ok=True)
    idx=load_index(root); vix=pd.read_csv(vroot/"india_vix.csv"); vix["date"]=pd.to_datetime(vix.date)
    panel=session_panel(idx,vix); gate=data_gate(panel,vroot)
    (out/"data_gate.json").write_text(json.dumps(gate,indent=2,default=str)); panel.to_csv(out/"feature_panel.csv",index=False)
    if args.gate_only or gate["status"]!="PASS": print(json.dumps(gate,indent=2)); return
    expiry=expiry_files(root); panel=attach_expiry(panel,expiry).dropna(subset=["expiry","atm"])
    signals=build_signals(panel); signals.to_csv(out/"true_signals.csv",index=False)
    prices=load_prices(root,expiry,signals)
    for friction,slip in (("base",0.20),("stress",0.40)):
        rows=[x for r in signals.itertuples(index=False) if (x:=trade_from_signal(r,prices,slip))]
        td=pd.DataFrame(rows); td.to_csv(out/f"trades_{friction}.csv",index=False); weekly(td).to_csv(out/f"weekly_{friction}.csv",index=False); summary(td).to_csv(out/f"true_cell_summary_{friction}.csv",index=False)
        null_rows=[]
        for seed in NULL_SEEDS:
            ns=build_signals(panel,null_seed=seed)
            for r in ns.itertuples(index=False):
                x=trade_from_signal(r,prices,slip)
                if x: x["null_seed"]=seed; null_rows.append(x)
        nd=pd.DataFrame(null_rows)
        if nd.empty:
            nd=pd.DataFrame(columns=["day","expiry","regime","direction","horizon","side","friction","raw_gross","slippage_cost","transaction_costs","net_pnl","null_seed"])
        nd.to_csv(out/f"null_trades_{friction}.csv",index=False); weekly(nd).to_csv(out/f"null_weekly_{friction}.csv",index=False)
        parts=[]
        for seed in NULL_SEEDS:
            q=summary(nd[nd.null_seed==seed]); q.insert(1,"null_seed",seed); parts.append(q)
        pd.concat(parts,ignore_index=True).to_csv(out/f"null_summary_{friction}.csv",index=False)
    cov=coverage(signals,prices); cov.to_csv(out/"price_coverage.csv",index=False); print(json.dumps(gate,indent=2))
if __name__=="__main__": main()
