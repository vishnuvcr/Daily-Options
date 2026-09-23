from __future__ import annotations
import argparse, json
from pathlib import Path
import duckdb, numpy as np, pandas as pd
from research.contracts import nifty_lot_size
from research.cost_model import OptionCostModel
from research.phase3g_oi_confirmed_breakout import summarize, walk_forward

LOOKBACKS=(1,3)
PERSIST=(1,2)
THRESH=(0.001,0.002)
EXPIRIES=("WEEK","MONTH")
WIDTHS=(1,2)
HOLDS=(15,30,60)
SETUP=["trade_date","expiry_type","entry_time","direction","atm_strike","wing_strike","hold_minutes"]

def grid():
    return [dict(lookback=l,persist=p,threshold=t,expiry_type=e,width_steps=w,hold_minutes=h)
            for l in LOOKBACKS for p in PERSIST for t in THRESH for e in EXPIRIES for w in WIDTHS for h in HOLDS]

def lead_query(root):
    g=(root/"**"/"*.parquet").as_posix()
    return f"""
    WITH o AS (
      SELECT datetime, CAST(date AS DATE) trade_date, expiry_type, option_type,
             CAST(strike_price AS DOUBLE) strike_price, CAST(spot AS DOUBLE) spot,
             CAST(close AS DOUBLE) close
      FROM read_parquet('{g}', union_by_name=true)
      WHERE close>0 AND strike_type='ATM'
    ),
    s AS (
      SELECT datetime, trade_date, MAX(spot) spot
      FROM o GROUP BY ALL
    ),
    p AS (
      SELECT datetime, trade_date, expiry_type, strike_price,
             MAX(spot) spot,
             MAX(CASE WHEN option_type='CALL' THEN close END) call_px,
             MAX(CASE WHEN option_type='PUT' THEN close END) put_px
      FROM o GROUP BY ALL
    ),
    x AS (
      SELECT p.*,
        LN(call_px/LAG(call_px) OVER (
          PARTITION BY trade_date,expiry_type,strike_price,option_type ORDER BY datetime
        )) AS bad_call,
        LN(put_px/LAG(put_px) OVER (
          PARTITION BY trade_date,expiry_type,strike_price,option_type ORDER BY datetime
        )) AS bad_put
      FROM p
    )
    SELECT * FROM (
      SELECT x.datetime,x.trade_date,x.expiry_type,x.strike_price,x.spot,
             x.call_px,x.put_px,
             LN(x.call_px/LAG(x.call_px) OVER (
                PARTITION BY x.trade_date,x.expiry_type,x.strike_price ORDER BY x.datetime
             )) call_ret,
             LN(x.put_px/LAG(x.put_px) OVER (
                PARTITION BY x.trade_date,x.expiry_type,x.strike_price ORDER BY x.datetime
             )) put_ret,
             LN(x.spot/LAG(x.spot) OVER (
                PARTITION BY x.trade_date ORDER BY x.datetime
             )) spot_ret,
             LN(x.call_px/LAG(x.call_px,3) OVER (
                PARTITION BY x.trade_date,x.expiry_type,x.strike_price ORDER BY x.datetime
             )) call_ret3,
             LN(x.put_px/LAG(x.put_px,3) OVER (
                PARTITION BY x.trade_date,x.expiry_type,x.strike_price ORDER BY x.datetime
             )) put_ret3,
             LN(x.spot/LAG(x.spot,3) OVER (
                PARTITION BY x.trade_date ORDER BY x.datetime
             )) spot_ret3
      FROM x
    ) q
    WHERE STRFTIME(datetime + INTERVAL '5 hours 30 minutes','%H:%M:%S')
          BETWEEN '09:30:00' AND '12:30:00'
    ORDER BY trade_date,expiry_type,datetime
    """

def raw_query(root):
    g=(root/"**"/"*.parquet").as_posix()
    return f"""
    SELECT datetime, CAST(date AS DATE) trade_date, expiry_type, option_type,
           CAST(strike_price AS DOUBLE) strike_price, CAST(close AS DOUBLE) close
    FROM read_parquet('{g}', union_by_name=true)
    WHERE close>0 AND STRFTIME(datetime + INTERVAL '5 hours 30 minutes','%H:%M:%S')
          BETWEEN '09:20:00' AND '14:45:00'
    """

def build_signals(f):
    rows=[]
    f=f.copy()
    f["score1"]=0.5*(f["call_ret"]-f["put_ret"])-f["spot_ret"]
    f["score3"]=0.5*(f["call_ret3"]-f["put_ret3"])-f["spot_ret3"]
    f=f.replace([np.inf,-np.inf],np.nan)
    for g in grid():
        z=f[f.expiry_type.eq(g["expiry_type"])].copy()
        z["score"]=z["score1"] if g["lookback"]==1 else z["score3"]
        z=z.dropna(subset=["score","call_px","put_px","spot"])
        s=np.sign(z.score)
        z["same"]=s.ne(0)&s.eq(s.shift(1))
        if g["persist"]==1:
            ok=s.ne(0)
        else:
            ok=z["same"]
        bull=ok&(z.score>=g["threshold"])
        bear=ok&(z.score<=-g["threshold"])
        z=z.loc[bull|bear].sort_values(["trade_date","datetime"]).copy()
        if z.empty: continue
        z=z.drop_duplicates("trade_date",keep="first")
        for r in z.itertuples():
            rows.append({
                "trade_date":r.trade_date,"expiry_type":r.expiry_type,"signal_time":r.datetime,
                "entry_time":r.datetime+pd.Timedelta(minutes=1),
                "spot":float(r.spot),"direction":"CALL" if r.score>0 else "PUT",
                "variant":json.dumps(g,sort_keys=True)
            })
    return pd.DataFrame(rows)

def session_maps(raw):
    return {k:g.sort_values("datetime") for k,g in raw.groupby(["trade_date","expiry_type"],sort=False)}

def choose_entries(sig,raw):
    if sig.empty:return pd.DataFrame()
    gs=session_maps(raw); out=[]
    for (d,e),sg in sig.groupby(["trade_date","expiry_type"],sort=False):
        g=gs.get((d,e))
        if g is None:continue
        w=g.pivot_table(index="datetime",columns=["option_type","strike_price"],values="close",aggfunc="last").sort_index()
        for r in sg.itertuples(index=False):
            if r.entry_time not in w.index:continue
            q=w.loc[r.entry_time]; q=q.iloc[-1] if isinstance(q,pd.DataFrame) else q
            vals=[(float(c[1]),float(p)) for c,p in q.items() if isinstance(c,tuple) and c[0]==r.direction and pd.notna(p)]
            if not vals:continue
            atm=min(vals,key=lambda t:abs(t[0]-r.spot)); m=json.loads(r.variant); width=int(m["width_steps"])
            wings=sorted([x for x in vals if x[0]>atm[0]]) if r.direction=="CALL" else sorted([x for x in vals if x[0]<atm[0]],reverse=True)
            if len(wings)<width:continue
            wing=wings[width-1]
            out.append({"trade_date":d,"expiry_type":e,"entry_time":r.entry_time,"direction":r.direction,
                        "spot":r.spot,"variant":r.variant,"atm_strike":atm[0],"wing_strike":wing[0],
                        "long_entry":atm[1],"short_entry":wing[1],"hold_minutes":int(m["hold_minutes"])})
    return pd.DataFrame(out)

def simulate(entries,raw):
    if entries.empty:return pd.DataFrame()
    gs=session_maps(raw); setups=entries.drop_duplicates(SETUP); out=[]
    for (d,e),sg in setups.groupby(["trade_date","expiry_type"],sort=False):
        g=gs.get((d,e))
        if g is None:continue
        w=g.pivot_table(index="datetime",columns=["option_type","strike_price"],values="close",aggfunc="last").sort_index()
        for r in sg.itertuples(index=False):
            cs=[(r.direction,r.atm_strike),(r.direction,r.wing_strike)]
            if any(c not in w.columns for c in cs):continue
            end=r.entry_time+pd.Timedelta(minutes=int(r.hold_minutes))
            z=w.loc[(w.index>=r.entry_time)&(w.index<=end),cs].dropna()
            if z.empty or r.entry_time not in z.index:continue
            sp=z[cs[0]]-z[cs[1]]; debit=float(sp.loc[r.entry_time])
            if not np.isfinite(debit) or debit<=0:continue
            stop=.50*debit; target=1.75*debit; a=sp.to_numpy(float); ex=len(a)-1; reason="time"
            if len(a)>1:
                sh=np.flatnonzero(a[1:]<=stop); th=np.flatnonzero(a[1:]>=target)
                si=int(sh[0]+1) if len(sh) else None; ti=int(th[0]+1) if len(th) else None
                if si is not None and (ti is None or si<=ti):ex,reason=si,"stop"
                elif ti is not None:ex,reason=ti,"target"
            rr=z.iloc[ex]
            out.append({"trade_date":d,"expiry_type":e,"entry_time":r.entry_time,"direction":r.direction,
                        "atm_strike":r.atm_strike,"wing_strike":r.wing_strike,"hold_minutes":r.hold_minutes,
                        "long_entry":r.long_entry,"short_entry":r.short_entry,"long_exit":float(rr.iloc[0]),
                        "short_exit":float(rr.iloc[1]),"exit_time":z.index[ex],"exit_reason":reason})
    return entries.merge(pd.DataFrame(out),on=SETUP+["long_entry","short_entry"],how="inner") if out else pd.DataFrame()

def cost(paths,slip):
    if paths.empty:return paths
    cm=OptionCostModel(); x=paths.copy(); d=pd.to_datetime(x.trade_date); x["lot_size"]=np.where(d<=pd.Timestamp("2025-12-30"),75,65)
    x["net_pnl"]=[cm.vertical_debit_spread_net_pnl(a,b,c,d,int(l),slippage_points=slip)
                  for a,b,c,d,l in zip(x.long_entry,x.short_entry,x.long_exit,x.short_exit,x.lot_size)]
    return x

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--data",type=Path,required=True); ap.add_argument("--out",type=Path,default=Path("reports/phase3h")); ap.add_argument("--slippage",nargs="+",type=float,default=[.2,.4]); a=ap.parse_args()
    con=duckdb.connect(); f=con.execute(lead_query(a.data)).df(); raw=con.execute(raw_query(a.data)).df(); con.close()
    f["datetime"]=pd.to_datetime(f.datetime); raw["datetime"]=pd.to_datetime(raw.datetime)
    sig=build_signals(f); ent=choose_entries(sig,raw); p=simulate(ent,raw); a.out.mkdir(parents=True,exist_ok=True); p.to_csv(a.out/"paths.csv",index=False)
    result={"features":len(f),"signals":len(sig),"entries":len(ent),"paths":len(p),"variants":len(grid()),"runs":{}}
    for s in a.slippage:
        t=cost(p,s); root=a.out/f"s{str(s).replace('.','_')}"; root.mkdir(exist_ok=True)
        board,pre=summarize(t,int(f.trade_date.nunique())); board.to_csv(root/"leaderboard.csv",index=False)
        wf,wfs=walk_forward(t); wf.to_csv(root/"walk_forward.csv",index=False)
        block={"slippage":s,"preliminary":pre,"walk_forward":wfs,"gate":wfs.get("gate",pre.get("gate"))}; (root/"summary.json").write_text(json.dumps(block,indent=2,default=str)); result["runs"][str(s)]=block
    (a.out/"summary.json").write_text(json.dumps(result,indent=2,default=str)); print(json.dumps(result,indent=2,default=str))

if __name__=="__main__":main()
