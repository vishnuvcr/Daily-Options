from __future__ import annotations
import json
from pathlib import Path
import duckdb, numpy as np, pandas as pd

START_DATE="2021-05-27"; END_DATE="2026-08-04"

def expiry_files(root):
    out=[]
    for p in sorted((root/"options"/"NIFTY").glob("*.parquet")):
        try: out.append((pd.Timestamp(p.stem).date(),p))
        except: pass
    return out

def nearest(files,d):
    td=pd.Timestamp(d).date()
    fut=[x for x in files if x[0]>=td]
    return min(fut,key=lambda x:x[0]) if fut else None

def load_spot(root):
    con=duckdb.connect(); con.execute("SET TimeZone='Asia/Kolkata'")
    p=root/"index"/"NIFTY.parquet"
    q=f"""
    SELECT "timestamp" AS ts, CAST(trading_day AS DATE) trade_date,
           CAST("close" AS DOUBLE) spot_close
    FROM read_parquet('{p}')
    WHERE CAST(trading_day AS DATE) BETWEEN DATE '{START_DATE}' AND DATE '{END_DATE}'
      AND strftime("timestamp",'%H:%M:%S') IN ('14:30:00','14:45:00','15:00:00')
      AND "close">0
    ORDER BY trade_date,ts
    LIMIT 100
    """
    x=con.execute(q).df(); con.close()
    x["ts"]=pd.to_datetime(x["ts"],utc=True).dt.tz_convert("Asia/Kolkata").dt.tz_localize(None).dt.floor("min")
    return x

def inspect_day(path,trade_date,signal_ts,spot):
    con=duckdb.connect(); con.execute("SET TimeZone='Asia/Kolkata'")
    p=str(path)
    q=f"""
    SELECT "timestamp" AS ts, CAST(trading_day AS DATE) trade_date,
           CAST(strike AS DOUBLE) strike, CAST(option_type AS VARCHAR) option_type,
           CAST(open AS DOUBLE) open_px, CAST("close" AS DOUBLE) close_px,
           CAST(volume AS DOUBLE) volume, CAST(open_interest AS DOUBLE) oi
    FROM read_parquet('{p}')
    WHERE CAST(trading_day AS DATE)=DATE '{trade_date}'
      AND "timestamp">=TIMESTAMP '{signal_ts}'
      AND "timestamp"<=TIMESTAMP '{signal_ts}'+INTERVAL '5 minutes'
      AND "close">0
    """
    qdf=con.execute(q).df(); con.close()
    if qdf.empty: return {"rows":0}
    qdf["ts"]=pd.to_datetime(qdf["ts"],utc=True).dt.tz_convert("Asia/Kolkata").dt.tz_localize(None).dt.floor("min")
    sig=qdf[qdf.ts==signal_ts]
    if sig.empty: return {"rows":len(qdf),"signal_rows":0}
    strikes=np.sort(sig.strike.unique())
    atm_i=int(np.argmin(np.abs(strikes-float(spot))))
    out={
      "rows":int(len(qdf)),
      "signal_rows":int(len(sig)),
      "signal_strikes":int(sig.strike.nunique()),
      "option_types":sorted(sig.option_type.unique().tolist()),
      "atm_strike":float(strikes[atm_i]),
      "spot_distance":float(abs(strikes[atm_i]-float(spot))),
      "entry_checks":[]
    }
    for side in ("PUT","CALL"):
        si=atm_i-2 if side=="PUT" else atm_i+2
        if si<0 or si>=len(strikes): continue
        code="PE" if side=="PUT" else "CE"
        for width in (1,2):
            wi=si-width if side=="PUT" else si+width
            if wi<0 or wi>=len(strikes): continue
            ss=float(strikes[si]); ww=float(strikes[wi])
            s=qdf[(qdf.option_type==code)&(qdf.strike==ss)&(qdf.ts>signal_ts)]
            w=qdf[(qdf.option_type==code)&(qdf.strike==ww)&(qdf.ts>signal_ts)]
            both=sorted(set(s.ts).intersection(set(w.ts)))
            first=str(min(both)) if both else None
            delay=(min(both)-signal_ts).total_seconds()/60.0 if both else None
            out["entry_checks"].append({
              "side":side,"width":width,"short_strike":ss,"wing_strike":ww,
              "first_both_minute":first,"delay_min":delay,
              "short_points":int(len(s)),"wing_points":int(len(w))
            })
    return out

def main(root,out):
    out.mkdir(parents=True,exist_ok=True)
    spot=load_spot(root); files=expiry_files(root)
    rows=[]
    for _,r in spot.iterrows():
        ef=nearest(files,r.trade_date)
        if ef is None: continue
        d=inspect_day(ef[1],r.trade_date,r.ts,float(r.spot_close))
        d["trade_date"]=str(r.trade_date); d["signal_ts"]=str(r.ts); d["spot"]=float(r.close)
        rows.append(d)
    summary={"signals":len(rows),"rows":rows}
    delays=[]
    exact=0
    within3=0
    within5=0
    for r in rows:
        for e in r.get("entry_checks",[]):
            if e["delay_min"] is not None:
                delays.append(e["delay_min"])
                exact += int(e["delay_min"]==1)
                within3 += int(e["delay_min"]<=3)
                within5 += int(e["delay_min"]<=5)
    summary["entry_checks"]=len(delays)
    summary["exact_1m"]=exact
    summary["within_3m"]=within3
    summary["within_5m"]=within5
    summary["median_delay_min"]=float(np.median(delays)) if delays else None
    summary["max_delay_min"]=float(np.max(delays)) if delays else None
    (out/"phase17c_entry_availability.json").write_text(json.dumps(summary,indent=2,default=str))
    print(json.dumps(summary,indent=2,default=str))
if __name__=="__main__":
    import sys
    main(Path(sys.argv[1]),Path(sys.argv[2]))
