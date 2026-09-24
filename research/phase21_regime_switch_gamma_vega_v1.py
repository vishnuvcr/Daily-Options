from __future__ import annotations
import argparse, json
from pathlib import Path
import duckdb, numpy as np, pandas as pd, yfinance as yf
from research.cost_model import OptionCostModel
from research.phase19_nifty_short_strangle_regime import expiry_files, expiry_for_day, load_exact_quotes, load_spot, lot, START_DATE, END_DATE

ENTRY=("14:30:00","14:45:00","15:00:00")
HOLDS=(15,30)
EXPIRY=("WEEK","MONTH")
OFFSETS=(3,4)
STOPS=(1.25,1.50)

def variants():
    out=[]
    for e in ENTRY:
        for ex in EXPIRY:
            for h in HOLDS:
                out.append(dict(regime="EXPANSION",entry=e,expiry_mode=ex,hold=h,offset=None,stop=.65,target=1.50))
                for off in OFFSETS:
                    for st in STOPS:
                        out.append(dict(regime="CALM",entry=e,expiry_mode=ex,hold=h,offset=off,stop=st,target=.50))
    return out

def vid(v):
    o="na" if v["offset"] is None else str(v["offset"])
    return f'{v["regime"]}|{v["entry"]}|{v["expiry_mode"]}|h{v["hold"]}|o{o}|s{v["stop"]}|t{v["target"]}'

def global_daily(root,name,symbol):
    p=root/f"{name}.csv"; root.mkdir(parents=True,exist_ok=True)
    if not p.exists() or p.stat().st_size<100:
        d=yf.download(symbol,start="2018-01-01",end="2026-09-01",auto_adjust=False,progress=False)
        if d.empty: raise RuntimeError(f"no {symbol}")
        if hasattr(d.columns,"levels"):
            d=d["Close"]
            if hasattr(d,"columns"): d=d.iloc[:,0]
        else: d=d["Close"]
        d.rename("Close").reset_index().to_csv(p,index=False)
    x=pd.read_csv(p)
    x["date"]=pd.to_datetime(x["Date"],errors="coerce").dt.date
    x["close"]=pd.to_numeric(x["Close"],errors="coerce")
    x=x.dropna(subset=["date","close"]).sort_values("date").drop_duplicates("date")
    r=x.close.pct_change(); mu=r.shift(1).rolling(20,min_periods=10).mean(); sd=r.shift(1).rolling(20,min_periods=10).std()
    x["z"]=(r-mu)/sd.replace(0,np.nan)
    return x[["date","z"]].dropna()

def prev_z(df,dates):
    a=pd.DataFrame({"date":pd.to_datetime(dates)}); b=df.copy(); b["date"]=pd.to_datetime(b.date)
    return pd.merge_asof(a.sort_values("date"),b.sort_values("date"),on="date",direction="backward",allow_exact_matches=False)["z"].to_numpy()

def regime_table(root,global_root):
    p=root/"index"/"NIFTY.parquet"; con=duckdb.connect(); con.execute("SET TimeZone='Asia/Kolkata'")
    q=f"""SELECT CAST(trading_day AS DATE) d, MIN_BY(CAST(close AS DOUBLE),timestamp) op, MAX_BY(CAST(close AS DOUBLE),timestamp) cl
          FROM read_parquet('{p}') WHERE CAST(trading_day AS DATE) BETWEEN DATE '{START_DATE}' AND DATE '{END_DATE}' AND close>0 GROUP BY 1 ORDER BY 1"""
    n=con.execute(q).df(); con.close(); n["prev"]=n.cl.shift(1); n["gap"]=n.op/n.prev-1
    sp=global_daily(global_root,"SP500","^GSPC"); nq=global_daily(global_root,"NASDAQ","^IXIC"); nk=global_daily(global_root,"NIKKEI","^N225")
    n["zsp"]=prev_z(sp,n.d); n["znq"]=prev_z(nq,n.d); n["znk"]=prev_z(nk,n.d); n["g3"]=n[["zsp","znq","znk"]].mean(axis=1)
    n["expansion"]=n.g3.abs().ge(.5)|n.gap.abs().ge(.0075)
    return n[["d","gap","g3","expansion"]].rename(columns={"d":"trade_date"})

def build_entries(root,spot,quotes,regime):
    files=expiry_files(root); ri=regime.set_index("trade_date"); rows=[]
    for v in variants():
        ss=spot[spot.ts.dt.strftime("%H:%M:%S").eq(v["entry"])]
        for d,sm0 in ss.groupby("trade_date",sort=True):
            sm=sm0.iloc[0]
            if d not in ri.index: continue
            rr=ri.loc[d]
            calm=(not bool(rr.expansion)) and abs(float(sm.ret10))<=.003 and float(sm.rv_ratio)<=1.0
            if (v["regime"]=="EXPANSION" and not bool(rr.expansion)) or (v["regime"]=="CALM" and not calm): continue
            ef=expiry_for_day(files,d)
            if ef is None: continue
            ed,path=ef
            if v["expiry_mode"]=="MONTH":
                f=[x for x in files if x[0]>pd.Timestamp(d).date() and x[0].month!=pd.Timestamp(d).date().month]
                if not f: continue
                ed,path=min(f,key=lambda x:x[0])
            q=quotes[(quotes.trade_date==d)&(quotes.ts>=sm.ts)&(quotes.ts<=sm.ts+pd.Timedelta(minutes=3))]
            sig=q[q.ts==sm.ts]
            strikes=np.sort(sig.strike.dropna().unique())
            if len(strikes)<7: continue
            ai=int(np.argmin(np.abs(strikes-float(sm.spot_close))))
            if v["regime"]=="EXPANSION":
                ps=cs=float(strikes[ai])
            else:
                off=int(v["offset"]); pi=ai-off; ci=ai+off
                if pi<0 or ci>=len(strikes): continue
                ps=float(strikes[pi]); cs=float(strikes[ci])
            pq=q[(q.option_type=="PE")&(q.strike==ps)&(q.ts>sm.ts)]
            cq=q[(q.option_type=="CE")&(q.strike==cs)&(q.ts>sm.ts)]
            common=sorted(set(pq.ts).intersection(set(cq.ts)))
            if not common: continue
            et=common[0]; pr=pq[pq.ts==et].head(1); cr=cq[cq.ts==et].head(1)
            if pr.empty or cr.empty: continue
            pe=float(pr.iloc[0].open_px); ce=float(cr.iloc[0].open_px); ev=pe+ce
            if ev<=0: continue
            rows.append(dict(variant_id=vid(v),regime=v["regime"],trade_date=d,ts=sm.ts,entry_ts=et,expiry=ed,
                             put_strike=ps,call_strike=cs,put_entry=pe,call_entry=ce,entry_value=ev,
                             hold=v["hold"],stop=v["stop"],target=v["target"]))
    return pd.DataFrame(rows)

def simulate(root,setups,slip):
    if setups.empty:return pd.DataFrame()
    files=dict(expiry_files(root)); con=duckdb.connect(); con.execute("SET TimeZone='Asia/Kolkata'")
    u=setups.drop_duplicates(["variant_id","trade_date","ts","entry_ts","expiry","put_strike","call_strike","hold","stop"]).reset_index(drop=True)
    u["id"]=np.arange(len(u),dtype=np.int64); con.register("s",u); parts=[]
    for ed,path in files.items():
        if int(con.execute("select count(*) from s where expiry=?",[ed]).fetchone()[0])==0: continue
        q=f"""select s.id,s.variant_id,s.regime,s.trade_date,s.ts,s.entry_ts,s.put_entry,s.call_entry,s.entry_value,s.hold,s.stop,s.target,
                     cast(o.timestamp as timestamp) ots,cast(o.option_type as varchar) ot,cast(o.strike as double) strike,
                     cast(o.high as double) hi,cast(o.low as double) lo,cast(o.close as double) cl
              from read_parquet('{path}') o join s on s.expiry=DATE '{ed}'
              and cast(cast(o.timestamp as timestamp) as date)=s.trade_date
              and ((o.option_type='PE' and cast(o.strike as double)=s.put_strike) or (o.option_type='CE' and cast(o.strike as double)=s.call_strike))
              and cast(o.timestamp as timestamp)>=s.entry_ts and cast(o.timestamp as timestamp)<=s.entry_ts+interval '30 minutes' where o.close>0"""
        z=con.execute(q).df()
        if not z.empty: z["ots"]=pd.to_datetime(z.ots).dt.floor("min"); parts.append(z)
    con.close()
    if not parts:return pd.DataFrame()
    w=pd.concat(parts,ignore_index=True); look=u.set_index("id"); cm=OptionCostModel(); rows=[]
    for sid,g in w.groupby("id",sort=False):
        r=look.loc[sid]; p=g[g.ot=="PE"][["ots","hi","lo","cl"]].rename(columns={"hi":"phi","lo":"plo","cl":"pcl"}); c=g[g.ot=="CE"][["ots","hi","lo","cl"]].rename(columns={"hi":"chi","lo":"clo","cl":"ccl"}); m=p.merge(c,on="ots").sort_values("ots"); m=m[m.ots<=r.entry_ts+pd.Timedelta(minutes=int(r.hold))]
        if m.empty: continue
        stopv=r.entry_value*r.stop; targetv=r.entry_value*r.target
        if r.regime=="EXPANSION":
            si=np.flatnonzero((m.plo+m.clo).to_numpy()<=stopv); ti=np.flatnonzero((m.phi+m.chi).to_numpy()>=targetv)
            if len(si) and (not len(ti) or si[0]<=ti[0]): ix,rs=int(si[0]),"STOP"
            elif len(ti): ix,rs=int(ti[0]),"TARGET"
            else: ix,rs=len(m)-1,"TIME"
            ex=m.iloc[ix]
            net=cm.net_pnl(r.put_entry,ex.pcl,1,lot(r.trade_date),slip)+cm.net_pnl(r.call_entry,ex.ccl,1,lot(r.trade_date),slip)
        else:
            si=np.flatnonzero((m.phi+m.chi).to_numpy()>=stopv); ti=np.flatnonzero((m.plo+m.clo).to_numpy()<=targetv)
            if len(si) and (not len(ti) or si[0]<=ti[0]): ix,rs=int(si[0]),"STOP"
            elif len(ti): ix,rs=int(ti[0]),"TARGET"
            else: ix,rs=len(m)-1,"TIME"
            ex=m.iloc[ix]; net=cm.short_strangle_net_pnl(r.put_entry,r.call_entry,ex.pcl,ex.ccl,lot(r.trade_date),slippage_points=slip)
        rows.append(dict(variant_id=r.variant_id,trade_date=r.trade_date,regime=r.regime,net_pnl=float(net),reason=rs))
    return pd.DataFrame(rows)

def board(trades):
    if trades.empty:return pd.DataFrame()
    out=[]
    for v,g in trades.groupby("variant_id"):
        d=g.groupby("trade_date").net_pnl.sum(); w=g.loc[g.net_pnl>0,"net_pnl"].sum(); l=-g.loc[g.net_pnl<0,"net_pnl"].sum()
        out.append(dict(variant_id=v,trades=len(g),active_days=len(d),mean_active_day_net=float(d.mean()),median_active_day_net=float(d.median()),win_rate=float((g.net_pnl>0).mean()),positive_day_rate=float((d>0).mean()),profit_factor=float(w/l) if l>0 else 999.0,max_drawdown=float((d.cumsum()-d.cumsum().cummax()).min()),total_net=float(g.net_pnl.sum())))
    return pd.DataFrame(out).sort_values("mean_active_day_net",ascending=False)

def wfa(trades):
    if trades.empty:return pd.DataFrame()
    x=trades.copy(); x["trade_date"]=pd.to_datetime(x.trade_date).dt.date; ds=sorted(x.trade_date.unique()); rows=[]; tl,vl,emb,te,st=120,40,5,40,40
    s=0
    while s+tl+vl+emb+te<=len(ds):
        tr=x[x.trade_date.isin(ds[s:s+tl])]; va=x[x.trade_date.isin(ds[s+tl:s+tl+vl])]; ts=ds[s+tl+vl+emb:s+tl+vl+emb+te]; te_df=x[x.trade_date.isin(ts)]
        sc=sorted([(v,float(g.groupby("trade_date").net_pnl.sum().mean())) for v,g in tr.groupby("variant_id") if len(g)>=8],key=lambda z:z[1],reverse=True)
        vals=sorted([(v,float(va[va.variant_id.eq(v)].groupby("trade_date").net_pnl.sum().mean())) for v,_ in sc[:16] if len(va[va.variant_id.eq(v)])>=5],key=lambda z:z[1],reverse=True)
        if vals:
            g=te_df[te_df.variant_id.eq(vals[0][0])]
            if not g.empty:
                d=g.groupby("trade_date").net_pnl.sum(); rows.append(dict(test_start=str(min(ts)),test_end=str(max(ts)),selected_variant=vals[0][0],validation_mean=vals[0][1],test_mean=float(d.mean()),positive_day_rate=float((d>0).mean()),trade_days=len(d)))
        s+=st
    return pd.DataFrame(rows)

def run(data,global_root,out,slip):
    out.mkdir(parents=True,exist_ok=True); spot=load_spot(data); reg=regime_table(data,global_root); q=load_exact_quotes(data,spot); setups=build_entries(data,spot,q,reg); trades=simulate(data,setups,slip); b=board(trades); wf=wfa(trades)
    b.to_csv(out/"phase21_leaderboard.csv",index=False); wf.to_csv(out/"phase21_walk_forward.csv",index=False)
    s=dict(phase=21,variants=len(variants()),setups=len(setups),trades=len(trades),expansion_trades=int((trades.regime=="EXPANSION").sum()) if not trades.empty else 0,calm_trades=int((trades.regime=="CALM").sum()) if not trades.empty else 0,target_qualified=int((b.mean_active_day_net>=1000).sum()) if not b.empty else 0,best=b.iloc[0].to_dict() if not b.empty else None,wfa_windows=len(wf),target_test_windows=int((wf.test_mean>=1000).sum()) if not wf.empty else 0,mean_test_window_net=float(wf.test_mean.mean()) if not wf.empty else None,slippage=slip)
    (out/"phase21_summary.json").write_text(json.dumps(s,indent=2,default=str)); print(json.dumps(s,indent=2,default=str))
if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--data",type=Path,required=True); ap.add_argument("--global-root",type=Path,required=True); ap.add_argument("--out",type=Path,required=True); ap.add_argument("--slippage",type=float,default=.20); a=ap.parse_args(); run(a.data,a.global_root,a.out,a.slippage)
