from __future__ import annotations
import argparse, json
from pathlib import Path
import duckdb, numpy as np, pandas as pd
from research.contracts import nifty_lot_size
from research.cost_model import OptionCostModel
from research.phase3g_oi_confirmed_breakout import parameter_grid, feature_query, raw_query, build_signals, summarize, walk_forward

SETUP=["trade_date","expiry_type","entry_time","direction","atm_strike","wing_strike","hold_minutes"]

def cost(df, slip):
    if df.empty: return df
    cm=OptionCostModel(); x=df.copy(); x["lot_size"]=x.trade_date.map(nifty_lot_size)
    x["net_pnl"]=[cm.vertical_debit_spread_net_pnl(a,b,c,d,int(l),slippage_points=slip)
                  for a,b,c,d,l in zip(x.long_entry,x.short_entry,x.long_exit,x.short_exit,x.lot_size)]
    return x

def session_maps(raw):
    return {k:g.sort_values("datetime") for k,g in raw.groupby(["trade_date","expiry_type"],sort=False)}

def entries(signals, raw):
    if signals.empty: return pd.DataFrame()
    gs=session_maps(raw); out=[]
    for (d,e),sg in signals.groupby(["trade_date","expiry_type"],sort=False):
        g=gs.get((d,e)); 
        if g is None: continue
        w=g.pivot_table(index="datetime",columns=["option_type","strike_price"],values="close",aggfunc="last").sort_index()
        for r in sg.itertuples(index=False):
            if r.entry_time not in w.index: continue
            q=w.loc[r.entry_time]; q=q.iloc[-1] if isinstance(q,pd.DataFrame) else q
            z=[(float(c[1]),float(p)) for c,p in q.items() if isinstance(c,tuple) and c[0]==r.direction and pd.notna(p)]
            if not z: continue
            atm=min(z,key=lambda t:abs(t[0]-float(r.spot))); m=json.loads(r.variant); width=int(m["width_steps"])
            wings=sorted([x for x in z if x[0]>atm[0]],reverse=False) if r.direction=="CALL" else sorted([x for x in z if x[0]<atm[0]],reverse=True)
            if len(wings)<width: continue
            wing=wings[width-1]
            out.append({"trade_id":int(r.trade_id),"trade_date":d,"expiry_type":e,"entry_time":r.entry_time,"direction":r.direction,
                        "spot":float(r.spot),"variant":r.variant,"atm_strike":atm[0],"wing_strike":wing[0],
                        "long_entry":atm[1],"short_entry":wing[1],"hold_minutes":int(m["hold_minutes"])})
    return pd.DataFrame(out)

def paths(entries_df, raw):
    if entries_df.empty: return pd.DataFrame()
    gs=session_maps(raw); setups=entries_df.drop_duplicates(SETUP).reset_index(drop=True); out=[]
    for (d,e),sg in setups.groupby(["trade_date","expiry_type"],sort=False):
        g=gs.get((d,e)); 
        if g is None: continue
        w=g.pivot_table(index="datetime",columns=["option_type","strike_price"],values="close",aggfunc="last").sort_index()
        for r in sg.itertuples(index=False):
            cs=[(r.direction,r.atm_strike),(r.direction,r.wing_strike)]
            if any(c not in w.columns for c in cs): continue
            end=r.entry_time+pd.Timedelta(minutes=int(r.hold_minutes))
            z=w.loc[(w.index>=r.entry_time)&(w.index<=end),cs].dropna()
            if z.empty or r.entry_time not in z.index: continue
            sp=z[cs[0]]-z[cs[1]]; debit=float(sp.loc[r.entry_time])
            if not np.isfinite(debit) or debit<=0: continue
            a=sp.to_numpy(float); stop=.50*debit; target=1.75*debit; ex=len(a)-1; reason="time"
            if len(a)>1:
                sh=np.flatnonzero(a[1:]<=stop); th=np.flatnonzero(a[1:]>=target)
                si=int(sh[0]+1) if len(sh) else None; ti=int(th[0]+1) if len(th) else None
                if si is not None and (ti is None or si<=ti): ex,reason=si,"stop"
                elif ti is not None: ex,reason=ti,"target"
            dt=z.index[ex]; row=z.iloc[ex]
            out.append({"trade_date":d,"expiry_type":e,"entry_time":r.entry_time,"direction":r.direction,
                        "atm_strike":r.atm_strike,"wing_strike":r.wing_strike,"hold_minutes":r.hold_minutes,
                        "long_entry":r.long_entry,"short_entry":r.short_entry,"long_exit":float(row.iloc[0]),
                        "short_exit":float(row.iloc[1]),"exit_time":dt,"exit_reason":reason,"debit":debit})
    return entries_df.merge(pd.DataFrame(out),on=SETUP+["long_entry","short_entry"],how="inner") if out else pd.DataFrame()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--data",type=Path,required=True); ap.add_argument("--out",type=Path,default=Path("reports/phase3g_fast2")); ap.add_argument("--slippage",nargs="+",type=float,default=[.20,.40]); a=ap.parse_args()
    con=duckdb.connect(); f=con.execute(feature_query(a.data)).df(); raw=con.execute(raw_query(a.data)).df(); con.close()
    f["datetime"]=pd.to_datetime(f["datetime"]); raw["datetime"]=pd.to_datetime(raw["datetime"])
    sig=build_signals(f,parameter_grid()); ent=entries(sig,raw); p=paths(ent,raw); a.out.mkdir(parents=True,exist_ok=True)
    p.to_csv(a.out/"paths.csv",index=False); result={"features":len(f),"signals":len(sig),"entries":len(ent),"paths":len(p),"variants":len(parameter_grid()),"runs":{}}
    for s in a.slippage:
        t=cost(p,s); root=a.out/f"s{str(s).replace('.','_')}"; root.mkdir(exist_ok=True)
        b,pre=summarize(t,int(f.trade_date.nunique())); b.to_csv(root/"leaderboard.csv",index=False); wf,wfs=walk_forward(t); wf.to_csv(root/"walk_forward.csv",index=False)
        block={"slippage":s,"preliminary":pre,"walk_forward":wfs,"gate":wfs.get("gate",pre.get("gate"))}; (root/"summary.json").write_text(json.dumps(block,indent=2,default=str)); result["runs"][str(s)]=block
    (a.out/"summary.json").write_text(json.dumps(result,indent=2,default=str)); print(json.dumps(result,indent=2,default=str))

if __name__=="__main__": main()
