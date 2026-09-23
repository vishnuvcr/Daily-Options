from __future__ import annotations
import argparse,json
from pathlib import Path
import duckdb,numpy as np,pandas as pd
from research.cost_model import OptionCostModel
from research.contracts import nifty_lot_size
from research.phase3g_oi_confirmed_breakout import summarize,walk_forward

GRID=[{"lookback":l,"persist":p,"threshold":t,"expiry_type":e,"width_steps":w,"hold_minutes":h}
      for l in (1,3) for p in (1,2) for t in (0.001,0.002)
      for e in ("WEEK","MONTH") for w in (1,2) for h in (15,30,60)]
SETUP=["trade_date","expiry_type","entry_time","direction","atm_strike","wing_strike","hold_minutes"]

def lead_sql(root):
    g=(root/"**"/"*.parquet").as_posix()
    return f"""
    WITH o AS (
      SELECT datetime,CAST(date AS DATE) trade_date,expiry_type,option_type,
             CAST(strike_price AS DOUBLE) strike_price,CAST(spot AS DOUBLE) spot,
             CAST(close AS DOUBLE) close_px
      FROM read_parquet('{g}',union_by_name=true)
      WHERE close>0 AND strike_type='ATM'
    ),
    p AS (
      SELECT datetime,trade_date,expiry_type,strike_price,MAX(spot) spot,
             MAX(CASE WHEN option_type='CALL' THEN close_px END) call_px,
             MAX(CASE WHEN option_type='PUT' THEN close_px END) put_px
      FROM o GROUP BY ALL
    )
    SELECT datetime,trade_date,expiry_type,strike_price,spot,call_px,put_px,
           LN(call_px/LAG(call_px) OVER(
             PARTITION BY trade_date,expiry_type,strike_price ORDER BY datetime)) call_ret1,
           LN(put_px/LAG(put_px) OVER(
             PARTITION BY trade_date,expiry_type,strike_price ORDER BY datetime)) put_ret1,
           LN(spot/LAG(spot) OVER(
             PARTITION BY trade_date ORDER BY datetime)) spot_ret1,
           LN(call_px/LAG(call_px,3) OVER(
             PARTITION BY trade_date,expiry_type,strike_price ORDER BY datetime)) call_ret3,
           LN(put_px/LAG(put_px,3) OVER(
             PARTITION BY trade_date,expiry_type,strike_price ORDER BY datetime)) put_ret3,
           LN(spot/LAG(spot,3) OVER(
             PARTITION BY trade_date ORDER BY datetime)) spot_ret3
    FROM p
    WHERE STRFTIME(datetime+INTERVAL '5 hours 30 minutes','%H:%M:%S')
      BETWEEN '09:30:00' AND '12:30:00'
    ORDER BY trade_date,expiry_type,datetime
    """

def raw_sql(root):
    g=(root/"**"/"*.parquet").as_posix()
    return f"""
    SELECT datetime,CAST(date AS DATE) trade_date,expiry_type,option_type,
           CAST(strike_price AS DOUBLE) strike_price,CAST(close AS DOUBLE) close
    FROM read_parquet('{g}',union_by_name=true)
    WHERE close>0 AND STRFTIME(datetime+INTERVAL '5 hours 30 minutes','%H:%M:%S')
      BETWEEN '09:20:00' AND '14:45:00'
    """

def signals(f):
    out=[]
    for g in GRID:
        z=f[f.expiry_type.eq(g["expiry_type"])].copy()
        z["score"]=((z["call_ret1"]-z["put_ret1"])*0.5-z["spot_ret1"]) if g["lookback"]==1 else ((z["call_ret3"]-z["put_ret3"])*0.5-z["spot_ret3"])
        z=z.replace([np.inf,-np.inf],np.nan).dropna(subset=["score","call_px","put_px","spot"])
        sign=np.sign(z["score"])
        z["persistent"]=sign.ne(0)&sign.eq(sign.shift(1)) if g["persist"]==2 else sign.ne(0)
        z=z[(z["persistent"])&((z["score"]>=g["threshold"])|(z["score"]<=-g["threshold"]))]
        z=z.sort_values(["trade_date","datetime"]).drop_duplicates("trade_date")
        for r in z.itertuples():
            out.append({"trade_date":r.trade_date,"expiry_type":r.expiry_type,"signal_time":r.datetime,
                        "entry_time":r.datetime+pd.Timedelta(minutes=1),"spot":float(r.spot),
                        "direction":"CALL" if r.score>0 else "PUT","variant":json.dumps(g,sort_keys=True)})
    return pd.DataFrame(out)

def maps(raw):
    return {k:g.sort_values("datetime") for k,g in raw.groupby(["trade_date","expiry_type"],sort=False)}

def make_entries(sig,raw):
    if sig.empty:return pd.DataFrame()
    gs=maps(raw); out=[]
    for (d,e),sg in sig.groupby(["trade_date","expiry_type"],sort=False):
        g=gs.get((d,e))
        if g is None:continue
        w=g.pivot_table(index="datetime",columns=["option_type","strike_price"],values="close",aggfunc="last").sort_index()
        for r in sg.itertuples(index=False):
            if r.entry_time not in w.index:continue
            q=w.loc[r.entry_time]; q=q.iloc[-1] if isinstance(q,pd.DataFrame) else q
            vals=[(float(c[1]),float(p)) for c,p in q.items() if isinstance(c,tuple) and c[0]==r.direction and pd.notna(p)]
            if not vals:continue
            atm=min(vals,key=lambda x:abs(x[0]-r.spot)); meta=json.loads(r.variant); width=int(meta["width_steps"])
            wings=sorted([x for x in vals if x[0]>atm[0]]) if r.direction=="CALL" else sorted([x for x in vals if x[0]<atm[0]],reverse=True)
            if len(wings)<width:continue
            wing=wings[width-1]
            out.append({"trade_date":d,"expiry_type":e,"entry_time":r.entry_time,"direction":r.direction,
                        "variant":r.variant,"atm_strike":atm[0],"wing_strike":wing[0],"long_entry":atm[1],
                        "short_entry":wing[1],"hold_minutes":int(meta["hold_minutes"])})
    return pd.DataFrame(out)

def paths(ent,raw):
    if ent.empty:return pd.DataFrame()
    gs=maps(raw); out=[]
    for (d,e),sg in ent.drop_duplicates(SETUP).groupby(["trade_date","expiry_type"],sort=False):
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
            if debit<=0:continue
            a=sp.to_numpy(float); stop=.5*debit; target=1.75*debit; ex=len(a)-1; reason="time"
            if len(a)>1:
                si=np.flatnonzero(a[1:]<=stop);ti=np.flatnonzero(a[1:]>=target)
                s=int(si[0]+1) if len(si) else None;t=int(ti[0]+1) if len(ti) else None
                if s is not None and (t is None or s<=t):ex,reason=s,"stop"
                elif t is not None:ex,reason=t,"target"
            rr=z.iloc[ex]
            out.append({"trade_date":d,"expiry_type":e,"entry_time":r.entry_time,"direction":r.direction,
                        "atm_strike":r.atm_strike,"wing_strike":r.wing_strike,"hold_minutes":r.hold_minutes,
                        "long_entry":r.long_entry,"short_entry":r.short_entry,"long_exit":float(rr.iloc[0]),
                        "short_exit":float(rr.iloc[1]),"exit_time":z.index[ex]})
    return ent.merge(pd.DataFrame(out),on=SETUP+["long_entry","short_entry"],how="inner") if out else pd.DataFrame()

def add_cost(x,slip):
    if x.empty:return x
    cm=OptionCostModel(); y=x.copy(); d=pd.to_datetime(y.trade_date); y["lot_size"]=np.where(d<=pd.Timestamp("2025-12-30"),75,65)
    y["net_pnl"]=[cm.vertical_debit_spread_net_pnl(a,b,c,d,int(l),slippage_points=slip) for a,b,c,d,l in zip(y.long_entry,y.short_entry,y.long_exit,y.short_exit,y.lot_size)]
    return y

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--data",type=Path,required=True);ap.add_argument("--out",type=Path,default=Path("reports/phase3h_clean"));a=ap.parse_args()
    con=duckdb.connect();f=con.execute(lead_sql(a.data)).df();raw=con.execute(raw_sql(a.data)).df();con.close()
    f["datetime"]=pd.to_datetime(f.datetime);raw["datetime"]=pd.to_datetime(raw.datetime)
    sig=signals(f);ent=make_entries(sig,raw);p=paths(ent,raw);a.out.mkdir(parents=True,exist_ok=True);p.to_csv(a.out/"paths.csv",index=False)
    result={"features":len(f),"signals":len(sig),"entries":len(ent),"paths":len(p),"variants":len(GRID)}
    for s in (.20,.40):
        t=add_cost(p,s);r=a.out/f"s{str(s).replace('.','_')}";r.mkdir(exist_ok=True);b,pre=summarize(t,int(f.trade_date.nunique()));b.to_csv(r/"leaderboard.csv",index=False);wf,wfs=walk_forward(t);wf.to_csv(r/"walk_forward.csv",index=False);result[str(s)]={"preliminary":pre,"walk_forward":wfs}
    (a.out/"summary.json").write_text(json.dumps(result,indent=2,default=str));print(json.dumps(result,indent=2,default=str))

if __name__=="__main__":main()
