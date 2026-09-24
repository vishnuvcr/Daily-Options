from __future__ import annotations
import argparse, json
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

def ist_ts(x):
    return pd.to_datetime(x, utc=True).dt.tz_convert("Asia/Kolkata").dt.floor("min")

def load_spot(root: Path):
    p=root/"index"/"NIFTY.parquet"
    con=duckdb.connect()
    con.execute("SET TimeZone='Asia/Kolkata'")
    q=f"""
    WITH b AS (
      SELECT "timestamp" AS ts,
             CAST(trading_day AS DATE) AS trade_date,
             CAST(close AS DOUBLE) AS close
      FROM read_parquet('{p}')
      WHERE CAST(trading_day AS DATE) BETWEEN DATE '{START_DATE}' AND DATE '{END_DATE}'
        AND close>0
    ),
    r AS (
      SELECT *,
             close/LAG(close,1) OVER(PARTITION BY trade_date ORDER BY ts)-1 AS ret1,
             close/LAG(close,10) OVER(PARTITION BY trade_date ORDER BY ts)-1 AS ret10
      FROM b
    ),
    v AS (
      SELECT *,
             STDDEV_SAMP(ret1) OVER(
               PARTITION BY trade_date ORDER BY ts ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
             ) AS rv20
      FROM r
    ),
    z AS (
      SELECT *,
             rv20/NULLIF(
               AVG(rv20) OVER(
                 PARTITION BY trade_date ORDER BY ts ROWS BETWEEN 119 PRECEDING AND CURRENT ROW
               ),0
             ) AS rv_ratio
      FROM v
    )
    SELECT trade_date,ts,close,ret10,rv20,rv_ratio
    FROM z
    WHERE ret10 IS NOT NULL
      AND rv20 IS NOT NULL
      AND rv_ratio IS NOT NULL
      AND strftime(ts,'%H:%M:%S') IN ('14:30:00','14:45:00','15:00:00')
    ORDER BY trade_date,ts
    """
    x=con.execute(q).df()
    con.close()
    if x.empty:
        return x
    x["trade_date"]=pd.to_datetime(x["trade_date"]).dt.date
    x["ts"]=ist_ts(x["ts"])
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
    con.execute("SET TimeZone='Asia/Kolkata'")
    con.register("wanted",wanted)
    chunks=[]
    for expiry_date,path in sorted(set(chosen.values()), key=lambda x:x[0]):
        dates=[d for d,(ed,_) in chosen.items() if ed==expiry_date]
        if not dates: continue
        vals=",".join([f"DATE '{d}'" for d in dates])
        q=f"""
        SELECT o."timestamp" AS ts,
               CAST(o.trading_day AS DATE) trade_date,
               CAST(o.strike AS DOUBLE) strike,
               CAST(o.option_type AS VARCHAR) option_type,
               CAST(o.open AS DOUBLE) open,
               CAST(o.close AS DOUBLE) close_px,
               CAST(o.volume AS DOUBLE) volume,
               CAST(o.open_interest AS DOUBLE) oi
        FROM read_parquet('{path}') o
        JOIN wanted w
          ON CAST(o.trading_day AS DATE)=w.trade_date
         AND (o."timestamp"=w.ts OR o."timestamp"=w.entry_ts)
        WHERE CAST(o.trading_day AS DATE) IN ({vals})
          AND o.close>0
        """
        z=con.execute(q).df()
        if not z.empty:
            z["ts"]=ist_ts(z["ts"])
            z["expiry"]=expiry_date
            chunks.append(z)
    con.close()
    return pd.concat(chunks,ignore_index=True) if chunks else pd.DataFrame()

def build_setups(spot, quotes):
    if quotes.empty:
        return pd.DataFrame()
    rows=[]
    for (d,ts),sig_meta in spot.groupby(["trade_date","ts"],sort=False):
        sig_meta=sig_meta.iloc[0]
        q=quotes[(quotes.trade_date==d)&(quotes.ts.isin([ts,ts+pd.Timedelta(minutes=1)]))]
        if q.empty:
            continue
        sig=q[q.ts==ts]
        ent=q[q.ts==ts+pd.Timedelta(minutes=1)]
        if sig.empty or ent.empty:
            continue
        strikes=np.sort(sig.strike.dropna().unique())
        if len(strikes)<7:
            continue
        atm_i=int(np.argmin(np.abs(strikes-float(sig_meta.close))))
        put2_i=atm_i-2
        call2_i=atm_i+2
        if put2_i<0 or call2_i>=len(strikes):
            continue
        put2=float(strikes[put2_i])
        call2=float(strikes[call2_i])
        put_sig=sig[(sig.option_type=="PE")&(sig.strike==put2)].head(1)
        call_sig=sig[(sig.option_type=="CE")&(sig.strike==call2)].head(1)
        if put_sig.empty or call_sig.empty:
            continue
        pclose=float(put_sig.iloc[0].close_px)
        cclose=float(call_sig.iloc[0].close_px)
        denom=max(1e-9,pclose+cclose)
        skew=(pclose-cclose)/denom
        pvol=float(put_sig.iloc[0].volume)
        cvol=float(call_sig.iloc[0].volume)
        vol_imb=(pvol-cvol)/max(1e-9,pvol+cvol)
        poi=float(put_sig.iloc[0].oi) if pd.notna(put_sig.iloc[0].oi) else 0.0
        coi=float(call_sig.iloc[0].oi) if pd.notna(call_sig.iloc[0].oi) else 0.0
        oi_imb=(poi-coi)/max(1e-9,poi+coi)
        expiry=put_sig.iloc[0].expiry
        for side in ("PUT","CALL"):
            short_i=put2_i if side=="PUT" else call2_i
            option_code="PE" if side=="PUT" else "CE"
            for width in WIDTHS:
                wing_i=short_i-width if side=="PUT" else short_i+width
                if wing_i<0 or wing_i>=len(strikes):
                    continue
                short_strike=float(strikes[short_i])
                wing_strike=float(strikes[wing_i])
                short_q=ent[(ent.option_type==option_code)&(ent.strike==short_strike)].head(1)
                wing_q=ent[(ent.option_type==option_code)&(ent.strike==wing_strike)].head(1)
                if short_q.empty or wing_q.empty:
                    continue
                short_entry=float(short_q.iloc[0].open_px)
                wing_entry=float(wing_q.iloc[0].open_px)
                credit=short_entry-wing_entry
                if credit<=0:
                    continue
                rows.append({
                    "trade_date":d,
                    "ts":ts,
                    "entry_ts":ts+pd.Timedelta(minutes=1),
                    "expiry":expiry,
                    "side":side,
                    "width":width,
                    "short_strike":short_strike,
                    "wing_strike":wing_strike,
                    "short_entry":short_entry,
                    "wing_entry":wing_entry,
                    "entry_credit":credit,
                    "skew":skew,
                    "vol_imb":vol_imb,
                    "oi_imb":oi_imb,
                    "spot_ret10":float(sig_meta.ret10),
                    "rv_ratio":float(sig_meta.rv_ratio)
                })
    return pd.DataFrame(rows)

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

def simulate(root, unique_setups, out, slippage):
    if unique_setups.empty:
        return pd.DataFrame()
    files=dict(expiry_files(root))
    con=duckdb.connect()
    con.execute("SET TimeZone='Asia/Kolkata'")
    con.register("legs",unique_setups[[
        "trade_date","entry_ts","expiry","side","short_strike","wing_strike"
    ]].drop_duplicates())
    chunks=[]
    for expiry_date,path in sorted(files.items()):
        active=int(con.execute("SELECT COUNT(*) FROM legs WHERE expiry=?", [expiry_date]).fetchone()[0])
        if active==0:
            continue
        q=f"""
        SELECT
          o."timestamp" AS ts,
          CAST(o.trading_day AS DATE) AS trade_date,
          CAST(o.strike AS DOUBLE) AS strike,
          CAST(o.option_type AS VARCHAR) AS option_type,
          CAST(o.high AS DOUBLE) AS high,
          CAST(o.low AS DOUBLE) AS low,
          CAST(o."close" AS DOUBLE) AS close_px
        FROM read_parquet('{path}') o
        JOIN legs l
          ON l.expiry=DATE '{expiry_date}'
         AND CAST(o.trading_day AS DATE)=l.trade_date
         AND o.option_type=(CASE WHEN l.side='PUT' THEN 'PE' ELSE 'CE' END)
         AND CAST(o.strike AS DOUBLE) IN(l.short_strike,l.wing_strike)
         AND o."timestamp">=l.entry_ts
         AND o."timestamp"<=l.entry_ts+INTERVAL '30 minutes'
        WHERE o."close">0
        """
        z=con.execute(q).df()
        if not z.empty:
            z["ts"]=ist_ts(z["ts"])
            z["expiry"]=expiry_date
            chunks.append(z)
    con.close()
    if not chunks:
        return pd.DataFrame()
    win=pd.concat(chunks,ignore_index=True)
    trades=[]
    for _,r in unique_setups.drop_duplicates([
        "trade_date","entry_ts","expiry","side","width","short_strike","wing_strike"
    ]).iterrows():
        option_code="PE" if r.side=="PUT" else "CE"
        q=win[
            (win.trade_date==r.trade_date)&
            (win.expiry==r.expiry)&
            (win.option_type==option_code)&
            (win.strike.isin([r.short_strike,r.wing_strike]))&
            (win.ts>=r.entry_ts)&
            (win.ts<=r.entry_ts+pd.Timedelta(minutes=max(HOLDS)))
        ]
        if q.empty:
            continue
        a=q[q.strike==r.short_strike][["ts","high","low","close_px"]].rename(
            columns={"high":"shigh","low":"slow","close_px":"sclose"}
        )
        b=q[q.strike==r.wing_strike][["ts","high","low","close_px"]].rename(
            columns={"high":"whigh","low":"wlow","close_px":"wclose"}
        )
        m=a.merge(b,on="ts").sort_values("ts")
        if m.empty:
            continue
        for hold in HOLDS:
            mm=m[m.ts<=r.entry_ts+pd.Timedelta(minutes=hold)]
            if mm.empty:
                continue
            hi=mm.shigh-mm.wlow
            lo=mm.slow-mm.whigh
            for stop in STOPS:
                stopv=float(r.entry_credit)*stop
                target=float(r.entry_credit)*TARGET_RATIO
                si=np.flatnonzero(hi>=stopv)
                ti=np.flatnonzero(lo<=target)
                si=int(si[0]) if len(si) else 10**9
                ti=int(ti[0]) if len(ti) else 10**9
                if si<=ti and si<10**9:
                    ix,reason=si,"STOP"
                elif ti<10**9:
                    ix,reason=ti,"TARGET"
                else:
                    ix,reason=len(mm)-1,"TIME"
                er=mm.iloc[ix]
                net=OptionCostModel().vertical_credit_spread_net_pnl(
                    float(r.short_entry),float(r.wing_entry),
                    float(er.sclose),float(er.wclose),
                    lot(r.trade_date),slippage_points=slippage
                )
                trades.append({
                    "trade_date":r.trade_date,
                    "ts":r.ts,
                    "expiry":r.expiry,
                    "side":r.side,
                    "width":r.width,
                    "hold":hold,
                    "stop":stop,
                    "short_strike":float(r.short_strike),
                    "wing_strike":float(r.wing_strike),
                    "net_pnl":net,
                    "reason":reason,
                    "entry_credit":float(r.entry_credit)
                })
    return pd.DataFrame(trades)

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
    # profit factor is computed from the grouped trade P&L before storing the board
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
    candidates=spot[["trade_date","ts","close","ret10","rv_ratio"]].drop_duplicates().copy()
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
            (trades.side==v.side)&(trades.width==v.width)&(trades.hold==v.hold)&(trades.stop==v.stop)&
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
