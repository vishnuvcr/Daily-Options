from __future__ import annotations
import argparse, json, math
from pathlib import Path
import duckdb
import numpy as np
import pandas as pd
from research.cost_model import OptionCostModel

ENTRY_TIMES=("14:30:00","14:45:00","15:00:00")
SKEW_THRESHOLDS=(0.10,0.15)
JUMP_MAX=(0.0030,0.0050)
RV_MIN=(1.00,1.25)
WIDTHS=(1,2)
HOLDS=(15,30)
STOPS=(1.25,1.50)
TARGET_RATIO=0.50
START_DATE="2021-05-27"
END_DATE="2026-08-04"

def expiry_files(root: Path):
    opts = root/"options"/"NIFTY"
    files = []
    for p in sorted(opts.glob("*.parquet")):
        try:
            d = pd.Timestamp(p.stem).date()
            files.append((d,p))
        except Exception:
            continue
    if not files:
        raise FileNotFoundError(f"No exact-expiry NIFTY files in {opts}")
    return files

def expiry_for_day(files, trade_date):
    td=pd.Timestamp(trade_date).date()
    fut=[(d,p) for d,p in files if d>=td]
    if not fut:
        return None
    return min(fut,key=lambda x:x[0])

def load_spot(root: Path):
    p=root/"index"/"NIFTY.parquet"
    con=duckdb.connect()
    q=f"""
    WITH b AS (
      SELECT CAST(timestamp AS TIMESTAMP) AS ts,
             CAST(trading_day AS DATE) AS trade_date,
             CAST(close AS DOUBLE) AS close
      FROM read_parquet('{p}')
      WHERE CAST(trading_day AS DATE) BETWEEN DATE '{START_DATE}' AND DATE '{END_DATE}'
        AND close>0
    ), r AS (
      SELECT *,
             close/LAG(close,1) OVER(PARTITION BY trade_date ORDER BY ts)-1 AS ret1,
             close/LAG(close,10) OVER(PARTITION BY trade_date ORDER BY ts)-1 AS ret10,
             STDDEV_SAMP(close/LAG(close,1) OVER(PARTITION BY trade_date ORDER BY ts)-1)
               OVER(PARTITION BY trade_date ORDER BY ts ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS rv20
      FROM b
    )
    SELECT * EXCLUDE(ret1),
           rv20/NULLIF(
             AVG(rv20) OVER(PARTITION BY trade_date ORDER BY ts ROWS BETWEEN 119 PRECEDING AND CURRENT ROW),0
           ) AS rv_ratio
    FROM r
    WHERE ret10 IS NOT NULL
      AND rv20 IS NOT NULL
      AND CAST(ts AS TIME) IN (
        TIME '14:30:00',TIME '14:45:00',TIME '15:00:00'
      )
    ORDER BY trade_date,ts
    """
    x=con.execute(q).df()
    con.close()
    if x.empty:
        return x
    x["trade_date"]=pd.to_datetime(x["trade_date"]).dt.date
    x["ts"]=pd.to_datetime(x["ts"]).dt.floor("min")
    return x

def variant_grid():
    return [
        dict(entry_time=e,skew=s,jump=j,rv=r,width=w,hold=h,stop=st,side=side)
        for e in ENTRY_TIMES
        for s in SKEW_THRESHOLDS
        for j in JUMP_MAX
        for r in RV_MIN
        for w in WIDTHS
        for h in HOLDS
        for st in STOPS
        for side in ("PUT","CALL")
    ]

def signal_candidates(spot, variants):
    rows=[]
    for v in variants:
        m=spot[
            (spot.ts.dt.strftime("%H:%M:%S")==v["entry_time"])
            & (spot.ret10.abs()<=v["jump"])
            & (spot.rv_ratio>=v["rv"])
        ].copy()
        if v["side"]=="PUT":
            m=m[m.ret10>=0]
        else:
            m=m[m.ret10<=0]
        if m.empty:
            continue
        m["variant_id"]=(
            f'{v["entry_time"]}|sk{s if (s:=v["skew"]) else v["skew"]}|'
            f'j{v["jump"]}|rv{v["rv"]}|w{v["width"]}|h{v["hold"]}|'
            f'stop{v["stop"]}|{v["side"]}'
        )
        rows.append(m[["trade_date","ts","close","ret10","rv_ratio","variant_id"]])
    return pd.concat(rows,ignore_index=True) if rows else pd.DataFrame()

def load_option_quotes(root, signals):
    files=expiry_files(root)
    chosen={}
    for d in sorted(signals.trade_date.unique()):
        ef=expiry_for_day(files,d)
        if ef:
            chosen[d]=ef
    if not chosen:
        return pd.DataFrame()
    wanted=signals[["trade_date","ts","close"]].drop_duplicates().copy()
    wanted["entry_ts"]=wanted["ts"]+pd.Timedelta(minutes=1)
    con=duckdb.connect()
    con.register("wanted",wanted)
    chunks=[]
    for expiry_date,path in sorted(set(chosen.values()), key=lambda x:x[0]):
        dates=[d for d,(ed,_) in chosen.items() if ed==expiry_date]
        if not dates: continue
        vals=",".join([f"DATE '{d}'" for d in dates])
        q=f"""
        SELECT CAST(o.timestamp AS TIMESTAMP) ts,
               CAST(o.trading_day AS DATE) trade_date,
               CAST(o.strike AS DOUBLE) strike,
               CAST(o.option_type AS VARCHAR) option_type,
               CAST(o.open AS DOUBLE) open,
               CAST(o.close AS DOUBLE) close,
               CAST(o.volume AS DOUBLE) volume,
               CAST(o.open_interest AS DOUBLE) oi
        FROM read_parquet('{path}') o
        JOIN wanted w
          ON CAST(o.trading_day AS DATE)=w.trade_date
         AND CAST(o.timestamp AS TIMESTAMP) IN (w.ts,w.entry_ts)
        WHERE CAST(o.trading_day AS DATE) IN ({vals})
          AND o.close>0
        """
        z=con.execute(q).df()
        if not z.empty:
            z["expiry"]=expiry_date
            chunks.append(z)
    con.close()
    return pd.concat(chunks,ignore_index=True) if chunks else pd.DataFrame()

def build_setups(signal_df, quotes):
    setups=[]
    signal_keys=signal_df[["trade_date","ts","close","variant_id"]].drop_duplicates()
    if quotes.empty: return pd.DataFrame()
    for (d,ts),g in quotes.groupby(["trade_date","ts"],sort=False):
        meta=signal_keys[(signal_keys.trade_date==d)&(signal_keys.ts==ts)]
        if meta.empty: continue
        spot=float(meta.iloc[0].close)
        strikes=np.sort(g.strike.dropna().unique())
        if len(strikes)<7: continue
        atm_i=int(np.argmin(np.abs(strikes-spot)))
        for side in ("PUT","CALL"):
            if side=="PUT":
                short_i=atm_i-2
            else:
                short_i=atm_i+2
            for width in WIDTHS:
                wing_i=short_i-width if side=="PUT" else short_i+width
                if short_i<0 or wing_i<0 or short_i>=len(strikes) or wing_i>=len(strikes):
                    continue
                short_strike=float(strikes[short_i]); wing_strike=float(strikes[wing_i])
                sel=g[g.option_type==side]
                sh=sel[sel.strike==short_strike]
                wh=sel[sel.strike==wing_strike]
                sig=meta.iloc[0]
                sigp=quotes[(quotes.trade_date==d)&(quotes.ts==ts)&(quotes.strike==short_strike)&(quotes.option_type==side)].head(1)
                sigw=quotes[(quotes.trade_date==d)&(quotes.ts==ts)&(quotes.strike==wing_strike)&(quotes.option_type==side)].head(1)
                if sigp.empty or sigw.empty: continue
                p=float(sigp.iloc[0].close); w=float(sigw.iloc[0].close)
                if p<=w: continue
                cross_call=quotes[(quotes.trade_date==d)&(quotes.ts==ts)&(quotes.strike==float(strikes[min(atm_i+2,len(strikes)-1)]))&(quotes.option_type=="CALL")]
                cross_put=quotes[(quotes.trade_date==d)&(quotes.ts==ts)&(quotes.strike==float(strikes[max(atm_i-2,0)]))&(quotes.option_type=="PUT")]
                if cross_call.empty or cross_put.empty: continue
                c=float(cross_call.iloc[0].close)
                pp=float(cross_put.iloc[0].close)
                denom=max(1e-9,pp+c)
                skew=(pp-c)/denom
                vol_imb=(float(cross_put.iloc[0].volume)-float(cross_call.iloc[0].volume))/max(1e-9,float(cross_put.iloc[0].volume)+float(cross_call.iloc[0].volume))
                oi_imb=(float(cross_put.iloc[0].oi)-float(cross_call.iloc[0].oi))/max(1e-9,float(cross_put.iloc[0].oi)+float(cross_call.iloc[0].oi))
                setups.append({
                    "trade_date":d,"ts":ts,"entry_ts":ts+pd.Timedelta(minutes=1),
                    "expiry":sigp.iloc[0]["expiry"],"side":side,"width":width,
                    "short_strike":short_strike,"wing_strike":wing_strike,
                    "short_signal":p,"wing_signal":w,"skew":skew,
                    "vol_imb":vol_imb,"oi_imb":oi_imb,
                    "spot_ret10":float(sig.ret10),"rv_ratio":float(sig.rv_ratio)
                })
    return pd.DataFrame(setups)

def filter_setups(setups, variants):
    out=[]
    if setups.empty:return pd.DataFrame()
    for v in variants:
        s=setups[
            (setups.side==v["side"])&(setups.width==v["width"])&
            (setups.skew>=v["skew"] if v["side"]=="PUT" else setups.skew<=-v["skew"])&
            (setups.vol_imb>=0 if v["side"]=="PUT" else setups.vol_imb<=0)&
            (setups.oi_imb>=0 if v["side"]=="PUT" else setups.oi_imb<=0)&
            (setups.spot_ret10>=0 if v["side"]=="PUT" else setups.spot_ret10<=0)&
            (setups.rv_ratio>=v["rv"])&
            (setups.spot_ret10.abs()<=v["jump"])&
            (setups.ts.dt.strftime("%H:%M:%S")==v["entry_time"])
        ].copy()
        if not s.empty:
            s["variant_id"]=(
                f'{v["entry_time"]}|sk{v["skew"]}|j{v["jump"]}|rv{v["rv"]}|'
                f'w{v["width"]}|h{v["hold"]}|stop{v["stop"]}|{v["side"]}'
            )
            out.append(s)
    return pd.concat(out,ignore_index=True) if out else pd.DataFrame()

def lot(d):
    d=pd.Timestamp(d).date()
    if d<pd.Timestamp("2024-04-26").date():return 50
    if d<pd.Timestamp("2024-11-21").date():return 25
    if d<pd.Timestamp("2026-01-06").date():return 75
    return 65

def simulate(root, setups, out, slippage):
    if setups.empty:return pd.DataFrame()
    max_hold=max(HOLDS)
    files={d:path for d,path in expiry_files(root)}
    legs=set()
    for _,r in setups.iterrows():
        legs.add((r.trade_date,r.entry_ts.date(),r.expiry,r.side,r.short_strike,r.wing_strike))
    chunks=[]
    con=duckdb.connect()
    con.register("legs",pd.DataFrame(list(legs),columns=["trade_date","entry_day","expiry","side","short_strike","wing_strike"]))
    for expiry_date,path in sorted(files.items()):
        active=con.execute("SELECT COUNT(*) FROM legs WHERE expiry=?", [expiry_date]).fetchone()[0]
        if not active: continue
        q=f"""
        SELECT CAST(o.timestamp AS TIMESTAMP) ts,
               CAST(o.trading_day AS DATE) trade_date,
               CAST(o.strike AS DOUBLE) strike,
               CAST(o.option_type AS VARCHAR) option_type,
               CAST(o.high AS DOUBLE) high,
               CAST(o.low AS DOUBLE) low,
               CAST(o.close AS DOUBLE) close
        FROM read_parquet('{path}') o
        JOIN legs l
          ON l.expiry=DATE '{expiry_date}'
         AND CAST(o.trading_day AS DATE)=l.trade_date
         AND o.option_type=l.side
         AND CAST(o.strike AS DOUBLE) IN(l.short_strike,l.wing_strike)
         AND CAST(o.timestamp AS TIMESTAMP)>=CAST(l.trade_date AS TIMESTAMP)
         AND CAST(o.timestamp AS TIMESTAMP)<=CAST(l.trade_date AS TIMESTAMP)+INTERVAL '23 hours 59 minutes'
        WHERE o.close>0
        """
        z=con.execute(q).df()
        if not z.empty:z["expiry"]=expiry_date;chunks.append(z)
    con.close()
    if not chunks:return pd.DataFrame()
    win=pd.concat(chunks,ignore_index=True)
    win["ts"]=pd.to_datetime(win.ts).dt.floor("min")
    trades=[]
    for _,r in setups.drop_duplicates(["trade_date","entry_ts","expiry","side","width","short_strike","wing_strike"]).iterrows():
        q=win[(win.trade_date==r.trade_date)&(win.expiry==r.expiry)&(win.option_type==r.side)&(win.strike.isin([r.short_strike,r.wing_strike]))&(win.ts>=r.entry_ts)&(win.ts<=r.entry_ts+pd.Timedelta(minutes=max_hold))]
        if q.empty:continue
        a=q[q.strike==r.short_strike][["ts","high","low","close"]].rename(columns={"high":"shigh","low":"slow","close":"sclose"})
        b=q[q.strike==r.wing_strike][["ts","high","low","close"]].rename(columns={"high":"whigh","low":"wlow","close":"wclose"})
        m=a.merge(b,on="ts").sort_values("ts")
        if m.empty:continue
        for hold in HOLDS:
            mm=m[m.ts<=r.entry_ts+pd.Timedelta(minutes=hold)]
            if mm.empty:continue
            hi=mm.shigh-mm.wlow
            lo=mm.slow-mm.whigh
            for stop in STOPS:
                stopv=float(r.short_signal-r.wing_signal)*stop
                target=float(r.short_signal-r.wing_signal)*TARGET_RATIO
                si=np.flatnonzero(hi>=stopv); ti=np.flatnonzero(lo<=target)
                si=int(si[0]) if len(si) else 10**9
                ti=int(ti[0]) if len(ti) else 10**9
                if si<=ti and si<10**9:ix,reason=si,"STOP"
                elif ti<10**9:ix,reason=ti,"TARGET"
                else:ix,reason=len(mm)-1,"TIME"
                er=mm.iloc[ix]
                net=OptionCostModel().vertical_credit_spread_net_pnl(
                    float(r.short_signal),float(r.wing_signal),
                    float(er.sclose),float(er.wclose),lot(r.trade_date),
                    slippage_points=slippage
                )
                trades.append({
                    "trade_date":r.trade_date,"ts":r.ts,"expiry":r.expiry,
                    "side":r.side,"width":r.width,"hold":hold,"stop":stop,
                    "net_pnl":net,"reason":reason,"skew":r.skew,"vol_imb":r.vol_imb,
                    "oi_imb":r.oi_imb,"entry_credit":float(r.short_signal-r.wing_signal)
                })
    t=pd.DataFrame(trades)
    if t.empty:return t
    t.to_csv(out/"phase17_trades.csv",index=False)
    board=[]
    days=t.trade_date.nunique()
    for vid,g in filter_setups(setups,variant_grid()).groupby("variant_id"):
        gg=t.copy()
        # Variant identity is reconstructed from setup properties by joins below in run()
    return t

def summarize(trades, signal_count, slippage, out):
    rows=[]
    if trades.empty:
        return {"trades":0,"variants":0,"target_qualified":0,"best":None,"slippage":slippage}
    # Recreate variant ID using all frozen dimensions.
    # The trade table stores only dimensions needed for exact grouping, while skew/jump/rv are recoverable by filtered signal merge in run().
    board=trades.groupby("variant_id").agg(
        trades=("net_pnl","size"),
        total_net=("net_pnl","sum"),
        mean_trade=("net_pnl","mean"),
        win_rate=("net_pnl",lambda s:float((s>0).mean()))
    ).reset_index()
    day=trades.groupby(["variant_id","trade_date"]).net_pnl.sum().reset_index()
    ad=day.groupby("variant_id").net_pnl.mean().rename("mean_active_day_net")
    board=board.merge(ad,on="variant_id")
    board["profit_factor"]=board.groupby("variant_id").net_pnl if False else 0.0
    board["target_qualified"]=board.mean_active_day_net>=1000
    board=board.sort_values("mean_active_day_net",ascending=False)
    board.to_csv(out/"phase17_leaderboard.csv",index=False)
    best=board.iloc[0].to_dict() if not board.empty else None
    return {
        "trades":int(len(trades)),
        "variants":int(board.variant_id.nunique()),
        "target_qualified":int(board.target_qualified.sum()),
        "positive_variants":int((board.mean_active_day_net>0).sum()),
        "best":best,
        "signal_rows":int(signal_count),
        "slippage":slippage
    }

def variant_id(v):
    return f'{v["entry_time"]}|sk{v["skew"]}|j{v["jump"]}|rv{v["rv"]}|w{v["width"]}|h{v["hold"]}|stop{v["stop"]}|{v["side"]}'

def run(root:Path,out:Path,slippage:float):
    out.mkdir(parents=True,exist_ok=True)
    spot=load_spot(root)
    if spot.empty: raise RuntimeError("No NIFTY index rows")
    variants=variant_grid()
    candidates=signal_candidates(spot,variants)
    # Quote loading is done for every candidate timestamp once; variant filtering happens only after exact expiry/option pressure is known.
    q=load_option_quotes(root,candidates)
    if q.empty: raise RuntimeError("No exact-expiry option quote rows for candidate timestamps")
    setups=build_setups(candidates,q)
    filtered=filter_setups(setups,variants)
    if filtered.empty:
        summary={"trades":0,"variants":len(variants),"target_qualified":0,"positive_variants":0,"best":None,"signal_rows":len(candidates),"slippage":slippage}
        (out/"phase17_summary.json").write_text(json.dumps(summary,indent=2,default=str))
        return summary
    # Map each executable setup to each matching variant; simulate unique setups once.
    unique=filtered.drop_duplicates(["trade_date","ts","entry_ts","expiry","side","width","short_strike","wing_strike"]).copy()
    trades=simulate(root,unique,out,slippage)
    if trades.empty:
        summary={"trades":0,"variants":len(variants),"target_qualified":0,"positive_variants":0,"best":None,"signal_rows":len(candidates),"slippage":slippage}
        (out/"phase17_summary.json").write_text(json.dumps(summary,indent=2,default=str))
        return summary
    # Assign variants by matching dimensions.
    rows=[]
    for _,v in filtered.iterrows():
        mask=(
            (trades.trade_date==v.trade_date)&(trades.ts==v.ts)&(trades.expiry==v.expiry)&
            (trades.side==v.side)&(trades.width==v.width)&
            (trades.short_strike==v.short_strike)&(trades.wing_strike==v.wing_strike)
        )
        x=trades[mask].copy()
        if x.empty:continue
        x["variant_id"]=variant_id(next(z for z in variants if variant_id(z)==v.variant_id))
        rows.append(x)
    final=pd.concat(rows,ignore_index=True) if rows else pd.DataFrame()
    final.to_csv(out/"phase17_trades.csv",index=False)
    summary=summarize(final,len(candidates),slippage,out)
    (out/"phase17_summary.json").write_text(json.dumps(summary,indent=2,default=str))
    print(json.dumps(summary,indent=2,default=str))
    return summary

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--data",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--slippage",type=float,default=.20)
    args=ap.parse_args()
    run(args.data,args.out,args.slippage)
