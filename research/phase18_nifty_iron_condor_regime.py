from __future__ import annotations
import argparse, json
from pathlib import Path
import duckdb, numpy as np, pandas as pd
from research.cost_model import OptionCostModel

ENTRY_TIMES=("14:30:00","14:45:00","15:00:00")
SHORT_OFFSETS=(2,3)
WING_WIDTHS=(2,3)
ABS_RET_MAX=(0.0015,0.0030)
RV_RATIO_MAX=(1.00,1.25)
HOLDS=(15,30)
STOPS=(1.25,1.50)
TARGET_RATIO=0.50
MAX_ENTRY_DELAY_MINUTES=3
START_DATE="2021-05-27"
END_DATE="2026-08-04"

def expiry_files(root: Path):
    out=[]
    for p in sorted((root/"options"/"NIFTY").glob("*.parquet")):
        try: out.append((pd.Timestamp(p.stem).date(),p))
        except Exception: pass
    if not out: raise FileNotFoundError("No exact-expiry NIFTY files")
    return out

def expiry_for_day(files,d):
    fut=[x for x in files if x[0]>=pd.Timestamp(d).date()]
    return min(fut,key=lambda x:x[0]) if fut else None

def ist_wall(x):
    return pd.to_datetime(x,utc=True).dt.tz_convert("Asia/Kolkata").dt.tz_localize(None).dt.floor("min")

def load_spot(root):
    p=root/"index"/"NIFTY.parquet"
    con=duckdb.connect(); con.execute("SET TimeZone='Asia/Kolkata'")
    q=f"""
    WITH b AS (
      SELECT "timestamp" ts, CAST(trading_day AS DATE) trade_date,
             CAST("close" AS DOUBLE) close
      FROM read_parquet('{p}')
      WHERE CAST(trading_day AS DATE) BETWEEN DATE '{START_DATE}' AND DATE '{END_DATE}'
        AND "close">0
    ),
    r AS (
      SELECT *, close/LAG(close,10) OVER(PARTITION BY trade_date ORDER BY ts)-1 AS ret10,
             close/LAG(close,1) OVER(PARTITION BY trade_date ORDER BY ts)-1 AS ret1
      FROM b
    ),
    v AS (
      SELECT *, STDDEV_SAMP(ret1) OVER(PARTITION BY trade_date ORDER BY ts ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS rv20
      FROM r
    ),
    z AS (
      SELECT *, rv20/NULLIF(AVG(rv20) OVER(PARTITION BY trade_date ORDER BY ts ROWS BETWEEN 119 PRECEDING AND CURRENT ROW),0) AS rv_ratio
      FROM v
    )
    SELECT trade_date,ts,close,ret10,rv_ratio
    FROM z
    WHERE ret10 IS NOT NULL AND rv_ratio IS NOT NULL
      AND strftime(ts,'%H:%M:%S') IN ('14:30:00','14:45:00','15:00:00')
    ORDER BY trade_date,ts
    """
    x=con.execute(q).df(); con.close()
    x["trade_date"]=pd.to_datetime(x.trade_date).dt.date
    x["ts"]=ist_wall(x.ts)
    return x

def variant_grid():
    return [
      dict(entry_time=e,short_offset=so,wing_width=ww,abs_ret=ar,rv_max=rv,hold=h,stop=st)
      for e in ENTRY_TIMES for so in SHORT_OFFSETS for ww in WING_WIDTHS
      for ar in ABS_RET_MAX for rv in RV_RATIO_MAX for h in HOLDS for st in STOPS
    ]

def variant_id(v):
    return f'{v["entry_time"]}|so{v["short_offset"]}|ww{v["wing_width"]}|r{v["abs_ret"]}|rv{v["rv_max"]}|h{v["hold"]}|s{v["stop"]}'

def load_exact_quotes(root,spot):
    files=expiry_files(root)
    chosen={d:expiry_for_day(files,d) for d in spot.trade_date.unique()}
    chosen={d:x for d,x in chosen.items() if x is not None}
    wanted=spot[["trade_date","ts"]].drop_duplicates().copy()
    wanted["end_ts"]=wanted.ts+pd.Timedelta(minutes=MAX_ENTRY_DELAY_MINUTES)
    con=duckdb.connect(); con.execute("SET TimeZone='Asia/Kolkata'"); con.register("wanted",wanted)
    chunks=[]
    for expiry_date,path in sorted(set(chosen.values()),key=lambda x:x[0]):
        dates=[d for d,(ed,_) in chosen.items() if ed==expiry_date]
        if not dates: continue
        vals=",".join(f"DATE '{d}'" for d in dates)
        q=f"""
        SELECT o."timestamp" ts, CAST(o.trading_day AS DATE) trade_date,
               CAST(o.strike AS DOUBLE) strike, CAST(o.option_type AS VARCHAR) option_type,
               CAST(o.open AS DOUBLE) open_px, CAST(o.high AS DOUBLE) high,
               CAST(o.low AS DOUBLE) low, CAST(o."close" AS DOUBLE) close_px
        FROM read_parquet('{path}') o
        JOIN wanted w ON CAST(o.trading_day AS DATE)=w.trade_date
                     AND o."timestamp">=w.ts AND o."timestamp"<=w.end_ts
        WHERE CAST(o.trading_day AS DATE) IN ({vals}) AND o."close">0
        """
        z=con.execute(q).df()
        if not z.empty:
            z["ts"]=ist_wall(z.ts); z["expiry"]=expiry_date; chunks.append(z)
    con.close()
    return pd.concat(chunks,ignore_index=True) if chunks else pd.DataFrame()

def build_setups(spot,quotes):
    rows=[]
    if quotes.empty: return pd.DataFrame()
    for (d,ts),sm in spot.groupby(["trade_date","ts"],sort=False):
        sm=sm.iloc[0]
        q=quotes[(quotes.trade_date==d)&(quotes.ts>=ts)&(quotes.ts<=ts+pd.Timedelta(minutes=MAX_ENTRY_DELAY_MINUTES))]
        sig=q[q.ts==ts]
        if sig.empty: continue
        strikes=np.sort(sig.strike.dropna().unique())
        if len(strikes)<9: continue
        atm=int(np.argmin(np.abs(strikes-float(sm.close))))
        for so in SHORT_OFFSETS:
            pi=atm-so; ci=atm+so
            if pi<0 or ci>=len(strikes): continue
            put_short=float(strikes[pi]); call_short=float(strikes[ci])
            for ww in WING_WIDTHS:
                pwi=pi-ww; cwi=ci+ww
                if pwi<0 or cwi>=len(strikes): continue
                put_wing=float(strikes[pwi]); call_wing=float(strikes[cwi])
                target_legs=[
                    ("PE",put_short,"put_short"),("PE",put_wing,"put_wing"),
                    ("CE",call_short,"call_short"),("CE",call_wing,"call_wing")
                ]
                leg_rows={}; ok=True
                for code,strike,name in target_legs:
                    z=q[(q.option_type==code)&(q.strike==strike)&(q.ts>ts)]
                    if z.empty: ok=False; break
                    leg_rows[name]=z
                if not ok: continue
                common=None
                for z in leg_rows.values():
                    s=set(z.ts)
                    common=s if common is None else common.intersection(s)
                common=sorted(common) if common else []
                if not common: continue
                entry_ts=common[0]
                vals={}
                for name,z in leg_rows.items():
                    row=z[z.ts==entry_ts].head(1)
                    if row.empty: ok=False; break
                    vals[name]=float(row.iloc[0].open_px)
                if not ok: continue
                credit=vals["put_short"]-vals["put_wing"]+vals["call_short"]-vals["call_wing"]
                if credit<=0: continue
                rows.append({
                  "trade_date":d,"ts":ts,"entry_ts":entry_ts,
                  "entry_delay_min":float((entry_ts-ts).total_seconds()/60),
                  "expiry":sig.iloc[0].expiry,
                  "short_offset":so,"wing_width":ww,
                  "put_short":put_short,"put_wing":put_wing,
                  "call_short":call_short,"call_wing":call_wing,
                  "put_short_entry":vals["put_short"],"put_wing_entry":vals["put_wing"],
                  "call_short_entry":vals["call_short"],"call_wing_entry":vals["call_wing"],
                  "entry_credit":credit,"spot_ret10":float(sm.ret10),"rv_ratio":float(sm.rv_ratio)
                })
    return pd.DataFrame(rows)

def filter_setups(setups):
    out=[]
    for v in variant_grid():
        s=setups[
          (setups.ts.dt.strftime("%H:%M:%S")==v["entry_time"])&
          (setups.short_offset==v["short_offset"])&
          (setups.wing_width==v["wing_width"])&
          (setups.spot_ret10.abs()<=v["abs_ret"])&
          (setups.rv_ratio<=v["rv_max"])
        ].copy()
        if s.empty: continue
        s["variant_id"]=variant_id(v); s["hold"]=v["hold"]; s["stop"]=v["stop"]; out.append(s)
    return pd.concat(out,ignore_index=True) if out else pd.DataFrame()

def lot(d):
    d=pd.Timestamp(d).date()
    if d<pd.Timestamp("2024-04-26").date(): return 50
    if d<pd.Timestamp("2024-11-21").date(): return 25
    if d<pd.Timestamp("2026-01-06").date(): return 75
    return 65

def simulate(root,filtered,slippage):
    if filtered.empty: return pd.DataFrame()
    files=dict(expiry_files(root))
    unique=filtered.drop_duplicates(["trade_date","entry_ts","expiry","put_short","put_wing","call_short","call_wing"]).copy()
    unique["setup_key"]=(
        unique.trade_date.astype(str)+"|"+unique.entry_ts.astype(str)+"|"+unique.expiry.astype(str)+"|"+
        unique.put_short.astype(str)+"|"+unique.put_wing.astype(str)+"|"+
        unique.call_short.astype(str)+"|"+unique.call_wing.astype(str)
    )
    unique=unique.drop_duplicates("setup_key").reset_index(drop=True)
    unique["setup_id"]=np.arange(len(unique))
    con=duckdb.connect(); con.execute("SET TimeZone='Asia/Kolkata'")
    con.register("legs",unique[["setup_id","setup_key","trade_date","entry_ts","expiry","put_short","put_wing","call_short","call_wing"]])
    chunks=[]
    for expiry_date,path in sorted(files.items()):
        active=int(con.execute("SELECT COUNT(*) FROM legs WHERE expiry=?", [expiry_date]).fetchone()[0])
        if active==0: continue
        q=f"""
        SELECT l.setup_id,o."timestamp" ts,CAST(o.trading_day AS DATE) trade_date,
               CAST(o.strike AS DOUBLE) strike,CAST(o.option_type AS VARCHAR) option_type,
               CAST(o.high AS DOUBLE) high,CAST(o.low AS DOUBLE) low,CAST(o."close" AS DOUBLE) close_px
        FROM read_parquet('{path}') o
        JOIN legs l ON l.expiry=DATE '{expiry_date}'
          AND CAST(o.trading_day AS DATE)=l.trade_date
          AND ((o.option_type='PE' AND CAST(o.strike AS DOUBLE) IN(l.put_short,l.put_wing))
               OR (o.option_type='CE' AND CAST(o.strike AS DOUBLE) IN(l.call_short,l.call_wing)))
          AND o."timestamp">=l.entry_ts
          AND o."timestamp"<=l.entry_ts+INTERVAL '30 minutes'
        WHERE o."close">0
        """
        z=con.execute(q).df()
        if not z.empty:
            z["ts"]=ist_wall(z.ts); z["expiry"]=expiry_date; chunks.append(z)
    con.close()
    if not chunks: return pd.DataFrame()
    win=pd.concat(chunks,ignore_index=True)
    lookup=unique.set_index("setup_id")
    out=[]
    for sid,g in win.groupby("setup_id",sort=False):
        r=lookup.loc[sid]
        ps=g[g.strike==r.put_short][["ts","high","low","close_px"]].rename(columns={"high":"psh","low":"psl","close_px":"psc"})
        pw=g[g.strike==r.put_wing][["ts","high","low","close_px"]].rename(columns={"high":"pwh","low":"pwl","close_px":"pwc"})
        cs=g[g.strike==r.call_short][["ts","high","low","close_px"]].rename(columns={"high":"csh","low":"csl","close_px":"csc"})
        cw=g[g.strike==r.call_wing][["ts","high","low","close_px"]].rename(columns={"high":"cwh","low":"cwl","close_px":"cwc"})
        m=ps.merge(pw,on="ts").merge(cs,on="ts").merge(cw,on="ts").sort_values("ts")
        if m.empty: continue
        for hold in HOLDS:
            mm=m[m.ts<=r.entry_ts+pd.Timedelta(minutes=hold)]
            if mm.empty: continue
            stop_mults=STOPS
            # Condor marked value: sum of both credit spreads' current debit value.
            stop_value=float(r.entry_credit)
            for stop in stop_mults:
                stopv=float(r.entry_credit)*stop
                target=float(r.entry_credit)*TARGET_RATIO
                current_hi=(mm.psh-mm.pwl)+(mm.csh-mm.cwl)
                current_lo=(mm.psl-mm.pwh)+(mm.csl-mm.cwh)
                si=np.flatnonzero(current_hi>=stopv)
                ti=np.flatnonzero(current_lo<=target)
                si=int(si[0]) if len(si) else 10**9
                ti=int(ti[0]) if len(ti) else 10**9
                if si<=ti and si<10**9: ix,reason=si,"STOP"
                elif ti<10**9: ix,reason=ti,"TARGET"
                else: ix,reason=len(mm)-1,"TIME"
                er=mm.iloc[ix]
                pnl=OptionCostModel().four_leg_defined_net_pnl(
                    r.put_wing_entry,r.put_short_entry,r.call_short_entry,r.call_wing_entry,
                    er.pwc,er.psc,er.csc,er.cwc,lot(r.trade_date),slippage_points=slippage
                )
                out.append({
                  "setup_id":int(sid),"setup_key":r.setup_key,
                  "trade_date":r.trade_date,"ts":r.ts,"expiry":r.expiry,
                  "short_offset":int(r.short_offset),"wing_width":int(r.wing_width),
                  "hold":hold,"stop":stop,"entry_credit":float(r.entry_credit),
                  "entry_delay_min":float(r.entry_delay_min),"net_pnl":pnl,"reason":reason
                })
    return pd.DataFrame(out)

def summarize(trades,signal_rows,out,slippage):
    if trades.empty:
        return {"trades":0,"variants":0,"target_qualified":0,"positive_variants":0,"best":None,"signals":int(signal_rows),"slippage":slippage}
    board=[]
    for vid,g in trades.groupby("variant_id"):
        day=g.groupby("trade_date").net_pnl.sum()
        pos=float(g.loc[g.net_pnl>0,"net_pnl"].sum()); neg=float(-g.loc[g.net_pnl<0,"net_pnl"].sum())
        dd=float((day.cumsum()-day.cumsum().cummax()).min())
        board.append({"variant_id":vid,"trades":len(g),"active_days":len(day),
                      "mean_active_day_net":float(day.mean()),
                      "win_rate":float((g.net_pnl>0).mean()),
                      "profit_factor":pos/max(1e-9,neg),
                      "max_drawdown":dd,"total_net":float(g.net_pnl.sum())})
    b=pd.DataFrame(board).sort_values("mean_active_day_net",ascending=False)
    b.to_csv(out/"phase18_leaderboard.csv",index=False)
    return {"trades":int(len(trades)),"variants":int(len(b)),
            "target_qualified":int((b.mean_active_day_net>=1000).sum()),
            "positive_variants":int((b.mean_active_day_net>0).sum()),
            "best":b.iloc[0].to_dict() if not b.empty else None,
            "signals":int(signal_rows),"slippage":slippage}

def run(root:Path,out:Path,slippage:float):
    out.mkdir(parents=True,exist_ok=True)
    spot=load_spot(root)
    quotes=load_exact_quotes(root,spot)
    setups=build_setups(spot,quotes)
    filtered=filter_setups(setups)
    trades=simulate(root,filtered,slippage)
    if not trades.empty:
        rows=[]
        for _,v in filtered.drop_duplicates(["trade_date","ts","expiry","put_short","put_wing","call_short","call_wing","hold","stop","variant_id"]).iterrows():
            setup_key=(
                str(v.trade_date)+"|"+str(v.entry_ts)+"|"+str(v.expiry)+"|"+
                str(v.put_short)+"|"+str(v.put_wing)+"|"+
                str(v.call_short)+"|"+str(v.call_wing)
            )
            m=trades[
                (trades.setup_key==setup_key)&
                (trades.short_offset==v.short_offset)&
                (trades.wing_width==v.wing_width)&
                (trades.hold==v.hold)&
                (trades.stop==v.stop)
            ].copy()
            if not m.empty:
                m["variant_id"]=v.variant_id
                rows.append(m)
        trades=pd.concat(rows,ignore_index=True) if rows else pd.DataFrame()
    summary=summarize(trades,len(spot),out,slippage)
    summary.update({"quote_rows":int(len(quotes)),"setup_rows":int(len(setups)),"filtered_setup_rows":int(len(filtered))})
    (out/"phase18_summary.json").write_text(json.dumps(summary,indent=2,default=str))
    if not trades.empty: trades.to_csv(out/"phase18_trades.csv",index=False)
    print(json.dumps(summary,indent=2,default=str))
    return summary

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--data",type=Path,required=True); ap.add_argument("--out",type=Path,required=True); ap.add_argument("--slippage",type=float,default=.20)
    a=ap.parse_args(); run(a.data,a.out,a.slippage)
