from __future__ import annotations
import argparse, json, math
from pathlib import Path
import duckdb, numpy as np, pandas as pd

START="2025-09-01"; END="2026-08-31"
SLIP_BASE=0.20
SLIP_STRESS=0.40
EXPIRY_CHOICES=("nearest_weekly","second_nearest_weekly")
STRIKE_CHOICES=("atm_consecutive","atm_minus_one")
GAPS=(200,250,300); WAITS=(15,30)
RISKS=("debit_stop_1x_profit_50pct","debit_stop_1x_profit_75pct","debit_stop_1x_expiry")
TIME_EXITS=("monday_15_00","expiry_day_15_00")

def lot_size(e):
    return 75 if pd.Timestamp(e).date()<=pd.Timestamp("2025-12-30").date() else 65

def weekly_expiries(expiries):
    # NSE has four weekly expiries excluding the monthly expiry. For this study
    # the monthly/long-dated last-Tuesday expiry is excluded by month-end rank.
    x=sorted(set(pd.Timestamp(e).date() for e in expiries))
    by_month={}
    for e in x: by_month.setdefault((e.year,e.month),[]).append(e)
    monthly={max(v) for v in by_month.values()}
    return [e for e in x if e not in monthly]

def load_spot(root):
    xs=[]
    for p in sorted(Path(root).glob("*.csv")):
        z=pd.read_csv(p)
        ts=pd.to_datetime(z["Timestamp"],errors="coerce")
        ts=ts.dt.tz_localize("Asia/Kolkata") if ts.dt.tz is None else ts.dt.tz_convert("Asia/Kolkata")
        z["Timestamp"]=ts
        for c in ("Open","High","Low","Close"): z[c]=pd.to_numeric(z[c],errors="coerce")
        xs.append(z[["Timestamp","Open","High","Low","Close"]])
    z=pd.concat(xs,ignore_index=True).dropna().drop_duplicates("Timestamp").sort_values("Timestamp")
    return z[(z.Timestamp.dt.date>=pd.Timestamp(START).date())&(z.Timestamp.dt.date<=pd.Timestamp(END).date())].reset_index(drop=True)

def cost(orders, slip):
    # Paytm Money: use ₹20/order as the conservative post-25-Aug-2023 standard;
    # statutory rates are date-aware and match the frozen project cost model.
    brokerage=20.0*len(orders)
    ex=sebi=stt=stamp=0.0
    for o in orders:
        d=o["date"]; px=o["price"]; qty=o["qty"]; side=o["side"]
        turnover=px*qty
        ex += turnover*(0.0003503 if d<pd.Timestamp("2026-03-01").date() else 0.0003553)
        sebi += turnover*0.000001
        if side<0: stt += turnover*(0.001 if d<pd.Timestamp("2026-04-01").date() else 0.0015)
        else: stamp += turnover*0.00003
    gst=0.18*(brokerage+ex+sebi)
    return brokerage+ex+sebi+stt+stamp+gst

def fill_price(raw, side, slip):
    return raw+slip if side>0 else raw-slip

def main(data_root, spot_root, out_root, limit_defs=0, smoke=False, slip=SLIP_BASE):
    out=Path(out_root); out.mkdir(parents=True,exist_ok=True)
    c=duckdb.connect()
    files=sorted(Path(data_root).glob("NIFTY_*.parquet"))
    if not files: raise RuntimeError("missing NIFTY option cache")
    S="read_parquet("+json.dumps([str(x) for x in files])+", union_by_name=true)"
    cov=json.loads(Path("reports/phase30_6_bear_put_signal_coverage.json").read_text())
    defs=[d for d in cov["definitions"] if d["signal_weeks"]>=20]
    if limit_defs: defs=defs[:limit_defs]
    if smoke: defs=defs[:2]
    signals=[]
    for d in defs:
        for s in d["signals"]:
            signals.append({"definition":d["definition"],**s})
    sig=pd.DataFrame(signals)
    if sig.empty: raise RuntimeError("no eligible signals")
    sig["signal_ts"]=pd.to_datetime(sig.signal_ts).dt.tz_convert("Asia/Kolkata")
    sig["date"]=sig.signal_ts.dt.date
    exp=[x[0] for x in c.execute(f"SELECT DISTINCT CAST(expiry AS DATE) FROM {S} WHERE granularity='1min' ORDER BY 1").fetchall()]
    wexp=weekly_expiries(exp)
    # Required date/expiry pairs for nearest/second-nearest weekly choices.
    req=[]
    for r in sig.itertuples():
        fut=[e for e in wexp if e>r.date]
        for ec in EXPIRY_CHOICES:
            if len(fut)<2: continue
            e=fut[0] if ec=="nearest_weekly" else fut[1]
            req.append((r.definition,r.signal_ts,e,r.Close if hasattr(r,"Close") else r.close))
    reqdf=pd.DataFrame(req,columns=["definition","signal_ts","expiry","spot"])
    if reqdf.empty: raise RuntimeError("no signals with two weekly expiries")
    reqdf["date"]=reqdf.signal_ts.dt.date
    c.register("reqpairs",reqdf[["date","expiry"]].drop_duplicates())
    strikes=c.execute(f"""
      SELECT DISTINCT q.date,q.expiry,q.strike
      FROM {S} q JOIN reqpairs r ON CAST(q.date AS DATE)=r.date AND CAST(q.expiry AS DATE)=r.expiry
      WHERE q.granularity='1min' AND UPPER(CAST(q.option_type AS VARCHAR))='PE' AND q.close>0
    """).df()
    strikes["date"]=pd.to_datetime(strikes.date).dt.date; strikes["expiry"]=pd.to_datetime(strikes.expiry).dt.date
    strike_map={(d,e):np.sort(g.strike.astype(float).unique()) for (d,e),g in strikes.groupby(["date","expiry"])}
    rows=[]
    for r in sig.itertuples():
        fut=[e for e in wexp if e>r.date]
        if len(fut)<2: continue
        for ec,e in zip(EXPIRY_CHOICES,fut[:2]):
            ks=strike_map.get((r.date,e),np.array([]))
            if not len(ks): continue
            spot=float(r.close)
            below=ks[ks<=spot]; above=ks[ks>=spot]
            if ec=="nearest_weekly" or ec=="second_nearest_weekly":
                pass
            for sc in STRIKE_CHOICES:
                if sc=="atm_consecutive":
                    if len(above)==0 or len(below)==0: continue
                    longk=float(above[0]); shortk=float(below[-1])
                else:
                    if len(below)==0: continue
                    at=float(below[-1]); higher=ks[ks>at]
                    if len(higher)==0: continue
                    longk=float(higher[0]); shortk=at
                rows.append({"signal_id":len(rows),"definition":r.definition,"signal_ts":r.signal_ts,
                             "signal_date":r.date,"resistance":float(r.resistance),"spot":spot,
                             "expiry_choice":ec,"strike_choice":sc,"expiry":e,
                             "long_strike":longk,"short_strike":shortk})
    tradespec=pd.DataFrame(rows)
    if tradespec.empty: raise RuntimeError("no strike-resolved signals")
    # Fetch only required PE contracts and only from signal date to expiry.
    contracts=tradespec[["expiry","long_strike","short_strike","signal_date"]].melt(
        id_vars=["expiry","signal_date"],value_name="strike").drop_duplicates()
    contracts=contracts.rename(columns={"expiry":"expiry","signal_date":"start_date"})
    c.register("contracts",contracts[["expiry","strike","start_date"]])
    opt=c.execute(f"""
      SELECT CAST(q.date AS DATE) date, CAST(q.timestamp AS TIMESTAMP) ts,
             CAST(q.expiry AS DATE) expiry, CAST(q.strike AS DOUBLE) strike,
             CAST(q.open AS DOUBLE) open_px, CAST(q.close AS DOUBLE) close_px
      FROM {S} q JOIN contracts k
        ON CAST(q.expiry AS DATE)=k.expiry AND CAST(q.strike AS DOUBLE)=k.strike
       AND CAST(q.date AS DATE)>=k.start_date AND CAST(q.date AS DATE)<=k.expiry
      WHERE q.granularity='1min' AND UPPER(CAST(q.option_type AS VARCHAR))='PE'
        AND q.open>0 AND q.close>0
      ORDER BY expiry,strike,ts
    """).df()
    if opt.empty: raise RuntimeError("no required option quotes")
    opt["ts"]=pd.to_datetime(opt.ts)
    # Keyed series; duplicates are removed deterministically.
    series={(e,s):g.sort_values("ts").drop_duplicates("ts").reset_index(drop=True)
            for (e,s),g in opt.groupby(["expiry","strike"],sort=False)}
    spot=load_spot(spot_root)
    spot_idx=spot.set_index("Timestamp")
    daily=spot.assign(day=spot.Timestamp.dt.date).groupby("day",sort=True).first()[["Open"]]
    spot_by_ts=spot.set_index("Timestamp")["Close"]
    all_weeks=pd.period_range(pd.Timestamp(START),pd.Timestamp(END),freq="W-MON")
    results=[]; edge=0
    def first_gap(date,res,gap,expiry):
        for d,rr in daily.loc[daily.index>date].iterrows():
            if d>expiry: break
            if float(rr.Open)>=res+gap: return d
        return None
    def exact_or_next(s, t, next_ok=False):
        if s is None or s.empty:return None
        if next_ok:
            z=s[s.ts>=pd.Timestamp(t)]
        else:
            z=s[s.ts==pd.Timestamp(t)]
        return None if z.empty else z.iloc[0]
    for r in tradespec.itertuples():
        L=series.get((r.expiry,r.long_strike)); P=series.get((r.expiry,r.short_strike))
        entry_ts=r.signal_ts+pd.Timedelta(minutes=1)
        le=exact_or_next(L,entry_ts); se=exact_or_next(P,entry_ts)
        if le is None or se is None: continue
        D=float(le.open_px-se.open_px)
        if D<=0: continue
        lot=lot_size(r.expiry)
        gap_events={g:first_gap(r.signal_date,r.resistance,g,r.expiry) for g in GAPS}
        for gap in GAPS:
            gd=gap_events[gap]
            for wait in WAITS:
                adj=None
                if gd is not None:
                    obs=pd.Timestamp(gd).tz_localize("Asia/Kolkata")+pd.Timedelta(minutes=wait)
                    sv=spot_by_ts.get(obs)
                    if pd.notna(sv) and float(sv)>r.resistance:
                        # Source says square off the new short if reversal occurs later; this is
                        # handled as an explicit position state in the minute loop.
                        ae=exact_or_next(P,obs+pd.Timedelta(minutes=1),True)
                        if ae is not None: adj=ae
                for risk in RISKS:
                    for tex in TIME_EXITS:
                        exit_day=pd.Timestamp(r.expiry).date() if tex=="expiry_day_15_00" else (pd.Timestamp(r.expiry)-pd.Timedelta(days=1)).date()
                        # Monday exit is only valid if the day before Tuesday expiry is a trading day.
                        exit_ts=pd.Timestamp(f"{exit_day} 15:00").tz_localize("Asia/Kolkata")
                        # Build aligned close marks. Adjustment is a single state transition.
                        z=pd.merge(L[["ts","close_px"]].rename(columns={"close_px":"long"}),
                                   P[["ts","close_px"]].rename(columns={"close_px":"short"}),
                                   on="ts",how="inner")
                        z=z[(z.ts>=entry_ts)&(z.ts<=exit_ts)]
                        if z.empty: continue
                        adjusted=False; adj_ts=None; extra=0.0; reversal_ts=None; reversal_px=None; stop_ts=None; target_ts=None
                        target_frac=0.5 if risk.endswith("50pct") else 0.75 if risk.endswith("75pct") else None
                        if adj is not None:
                            post_spot=spot_by_ts.loc[(spot_by_ts.index>adj.ts)&(spot_by_ts.index<=exit_ts)]
                            rev=post_spot[post_spot<=r.resistance]
                            if not rev.empty:
                                reversal_ts=rev.index[0]+pd.Timedelta(minutes=1)
                                rb=exact_or_next(P,reversal_ts,True)
                                if rb is not None: reversal_px=float(rb.open_px)
                                else: reversal_ts=None
                        for rr in z.itertuples():
                            if adj is not None and (not adjusted) and rr.ts>=adj.ts:
                                adjusted=True; adj_ts=adj.ts; extra=float(adj.open_px)
                            if adjusted and reversal_ts is not None and rr.ts>=reversal_ts:
                                adjusted=False
                                realized_extra=extra-reversal_px
                            else:
                                realized_extra=0.0
                            pnl=float(rr.long-rr.short-D) + realized_extra
                            if adjusted: pnl += extra-float(rr.short)
                            if risk!="debit_stop_1x_expiry" and pnl<=-D:
                                stop_ts=rr.ts+pd.Timedelta(minutes=1); break
                            if target_frac is not None and pnl>=target_frac*(r.long_strike-r.short_strike):
                                target_ts=rr.ts+pd.Timedelta(minutes=1); break
                        gross=sum((-1 if o["side"]>0 else 1)*o["price"]*o["qty"] for o in orders)
                        net=gross-cost(orders,slip)
                        week=str(pd.Timestamp(r.signal_date).to_period("W-MON"))
                        # Capital proxy: debit + 2% ELM on short notional, 3% for >10% OTM short.
                        cap=D*lot
                        spot0=float(r.spot)
                        elm_rate=0.03 if r.short_strike<0.90*spot0 else 0.02
                        cap=max(cap,cap+elm_rate*r.short_strike*lot*(2 if adjusted else 1))
                        results.append({"definition":r.definition,"expiry_choice":r.expiry_choice,
                                        "strike_choice":r.strike_choice,"gap":gap,"wait":wait,
                                        "risk":risk,"time_exit":tex,"trade_date":r.signal_date,
                                        "week":week,"net_pnl":net,"gross_pnl":gross,
                                        "capital_proxy":cap,"reason":reason,"adjusted":adjusted})
    tr=pd.DataFrame(results)
    if tr.empty: raise RuntimeError("no executable trades in matrix")
    tr.to_csv(out/"trades.csv",index=False)
    keys=["definition","expiry_choice","strike_choice","gap","wait","risk","time_exit"]
    rows=[]
    for k,g in tr.groupby(keys,sort=False):
        weeks=g.groupby("week").net_pnl.sum()
        allw=pd.Series(0.0,index=[str(x) for x in all_weeks])
        allw.loc[weeks.index]=weeks.values
        eq=allw.cumsum(); dd=eq-eq.cummax()
        grosspos=g.loc[g.net_pnl>0,"net_pnl"].sum(); grossneg=-g.loc[g.net_pnl<0,"net_pnl"].sum()
        q05=float(allw.quantile(0.05)); es=float(allw[allw<=q05].mean()) if (allw<=q05).any() else q05
        rows.append(dict(zip(keys,k),trades=len(g),weeks_completed=int(g.week.nunique()),
            mean_weekly_net=float(allw.mean()),median_weekly_net=float(allw.median()),
            profitable_week_rate=float((allw>0).mean()),profit_factor=float(grosspos/grossneg) if grossneg else math.inf,
            max_drawdown=float(dd.min()),weekly_q05=q05,weekly_es05=es,
            execution_coverage=float(len(g)/max(1,len(g))),avg_capital_proxy=float(g.capital_proxy.mean()),
            peak_capital_proxy=float(g.capital_proxy.max()),gross_pnl=float(g.gross_pnl.sum()),
            net_pnl=float(g.net_pnl.sum()),cost_share=float(1-g.net_pnl.sum()/g.gross_pnl.sum()) if g.gross_pnl.sum() else 0.0,
            gate=bool(allw.mean()>=5000 and allw.median()>=5000 and (allw>0).mean()>=0.70 and g.week.nunique()>=20)))
    lb=pd.DataFrame(rows).sort_values(["gate","mean_weekly_net"],ascending=[False,False])
    lb.to_csv(out/"leaderboard.csv",index=False)
    summary={"registered_cells":6480,"tested_cells":len(lb),"trade_records":len(tr),
             "passed_gate":int(lb.gate.sum()),"best":lb.iloc[0].to_dict(),"slippage":slip,
             "pnl_authorized":True,"study_window":[START,END]}
    (out/"summary.json").write_text(json.dumps(summary,indent=2,default=str))
    print(json.dumps(summary,indent=2,default=str))

if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--data-root",type=Path,required=True); a.add_argument("--spot-root",type=Path,required=True)
    a.add_argument("--out-root",type=Path,required=True); a.add_argument("--slippage",type=float,default=.20)
    a.add_argument("--limit-defs",type=int,default=0); a.add_argument("--smoke",action="store_true")
    x=a.parse_args(); main(x.data_root,x.spot_root,x.out_root,x.limit_defs,x.smoke,x.slippage)                        orders=[
                            {"date":r.signal_date,"side":1,"price":fill_price(float(le.open_px),1,slip),"qty":lot},
                            {"date":r.signal_date,"side":-1,"price":fill_price(float(se.open_px),-1,slip),"qty":lot},
                            {"date":pd.Timestamp(xt).date(),"side":1,"price":fill_price(float(le2.open_px),1,slip),"qty":lot},
                            {"date":pd.Timestamp(xt).date(),"side":-1,"price":fill_price(float(se2.open_px),-1,slip),"qty":lot},
                        ]
                        if adj is not None:
                            orders.insert(2,{"date":pd.Timestamp(adj.ts).date(),"side":-1,
                                             "price":fill_price(float(adj.open_px),-1,slip),"qty":lot})
                            if reversal_ts is not None and reversal_ts<=pd.Timestamp(xt) and reversal_px is not None:
                                orders.insert(3,{"date":pd.Timestamp(reversal_ts).date(),"side":1,
                                                 "price":fill_price(float(reversal_px),1,slip),"qty":lot})
                            else:
                                orders.append({"date":pd.Timestamp(xt).date(),"side":1,
                                               "price":fill_price(float(se2.open_px),1,slip),"qty":lot})
                        gross=sum((-1 if o["side"]>0 else 1)*o["price"]*o["qty"] for o in orders)
                        net=gross-cost(orders,slip)
                        week=str(pd.Timestamp(r.signal_date).to_period("W-MON"))
                        # Capital proxy: debit + 2% ELM on short notional, 3% for >10% OTM short.
                        cap=D*lot
                        spot0=float(r.spot)
                        elm_rate=0.03 if r.short_strike<0.90*spot0 else 0.02
                        cap=max(cap,cap+elm_rate*r.short_strike*lot*(2 if adjusted else 1))
                        results.append({"definition":r.definition,"expiry_choice":r.expiry_choice,
                                        "strike_choice":r.strike_choice,"gap":gap,"wait":wait,
                                        "risk":risk,"time_exit":tex,"trade_date":r.signal_date,
                                        "week":week,"net_pnl":net,"gross_pnl":gross,
                                        "capital_proxy":cap,"reason":reason,"adjusted":adjusted})
    tr=pd.DataFrame(results)
    if tr.empty: raise RuntimeError("no executable trades in matrix")
    tr.to_csv(out/"trades.csv",index=False)
    keys=["definition","expiry_choice","strike_choice","gap","wait","risk","time_exit"]
    rows=[]
    for k,g in tr.groupby(keys,sort=False):
        weeks=g.groupby("week").net_pnl.sum()
        allw=pd.Series(0.0,index=[str(x) for x in all_weeks])
        allw.loc[weeks.index]=weeks.values
        eq=allw.cumsum(); dd=eq-eq.cummax()
        grosspos=g.loc[g.net_pnl>0,"net_pnl"].sum(); grossneg=-g.loc[g.net_pnl<0,"net_pnl"].sum()
        q05=float(allw.quantile(0.05)); es=float(allw[allw<=q05].mean()) if (allw<=q05).any() else q05
        rows.append(dict(zip(keys,k),trades=len(g),weeks_completed=int(g.week.nunique()),
            mean_weekly_net=float(allw.mean()),median_weekly_net=float(allw.median()),
            profitable_week_rate=float((allw>0).mean()),profit_factor=float(grosspos/grossneg) if grossneg else math.inf,
            max_drawdown=float(dd.min()),weekly_q05=q05,weekly_es05=es,
            execution_coverage=float(len(g)/max(1,len(g))),avg_capital_proxy=float(g.capital_proxy.mean()),
            peak_capital_proxy=float(g.capital_proxy.max()),gross_pnl=float(g.gross_pnl.sum()),
            net_pnl=float(g.net_pnl.sum()),cost_share=float(1-g.net_pnl.sum()/g.gross_pnl.sum()) if g.gross_pnl.sum() else 0.0,
            gate=bool(allw.mean()>=5000 and allw.median()>=5000 and (allw>0).mean()>=0.70 and g.week.nunique()>=20)))
    lb=pd.DataFrame(rows).sort_values(["gate","mean_weekly_net"],ascending=[False,False])
    lb.to_csv(out/"leaderboard.csv",index=False)
    summary={"registered_cells":6480,"tested_cells":len(lb),"trade_records":len(tr),
             "passed_gate":int(lb.gate.sum()),"best":lb.iloc[0].to_dict(),"slippage":slip,
             "pnl_authorized":True,"study_window":[START,END]}
    (out/"summary.json").write_text(json.dumps(summary,indent=2,default=str))
    print(json.dumps(summary,indent=2,default=str))

if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--data-root",type=Path,required=True); a.add_argument("--spot-root",type=Path,required=True)
    a.add_argument("--out-root",type=Path,required=True); a.add_argument("--slippage",type=float,default=.20)
    a.add_argument("--limit-defs",type=int,default=0); a.add_argument("--smoke",action="store_true")
    x=a.parse_args(); main(x.data_root,x.spot_root,x.out_root,x.limit_defs,x.smoke,x.slippage)
