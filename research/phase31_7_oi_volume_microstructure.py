#!/usr/bin/env python3
from pathlib import Path
from datetime import date, timedelta
import argparse, json, math
import duckdb
import numpy as np
import pandas as pd

START=date(2021,7,1)
END=date(2026,8,31)
THRESHOLDS=(0.20,0.40)
FEATURES=("VOL_IMB","OI_CHANGE_IMB","JOINT")
BUCKETS=(0,1)
NULL_SEEDS=(101,202,303,404,505)
WING=200

def lot_size(expiry):
    d=pd.Timestamp(expiry).date()
    if d<date(2024,4,26): return 50
    if d<date(2024,11,21): return 25
    if d<date(2026,1,6): return 75
    return 65

def charge(price, action, qty, lot, d):
    gross=float(price)*qty*lot
    stt=gross*(0.001 if d<date(2026,4,1) else 0.0015) if action=="SELL" else 0.0
    exch=gross*(0.0003503 if d<date(2026,3,1) else 0.000355299)
    sebi=gross*0.000001
    stamp=gross*0.00003 if action=="BUY" else 0.0
    brokerage=20.0
    gst=0.18*(brokerage+exch+sebi)
    return brokerage+exch+sebi+stt+stamp+gst

def expiry_files(root):
    files={}
    for p in sorted((root/"options/NIFTY").glob("*.parquet")):
        try:
            d=pd.Timestamp(p.stem).date()
        except Exception:
            continue
        files[d]=p
    return files

def load_index(con, path):
    q=f"""SELECT CAST(timestamp AS TIMESTAMP) ts,
                 CAST(open AS DOUBLE) open_px,
                 CAST(close AS DOUBLE) close_px
          FROM read_parquet('{str(path).replace("'", "''")}')
          WHERE CAST(timestamp AS DATE) BETWEEN DATE '{START}' AND DATE '{END}'
          ORDER BY ts"""
    x=con.execute(q).df()
    x.ts=pd.to_datetime(x.ts)
    x["date"]=x.ts.dt.date
    x["time"]=x.ts.dt.strftime("%H:%M:%S")
    return x.drop_duplicates("ts")

def nearest_strike(px):
    return int(round(float(px)/50.0)*50)

def option_feature_rows(con, expiry_map, days_df):
    rows=[]; diag=[]
    for day,row in days_df.iterrows():
        d=row["date"]; spot=float(row["spot"]); atm=nearest_strike(spot)
        future=[e for e in sorted(expiry_map) if e>=d]
        if len(future)<2:
            diag.append({"day":str(d),"status":"MISSING_EXPIRY"})
            continue
        for bucket in BUCKETS:
            expiry=future[bucket]; path=expiry_map[expiry]
            p=str(path).replace("'","''")
            q=f"""SELECT CAST(timestamp AS TIMESTAMP) ts,
                         UPPER(CAST(option_type AS VARCHAR)) option_type,
                         CAST(strike AS DOUBLE) strike,
                         CAST(volume AS DOUBLE) volume,
                         CAST(open_interest AS DOUBLE) oi
                  FROM read_parquet('{p}')
                  WHERE CAST(timestamp AS TIMESTAMP) IN
                        (TIMESTAMP '{d} 09:25:00', TIMESTAMP '{d} 09:30:00')
                    AND CAST(strike AS DOUBLE)={float(atm)}
                    AND UPPER(CAST(option_type AS VARCHAR)) IN ('CE','PE')"""
            z=con.execute(q).df().drop_duplicates(["ts","option_type"])
            if z.empty or len(z)!=4:
                diag.append({"day":str(d),"bucket":bucket,"status":"MISSING_FEATURE_LEGS"})
                continue
            z["ts"]=pd.to_datetime(z.ts)
            try:
                ce25=z[(z.ts==pd.Timestamp(f"{d} 09:25:00"))&(z.option_type=="CE")].iloc[0]
                pe25=z[(z.ts==pd.Timestamp(f"{d} 09:25:00"))&(z.option_type=="PE")].iloc[0]
                ce30=z[(z.ts==pd.Timestamp(f"{d} 09:30:00"))&(z.option_type=="CE")].iloc[0]
                pe30=z[(z.ts==pd.Timestamp(f"{d} 09:30:00"))&(z.option_type=="PE")].iloc[0]
            except Exception:
                diag.append({"day":str(d),"bucket":bucket,"status":"INCOMPLETE_FEATURE_ROWS"})
                continue
            ce_v,pe_v=float(ce30.volume),float(pe30.volume)
            dce=float(ce30.oi)-float(ce25.oi); dpe=float(pe30.oi)-float(pe25.oi)
            vol_den=ce_v+pe_v
            oi_den=abs(dce)+abs(dpe)
            if pd.isna(ce_v) or pd.isna(pe_v) or pd.isna(dce) or pd.isna(dpe) or vol_den<=0 or oi_den<=0:
                diag.append({"day":str(d),"bucket":bucket,"status":"INVALID_FEATURE_VALUES"})
                continue
            vol_imb=(ce_v-pe_v)/vol_den
            oi_imb=(dce-dpe)/oi_den
            rows.append({
                "day":d,"bucket":bucket,"expiry":expiry,"spot":spot,"atm":atm,
                "vol_imb":vol_imb,"oi_change_imb":oi_imb,"joint":0.5*vol_imb+0.5*oi_imb,
                "entry_ts":pd.Timestamp(f"{d} 09:31:00"),"exit_ts":pd.Timestamp(f"{d} 15:10:00")
            })
    return pd.DataFrame(rows), pd.DataFrame(diag)

def load_prices(con, expiry_map, features):
    con.execute("SET TimeZone='Asia/Kolkata'")
    prices={}
    if features.empty:
        con.close()
        return prices
    wanted=features[["day","bucket","expiry","atm","entry_ts","exit_ts"]].drop_duplicates().rename(columns={"day":"trade_date"}).copy()
    wanted["expiry_key"]=pd.to_datetime(wanted["expiry"]).dt.date
    for expiry,path in sorted(expiry_map.items()):
        active=wanted[wanted.expiry_key==expiry].copy()
        if active.empty:
            continue
        dates=sorted(pd.to_datetime(active.trade_date).dt.date.unique().tolist())
        date_sql=",".join(f"DATE '{d}'" for d in dates)
        p=str(path).replace("'","''")
        strikes=sorted(set(float(x) for x in active.atm.tolist()) |
                       set(float(x)+WING for x in active.atm.tolist()) |
                       set(float(x)-WING for x in active.atm.tolist()))
        strike_sql=",".join(str(x) for x in strikes)
        q=f"""
            WITH src AS (
                SELECT
                    CAST(o.timestamp AS TIMESTAMP) AS ts,
                    CAST(CAST(o.timestamp AS TIMESTAMP) AS DATE) AS trade_date,
                    strftime(CAST(o.timestamp AS TIMESTAMP), '%H:%M:%S') AS time_str,
                    UPPER(CAST(o.option_type AS VARCHAR)) AS option_type,
                    CAST(o.strike AS DOUBLE) AS strike,
                    CAST(o.open AS DOUBLE) AS open_px,
                    CAST(o.close AS DOUBLE) AS close_px
                FROM read_parquet('{p}') o
            )
            SELECT
                s.ts,
                s.trade_date,
                s.option_type,
                s.strike,
                CASE
                    WHEN s.time_str='09:31:00' THEN s.open_px
                    WHEN s.time_str='15:10:00' THEN s.close_px
                END AS exec_px
            FROM src s
            WHERE s.trade_date IN ({date_sql})
              AND s.strike IN ({strike_sql})
              AND s.time_str IN ('09:31:00','15:10:00')
              AND s.option_type IN ('CE','PE')
              AND ((s.time_str='09:31:00' AND s.open_px>0)
                OR (s.time_str='15:10:00' AND s.close_px>0))
        """
        z=con.execute(q).df()
        if z.empty:
            continue
        for r in z.itertuples(index=False):
            prices[price_key(r.trade_date,expiry,r.option_type,float(r.strike),pd.Timestamp(r.ts))]=float(r.exec_px)
    con.close()
    return prices

def norm_date(x):
    return pd.Timestamp(x).date()

def price_key(day, expiry, option_type, strike, ts):
    return (norm_date(day), norm_date(expiry), str(option_type).upper(), float(strike), pd.Timestamp(ts).tz_localize(None) if getattr(pd.Timestamp(ts), "tzinfo", None) else pd.Timestamp(ts))

FEATURE_COLS={"VOL_IMB":"vol_imb","OI_CHANGE_IMB":"oi_change_imb","JOINT":"joint"}

def permute_feature_values(panel, feature_col, bucket, seed):
    out=panel.copy()
    rng=np.random.default_rng(seed)
    ix=out.index[out.bucket==bucket]
    vals=out.loc[ix,feature_col].to_numpy(copy=True)
    rng.shuffle(vals)
    out.loc[ix,feature_col]=vals
    return out

def build_signals(panel, null_seed=None):
    working=panel.copy()
    if null_seed is not None:
        for feature in FEATURES:
            col=FEATURE_COLS[feature]
            for bucket in BUCKETS:
                working=permute_feature_values(working,col,bucket,null_seed)
    sig=[]
    for feature in FEATURES:
        col=FEATURE_COLS[feature]
        for threshold in THRESHOLDS:
            for bucket in BUCKETS:
                z=working[working.bucket==bucket].copy()
                for r in z.itertuples(index=False):
                    val=float(getattr(r,col))
                    if abs(val)<threshold:
                        continue
                    side="CALL" if val>0 else "PUT"
                    sig.append({
                        **r._asdict(),
                        "feature":feature,
                        "threshold":threshold,
                        "side":side,
                        "signal_value":val,
                        "null_seed":null_seed
                    })
    return pd.DataFrame(sig)


def trade_from_signal(frow, side, prices, slip):
    d=norm_date(frow.day); expiry=norm_date(frow.expiry); atm=int(frow.atm); lot=lot_size(expiry)
    typ="CE" if side=="CALL" else "PE"
    wing=atm+WING if side=="CALL" else atm-WING
    legs=[(typ,atm,"BUY"),(typ,wing,"SELL")]
    raw=exec_gross=slip_cost=tc=0.0
    for opt, strike, action in legs:
        ep=prices.get(price_key(d,expiry,opt,float(strike),frow.entry_ts))
        xp=prices.get(price_key(d,expiry,opt,float(strike),frow.exit_ts))
        if ep is None or xp is None:
            return None
        if action=="BUY":
            ee=ep+slip; xx=max(0.0,xp-slip); rp=(xp-ep)*lot; epnl=(xx-ee)*lot; exit_action="SELL"
        else:
            ee=max(0.0,ep-slip); xx=xp+slip; rp=(ep-xp)*lot; epnl=(ee-xx)*lot; exit_action="BUY"
        costs=charge(ee,action,1,lot,d)+charge(xx,exit_action,1,lot,d)
        raw+=rp; exec_gross+=epnl; slip_cost+=rp-epnl; tc+=costs
    return {
        "day":str(d),"expiry":str(expiry),"bucket":int(frow.bucket),"feature":frow.feature,
        "threshold":float(frow.threshold),"side":side,"friction":"base" if slip==0.20 else "stress",
        "raw_gross":raw,"execution_gross":exec_gross,"slippage_cost":slip_cost,
        "transaction_costs":tc,"net_pnl":exec_gross-tc
    }

def cell_summary(trades, mode, seed=None):
    out=[]
    declared=[(feature,float(thr),int(bucket)) for feature in FEATURES for thr in THRESHOLDS for bucket in BUCKETS]
    friction=(trades.friction.iloc[0] if not trades.empty else None)
    for feature,thr,bucket in declared:
        g=trades[(trades.feature==feature)&(trades.threshold==thr)&(trades.bucket==bucket)] if not trades.empty else trades.iloc[0:0]
        if seed is not None and "null_seed" in g.columns:
            g=g[g.null_seed==seed]
        if g.empty:
            out.append({"mode":mode,"null_seed":seed,"feature":feature,"threshold":thr,"bucket":bucket,"friction":friction,
              "trades":0,"weeks":0,"total_net":0.0,"mean_weekly_net":0.0,"median_weekly_net":0.0,
              "positive_week_rate":0.0,"worst_trade":float("nan"),"worst_week":float("nan"),
              "total_slippage":0.0,"total_transaction_costs":0.0,"raw_gross":0.0})
            continue
        wk=g.assign(week=pd.to_datetime(g.day).dt.to_period("W-SUN").astype(str)).groupby("week").net_pnl.sum()
        out.append({
          "mode":mode,"null_seed":seed,"feature":feature,"threshold":thr,"bucket":bucket,"friction":g.friction.iloc[0],
          "trades":int(len(g)),"weeks":int(len(wk)),"total_net":float(g.net_pnl.sum()),
          "mean_weekly_net":float(wk.mean()),"median_weekly_net":float(wk.median()),
          "positive_week_rate":float((wk>0).mean()),"worst_trade":float(g.net_pnl.min()),
          "worst_week":float(wk.min()),"total_slippage":float(g.slippage_cost.sum()),
          "total_transaction_costs":float(g.transaction_costs.sum()),"raw_gross":float(g.raw_gross.sum())
        })
    return pd.DataFrame(out)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--data",default="data/cache/phase31_trademarkk")
    ap.add_argument("--out",default="reports/phase31_7")
    ap.add_argument("--slippage",type=float,default=0.20)
    ap.add_argument("--gate-only",action="store_true")
    args=ap.parse_args()
    root=Path(args.data); out=Path(args.out); out.mkdir(parents=True,exist_ok=True)
    con=duckdb.connect(); con.execute("SET TimeZone='Asia/Kolkata'")
    idx=load_index(con,root/"index/NIFTY.parquet")
    sessions=idx[idx.time=="09:30:00"][["date","close_px"]].rename(columns={"close_px":"spot"}).copy()
    expiry_map=expiry_files(root)
    sample_file=next(iter(expiry_map.values()),None)
    required_cols=[]; schema_ok=False
    if sample_file:
        p=str(sample_file).replace("'","''")
        sch=con.execute(f"DESCRIBE SELECT * FROM read_parquet('{p}')").df()
        required_cols=[str(x).lower() for x in sch.column_name.tolist()]
        schema_ok=("volume" in required_cols and "open_interest" in required_cols)
    features,diag=option_feature_rows(con,expiry_map,sessions)
    con.close()
    eligible=len(sessions); cov={}
    for b in BUCKETS:
        cov[b]=float((features.bucket==b).sum()/eligible) if eligible else 0.0
    gate={
        "status":"PASS" if schema_ok and cov.get(0,0)>=0.70 and cov.get(1,0)>=0.50 else "FAIL",
        "eligible_sessions":int(eligible),"feature_rows":int(len(features)),
        "schema_has_volume":bool("volume" in required_cols),
        "schema_has_open_interest":bool("open_interest" in required_cols),
        "nearest_coverage":cov.get(0,0.0),"next_coverage":cov.get(1,0.0),
        "required_nearest_coverage":0.70,"required_next_coverage":0.50,
        "study_start":str(START),"study_end":str(END)
    }
    (out/"data_gate.json").write_text(json.dumps(gate,indent=2),encoding="utf-8")
    diag.to_csv(out/"feature_diagnostics.csv",index=False)
    if args.gate_only or gate["status"]!="PASS":
        features.to_csv(out/"features.csv",index=False)
        print(json.dumps(gate,indent=2))
        return
    signals=build_signals(features)

    if signals.empty:
        pd.DataFrame(columns=["feature","threshold","bucket","side","signals"]).to_csv(out/"signal_counts.csv",index=False)
    else:
        (signals.groupby(["feature","threshold","bucket","side"]).size().reset_index(name="signals")
         .sort_values(["feature","threshold","bucket","side"])
         .to_csv(out/"signal_counts.csv",index=False))
    prices=load_prices(duckdb.connect(),expiry_map,signals)
    coverage=[]
    if not signals.empty:
        for keys,g in signals.groupby(["feature","threshold","bucket","side"]):
            complete=0
            for r in g.itertuples(index=False):
                typ="CE" if r.side=="CALL" else "PE"
                wing=r.atm+WING if r.side=="CALL" else r.atm-WING
                req=[(typ,r.atm,r.entry_ts),(typ,r.atm,r.exit_ts),(typ,wing,r.entry_ts),(typ,wing,r.exit_ts)]
                complete += int(all(price_key(r.day,r.expiry,o,float(k),pd.Timestamp(ts)) in prices for o,k,ts in req))
            coverage.append({"feature":keys[0],"threshold":float(keys[1]),"bucket":int(keys[2]),"side":keys[3],
              "signals":int(len(g)),"complete_price_coverage":int(complete),"coverage_rate":float(complete/len(g))})
    pd.DataFrame(coverage).to_csv(out/"price_coverage.csv",index=False)
    # Reuse prices for true and null controls.
    for friction,slip in (("base",0.20),("stress",0.40)):
        tr=[]
        for r in signals.itertuples(index=False):
            x=trade_from_signal(r,r.side,prices,slip)
            if x: tr.append(x)
        td=pd.DataFrame(tr)
        td.to_csv(out/f"trades_{friction}.csv",index=False)
        cell_summary(td,"TRUE").to_csv(out/f"true_cell_summary_{friction}.csv",index=False)
        null_rows=[]
        for seed in NULL_SEEDS:
            sf=build_signals(features,null_seed=seed)
            for r in sf.itertuples(index=False):
                x=trade_from_signal(r,r.side,prices,slip)
                if x:
                    x["null_seed"]=seed
                    null_rows.append(x)
        nd=pd.DataFrame(null_rows)
        nd.to_csv(out/f"null_trades_{friction}.csv",index=False)
        null_parts=[cell_summary(nd,"NULL",seed=seed) for seed in NULL_SEEDS]
        pd.concat(null_parts,ignore_index=True).to_csv(out/f"null_summary_{friction}.csv",index=False)
    print(json.dumps(gate,indent=2))
if __name__=="__main__":
    main()
