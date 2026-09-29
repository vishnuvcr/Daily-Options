from __future__ import annotations
import argparse, json
from datetime import date
from pathlib import Path
import duckdb, numpy as np, pandas as pd

START_DATE = "2021-07-01"
END_DATE = "2026-08-04"
ENTRY_REF, ENTRY_FILL, EXIT_TIME, EXIT_FALLBACK_TIME = "09:30:00", "09:31:00", "15:15:00", "15:14:00"

def lot_size(expiry):
    d = pd.Timestamp(expiry).date()
    if d < date(2021,7,1): return 75
    if d < date(2024,4,26): return 50
    if d < date(2024,11,21): return 25
    if d < date(2026,1,6): return 75
    return 65

def cost(legs, lot, slip, entry_date, exit_date):
    turnover=sum((x["entry"]+x["exit"])*x["qty"]*lot for x in legs)
    sell_entry=sum(x["entry"]*x["qty"]*lot for x in legs if x["sign"]<0)
    sell_exit=sum(x["exit"]*x["qty"]*lot for x in legs if x["sign"]>0)
    buy_entry=sum(x["entry"]*x["qty"]*lot for x in legs if x["sign"]>0)
    buy_exit=sum(x["exit"]*x["qty"]*lot for x in legs if x["sign"]<0)
    brokerage=40.0*len(legs)
    exchange=turnover*(0.0003503 if pd.Timestamp(entry_date).date()<date(2026,3,1) else 0.000355299)
    sebi=turnover*0.000001
    er=0.001 if pd.Timestamp(entry_date).date()<date(2026,4,1) else 0.0015
    xr=0.001 if pd.Timestamp(exit_date).date()<date(2026,4,1) else 0.0015
    stt=sell_entry*er+sell_exit*xr
    stamp=(buy_entry+buy_exit)*0.00003
    gst=0.18*(brokerage+exchange+sebi)
    sl=2.0*slip*sum(x["qty"]*lot for x in legs)
    return float(brokerage+exchange+sebi+stt+stamp+gst+sl)

def load_index(root):
    p=root/"index"/"NIFTY.parquet"
    con=duckdb.connect()
    con.execute("SET TimeZone='Asia/Kolkata'")
    con.execute("SET TimeZone='Asia/Kolkata'")
    q=f"""SELECT CAST(timestamp AS TIMESTAMP) ts, CAST(trading_day AS DATE) trade_date,
    CAST(open AS DOUBLE) open_px, CAST(high AS DOUBLE) high_px, CAST(low AS DOUBLE) low_px,
    CAST(close AS DOUBLE) close_px FROM read_parquet('{p}',union_by_name=true)
    WHERE CAST(trading_day AS DATE) BETWEEN DATE '{START_DATE}' AND DATE '{END_DATE}'
    AND CAST(CAST(timestamp AS TIMESTAMP) AS TIME) BETWEEN TIME '09:15:00' AND TIME '15:29:00' ORDER BY ts"""
    x=con.execute(q).df(); con.close()
    if x.empty: raise RuntimeError("NIFTY index data missing in research window")
    x["ts"]=pd.to_datetime(x["ts"]); x["trade_date"]=pd.to_datetime(x["trade_date"]).dt.date
    return x

def expiry_files(root):
    out=[]
    for p in sorted((root/"options"/"NIFTY").glob("*.parquet")):
        try: out.append((pd.Timestamp(p.stem).date(),p))
        except Exception: pass
    if not out: raise FileNotFoundError("No exact-expiry option parquet files")
    return out

def sessions(idx):
    days=sorted(idx.trade_date.unique()); rows=[]
    for i,td in enumerate(days):
        g=idx[idx.trade_date==td]
        ref=g[g.ts.dt.strftime("%H:%M:%S")==ENTRY_REF]
        op=g[g.ts.dt.strftime("%H:%M:%S")=="09:15:00"]
        pre=g[g.ts.dt.strftime("%H:%M:%S").between("09:15:00","09:29:00")]
        if i==0 or ref.empty or op.empty or pre.empty: continue
        prev=idx[idx.trade_date==days[i-1]]
        pc=float(prev.close_px.iloc[-1])
        if pc<=0: continue
        pr=float((prev.high_px.max()-prev.low_px.min())/pc)
        pret=float(prev.close_px.iloc[-1]/prev.open_px.iloc[0]-1)
        r15=float(pre.close_px.iloc[-1]/op.open_px.iloc[0]-1)
        rr=float((pre.high_px.max()-pre.low_px.min())/op.open_px.iloc[0])
        rows.append({"trade_date":td,"entry_spot":float(ref.close_px.iloc[0]),
          "gap_pct":float(op.open_px.iloc[0]/pc-1),"gap_abs_pct":abs(float(op.open_px.iloc[0]/pc-1)),
          "first15_ret":r15,"first15_abs_ret":abs(r15),"first15_range_pct":rr,
          "prior_day_range_pct":pr,"prior_day_return_pct":pret,
          "day_of_week":pd.Timestamp(td).day_name()})
    s=pd.DataFrame(rows)
    if s.empty: return s
    s["prior20_median_range_pct"]=s.prior_day_range_pct.shift(1).rolling(20,min_periods=10).median()
    return s

def assign_expiry(s, files):
    ex=[e for e,_ in files]
    z=s.copy(); z["expiry"]=[next((e for e in ex if e>=d),None) for d in z.trade_date]
    return z.dropna(subset=["expiry"]).copy()

def query_quotes(con,path,days):
    if not days: return pd.DataFrame()
    con.execute("SET TimeZone='Asia/Kolkata'")
    vals=",".join(f"(DATE '{d}')" for d in days)
    q=f"""WITH d(trade_date) AS (VALUES {vals})
    SELECT CAST(o.trading_day AS DATE) trade_date, CAST(o.timestamp AS TIMESTAMP) ts,
    CAST(o.strike AS DOUBLE) strike, UPPER(CAST(o.option_type AS VARCHAR)) option_type,
    CAST(o.open AS DOUBLE) open_px, CAST(o.close AS DOUBLE) close_px FROM read_parquet('{path}',union_by_name=true) o
    JOIN d ON CAST(o.trading_day AS DATE)=d.trade_date
    WHERE (o.open>0 OR o.close>0)"""
    x=con.execute(q).df()
    if x.empty: return x
    # Normalize to Python date so option rows join exactly with session.trade_date.
    x["trade_date"]=pd.to_datetime(x["trade_date"]).dt.date
    x["ts"]=pd.to_datetime(x["ts"])
    x["hhmm"]=x["ts"].dt.strftime("%H:%M:%S")
    return x[x["hhmm"].isin([ENTRY_FILL, EXIT_TIME, EXIT_FALLBACK_TIME])].copy()

def pick_otm(chain,spot):
    ce=np.sort(chain.loc[chain.option_type=="CE","strike"].unique())
    pe=np.sort(chain.loc[chain.option_type=="PE","strike"].unique())
    ce=ce[ce>spot]; pe=pe[pe<spot]
    if len(ce)<2 or len(pe)<2: return None
    return {"short_ce":float(ce[0]),"long_ce":float(ce[1]),
            "short_pe":float(pe[-1]),"long_pe":float(pe[-2])}

def px(df,side,strike):
    x=df[(df.option_type==side)&np.isclose(df.strike,strike)]
    return float(x.open_px.iloc[0]) if not x.empty else np.nan

def make_trades(sess,q,diag_rows=None,expiry=None):
    out=[]
    for r in sess.itertuples(index=False):
        drow={"trade_date":str(r.trade_date),"expiry":str(expiry) if expiry is not None else str(r.expiry),"stage":"start",
              "quote_rows":0,"entry_rows":0,"entry_ce_strikes":0,"entry_pe_strikes":0}
        z=q[q.trade_date==r.trade_date]
        drow["quote_rows"]=int(len(z))
        en=z[z.ts.dt.strftime("%H:%M:%S")==ENTRY_FILL]
        drow["entry_rows"]=int(len(en))
        drow["entry_ce_strikes"]=int(en.loc[en.option_type=="CE","strike"].nunique())
        drow["entry_pe_strikes"]=int(en.loc[en.option_type=="PE","strike"].nunique())
        if en.empty:
            drow["stage"]="no_entry_quote"; diag_rows.append(drow) if diag_rows is not None else None; continue
        k=pick_otm(en,r.entry_spot)
        if not k:
            drow["stage"]="insufficient_otm_strikes"; diag_rows.append(drow) if diag_rows is not None else None; continue
        drow.update({"short_ce":k["short_ce"],"long_ce":k["long_ce"],"short_pe":k["short_pe"],"long_pe":k["long_pe"]})
        specs=[("short_ce","CE",k["short_ce"],-1,1),("long_ce","CE",k["long_ce"],1,2),
               ("short_pe","PE",k["short_pe"],-1,1),("long_pe","PE",k["long_pe"],1,2)]
        exact=z[z.ts.dt.strftime("%H:%M:%S")==EXIT_TIME]
        fallback=z[z.ts.dt.strftime("%H:%M:%S")==EXIT_FALLBACK_TIME]
        legs=[]; ok=True; exit_mark_time=None
        for name,side,strike,sign,qty in specs:
            a=px(en,side,strike)
            if not np.isfinite(a):
                drow["stage"]=f"missing_entry_{name}"; ok=False; break
            x=exact[(exact.option_type==side)&np.isclose(exact.strike,strike)]
            if not x.empty and pd.notna(x.open_px.iloc[0]) and x.open_px.iloc[0]>0:
                b=float(x.open_px.iloc[0]); bt=EXIT_TIME
            else:
                x=fallback[(fallback.option_type==side)&np.isclose(fallback.strike,strike)]
                if x.empty or pd.isna(x.close_px.iloc[0]) or x.close_px.iloc[0]<=0:
                    drow["stage"]=f"missing_exit_{name}"; ok=False; break
                b=float(x.close_px.iloc[0]); bt=EXIT_FALLBACK_TIME
            if exit_mark_time is None: exit_mark_time=bt
            elif bt != exit_mark_time:
                drow["stage"]="mixed_exit_mark_times"; ok=False; break
            legs.append((name,strike,sign,qty,a,b))
        if not ok:
            diag_rows.append(drow) if diag_rows is not None else None; continue
        lot=lot_size(pd.Timestamp(r.expiry).date())
        gross=sum(sign*(b-a)*qty*lot for _,_,sign,qty,a,b in legs)
        short_sum=sum(a*qty for _,_,sgn,qty,a,_ in legs if sgn<0)
        long_sum=sum(a*qty for _,_,sgn,qty,a,_ in legs if sgn>0)
        row={f:getattr(r,f) for f in r._fields}
        row.update({"lot":lot,"gross_pnl":gross,"short_premium_sum":short_sum,
                    "long_premium_sum":long_sum,"exit_mark_time":exit_mark_time,
                    "net_entry_credit_points":short_sum-long_sum,
                    "entry_debit_points":long_sum-short_sum,
                    "long_short_premium_ratio":long_sum/short_sum if short_sum>0 else np.nan,
                    "expiry_day":r.trade_date==pd.Timestamp(r.expiry).date(),
                    "days_to_expiry":(pd.Timestamp(r.expiry).date()-r.trade_date).days})
        for name,strike,sign,qty,a,b in legs:
            row[f"{name}_strike"]=strike; row[f"{name}_entry"]=a; row[f"{name}_exit"]=b
        out.append(row)
        if diag_rows is not None:
            drow["stage"]="complete_trade"
            drow["exit_mark_time"]=exit_mark_time
            diag_rows.append(drow)
    return pd.DataFrame(out)

def apply_costs(t,slip):
    cs=[]; nets=[]
    for r in t.itertuples(index=False):
        legs=[{"entry":r.short_ce_entry,"exit":r.short_ce_exit,"qty":1,"sign":-1},
              {"entry":r.long_ce_entry,"exit":r.long_ce_exit,"qty":2,"sign":1},
              {"entry":r.short_pe_entry,"exit":r.short_pe_exit,"qty":1,"sign":-1},
              {"entry":r.long_pe_entry,"exit":r.long_pe_exit,"qty":2,"sign":1}]
        c=cost(legs,int(r.lot),slip,r.trade_date,r.trade_date); cs.append(c); nets.append(r.gross_pnl-c)
    z=t.copy(); z["total_cost"]=cs; z["net_pnl"]=nets; z=z.sort_values("trade_date").reset_index(drop=True)
    z["cum_net_pnl"]=z.net_pnl.cumsum(); z["peak_cum_net_pnl"]=z.cum_net_pnl.cummax(); z["drawdown"]=z.cum_net_pnl-z.peak_cum_net_pnl
    return z

def summary(t):
    w=t[t.net_pnl>0]; l=t[t.net_pnl<0]
    return {"trades":int(len(t)),"wins":int(len(w)),"losses":int(len(l)),
      "win_rate":float((t.net_pnl>0).mean()),"gross_pnl":float(t.gross_pnl.sum()),
      "total_cost":float(t.total_cost.sum()),"net_pnl":float(t.net_pnl.sum()),
      "mean_net_pnl":float(t.net_pnl.mean()),"median_net_pnl":float(t.net_pnl.median()),
      "mean_win":float(w.net_pnl.mean()) if len(w) else None,"mean_loss":float(l.net_pnl.mean()) if len(l) else None,
      "profit_factor":float(w.net_pnl.sum()/abs(l.net_pnl.sum())) if len(l) else None,
      "max_drawdown":float(t.drawdown.min()),"max_gain":float(t.net_pnl.max()),"max_loss":float(t.net_pnl.min())}

def feature_analysis(t,out):
    feats=["gap_pct","gap_abs_pct","first15_ret","first15_abs_ret","first15_range_pct",
           "prior_day_range_pct","prior20_median_range_pct","prior_day_return_pct",
           "days_to_expiry","short_premium_sum","long_premium_sum","net_entry_credit_points",
           "entry_debit_points","long_short_premium_ratio","entry_spot"]
    d=t[t.trade_date<=date(2024,12,31)].copy(); h=t[t.trade_date>=date(2025,1,1)].copy()
    dr=[]; hr=[]
    for f in feats:
        x=d[f].dropna()
        if len(x)<50: continue
        cuts=x.quantile([0,.2,.4,.6,.8,1]).to_numpy(); cuts[0]=-np.inf; cuts[-1]=np.inf
        for label,df,store in [("discovery",d,dr),("holdout",h,hr)]:
            q=df[[f,"net_pnl"]].dropna().copy()
            if q.empty: continue
            q["bin"]=pd.cut(q[f],bins=cuts,include_lowest=True,duplicates="drop")
            g=q.groupby("bin",observed=True).agg(trades=("net_pnl","size"),mean_pnl=("net_pnl","mean"),
               median_pnl=("net_pnl","median"),win_rate=("net_pnl",lambda s:float((s>0).mean())),
               loss_rate=("net_pnl",lambda s:float((s<0).mean()))).reset_index()
            g.insert(0,"feature",f); g.insert(1,"sample",label); store.append(g)
    if dr: pd.concat(dr,ignore_index=True).to_csv(out/"feature_bins_discovery.csv",index=False)
    if hr: pd.concat(hr,ignore_index=True).to_csv(out/"feature_bins_holdout.csv",index=False)
    y=t.copy(); y["year"]=pd.to_datetime(y.trade_date).dt.year
    y.groupby("year").agg(trades=("net_pnl","size"),net_pnl=("net_pnl","sum"),win_rate=("net_pnl",lambda s:float((s>0).mean())),mean_pnl=("net_pnl","mean")).reset_index().to_csv(out/"year_breakdown.csv",index=False)
    y.groupby("expiry_day").agg(trades=("net_pnl","size"),net_pnl=("net_pnl","sum"),win_rate=("net_pnl",lambda s:float((s>0).mean())),mean_pnl=("net_pnl","mean")).reset_index().to_csv(out/"expiry_day_breakdown.csv",index=False)
    try:
        from sklearn.tree import DecisionTreeClassifier, export_text
        from sklearn.model_selection import StratifiedKFold, cross_val_score
        fs=[f for f in feats if f in d.columns]; z=d.dropna(subset=fs+["net_pnl"])
        if len(z)>=200:
            X=z[fs]; y=(z.net_pnl<0).astype(int); clf=DecisionTreeClassifier(max_depth=3,min_samples_leaf=50,random_state=1)
            cv=StratifiedKFold(n_splits=5,shuffle=False); auc=cross_val_score(clf,X,y,cv=cv,scoring="roc_auc")
            clf.fit(X,y); (out/"loss_tree.txt").write_text(export_text(clf,feature_names=fs))
            (out/"loss_tree_cv.json").write_text(json.dumps({"auc_mean":float(auc.mean()),"auc_std":float(auc.std()),"max_depth":3,"min_samples_leaf":50},indent=2))
    except Exception as e:
        (out/"loss_tree_error.txt").write_text(repr(e))

def run(data,out,slip):
    root=Path(data); out=Path(out); out.mkdir(parents=True,exist_ok=True)
    idx=load_index(root); files=expiry_files(root); sess=assign_expiry(sessions(idx),files)
    if len(sess)<1000: raise RuntimeError(f"Eligibility gate failed: {len(sess)} sessions")
    con=duckdb.connect(); con.execute("SET TimeZone='Asia/Kolkata'"); frames=[]; cov=[]; diag_rows=[]
    for expiry,path in files:
        sub=sess[sess.expiry==expiry]; days=sub.trade_date.tolist()
        if not days: continue
        q=query_quotes(con,path,days); cov.append({"expiry":str(expiry),"sessions":len(days),"quote_rows":int(len(q))})
        t=make_trades(sub,q,diag_rows,expiry)
        if not t.empty: frames.append(t)
    con.close()
    diag_df=pd.DataFrame(diag_rows)
    if not diag_df.empty:
        diag_df.to_csv(out/"selection_diagnostics.csv",index=False)
        (out/"selection_diagnostics_summary.json").write_text(json.dumps(diag_df.stage.value_counts().to_dict(),indent=2))
    (out/"coverage.json").write_text(json.dumps(cov,indent=2))
    if not frames:
        stage_counts=diag_df.stage.value_counts().to_dict() if not diag_df.empty else {}
        raise RuntimeError("No complete four-leg trades; stage_counts="+json.dumps(stage_counts,sort_keys=True))
    trades=apply_costs(pd.concat(frames,ignore_index=True),slip)
    trades.to_csv(out/"trades.csv",index=False)
    s=summary(trades); s.update({"slippage":slip,"eligible_sessions":len(sess),"executed_trades":len(trades),
      "execution_coverage":len(trades)/len(sess),"start_date":START_DATE,"end_date":END_DATE,"expiry_files_used":len(cov)})
    (out/"summary.json").write_text(json.dumps(s,indent=2)); (out/"coverage.json").write_text(json.dumps(cov,indent=2))
    feature_analysis(trades,out); return s

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--data",required=True); ap.add_argument("--out",required=True); ap.add_argument("--slippage",type=float,required=True)
    a=ap.parse_args(); print(json.dumps(run(a.data,a.out,a.slippage),indent=2))
