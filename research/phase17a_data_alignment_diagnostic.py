from __future__ import annotations
import json
from pathlib import Path
import duckdb
import pandas as pd

START_DATE="2021-05-27"
END_DATE="2026-08-04"
ENTRY_TIMES=("14:30:00","14:45:00","15:00:00")

def expiry_files(root):
    ps=[]
    for p in sorted((root/"options"/"NIFTY").glob("*.parquet")):
        try: ps.append((pd.Timestamp(p.stem).date(),p))
        except: pass
    return ps

def nearest(files,d):
    fut=[x for x in files if x[0]>=d]
    return min(fut,key=lambda x:x[0]) if fut else None

def spot_candidates(root):
    con=duckdb.connect()
    con.execute("SET TimeZone='Asia/Kolkata'")
    p=root/"index"/"NIFTY.parquet"
    q=f"""
    WITH b AS (
      SELECT CAST(timestamp AS TIMESTAMP) ts,
             CAST(trading_day AS DATE) trade_date,
             CAST(close AS DOUBLE) close_px
      FROM read_parquet('{p}')
      WHERE CAST(trading_day AS DATE) BETWEEN DATE '{START_DATE}' AND DATE '{END_DATE}'
        AND close>0
    ),
    r AS (
      SELECT *,
             close/LAG(close,10) OVER(PARTITION BY trade_date ORDER BY ts)-1 ret10
      FROM b
    )
    SELECT *
    FROM r
    WHERE ret10 IS NOT NULL
      AND ABS(ret10)<=0.005
      AND CAST(ts AS TIME) IN (TIME '14:30:00',TIME '14:45:00',TIME '15:00:00')
    ORDER BY trade_date,ts
    LIMIT 20
    """
    x=con.execute(q).df(); con.close()
    return x

def inspect_file(path):
    con=duckdb.connect()
    con.execute("SET TimeZone='Asia/Kolkata'")
    q=f"""
    SELECT *
    FROM read_parquet('{path}')
    LIMIT 20
    """
    sample=con.execute(q).df()
    schema=con.execute(f"DESCRIBE SELECT * FROM read_parquet('{path}')").df()
    types=con.execute(f"SELECT DISTINCT CAST(option_type AS VARCHAR) option_type FROM read_parquet('{path}') ORDER BY 1").df()
    times=con.execute(f"""
      SELECT MIN(CAST(timestamp AS TIMESTAMP)) min_ts,
             MAX(CAST(timestamp AS TIMESTAMP)) max_ts,
             COUNT(*) rows
      FROM read_parquet('{path}')
    """).df()
    con.close()
    return sample,schema,types,times

def probe_candidate(path, trade_date, signal_ts, spot):
    entry_ts=signal_ts+pd.Timedelta(minutes=1)
    con=duckdb.connect(); con.execute("SET TimeZone='Asia/Kolkata'")
    q=f"""
    SELECT
      CAST(timestamp AS TIMESTAMP) ts,
      CAST(trading_day AS DATE) trade_date,
      CAST(strike AS DOUBLE) strike,
      CAST(option_type AS VARCHAR) option_type,
      CAST(open AS DOUBLE) open,
      CAST(close AS DOUBLE) close,
      CAST(volume AS DOUBLE) volume,
      CAST(open_interest AS DOUBLE) oi
    FROM read_parquet('{path}')
    WHERE CAST(trading_day AS DATE)=DATE '{trade_date}'
      AND CAST(timestamp AS TIMESTAMP) IN (TIMESTAMP '{signal_ts}',TIMESTAMP '{entry_ts}')
      AND close>0
    ORDER BY ts,strike
    """
    rows=con.execute(q).df()
    summary={}
    summary["signal_ts"]=str(signal_ts)
    summary["entry_ts"]=str(entry_ts)
    summary["spot"]=float(spot)
    summary["rows_at_signal"]=int((rows.ts==pd.Timestamp(signal_ts)).sum()) if not rows.empty else 0
    summary["rows_at_entry"]=int((rows.ts==pd.Timestamp(entry_ts)).sum()) if not rows.empty else 0
    summary["option_types"]=sorted(rows.option_type.dropna().unique().tolist()) if not rows.empty else []
    summary["strike_count_signal"]=int(rows.loc[rows.ts==pd.Timestamp(signal_ts),"strike"].nunique()) if not rows.empty else 0
    summary["strike_min_signal"]=float(rows.loc[rows.ts==pd.Timestamp(signal_ts),"strike"].min()) if summary["strike_count_signal"] else None
    summary["strike_max_signal"]=float(rows.loc[rows.ts==pd.Timestamp(signal_ts),"strike"].max()) if summary["strike_count_signal"] else None
    summary["sample_rows"]=rows.head(30).to_dict("records")
    con.close()
    return summary

def main(root:Path,out:Path):
    out.mkdir(parents=True,exist_ok=True)
    files=expiry_files(root)
    spots=spot_candidates(root)
    results={"file_count":len(files),"first_expiry":str(files[0][0]) if files else None,
             "last_expiry":str(files[-1][0]) if files else None,
             "spot_candidate_rows":int(len(spots))}
    if not files:
        raise RuntimeError("No exact-expiry files found")
    sample,schema,types,times=inspect_file(str(files[0][1]))
    results["first_file"]=str(files[0][1])
    results["schema"]=schema.to_dict("records")
    results["distinct_option_type"]=types.option_type.tolist()
    results["time_range"]=times.to_dict("records")
    results["sample_columns"]=sample.columns.tolist()
    if not spots.empty:
        row=spots.iloc[0]
        td=pd.Timestamp(row.trade_date).date()
        ef=nearest(files,td)
        results["candidate_trade_date"]=str(td)
        results["candidate_signal_ts"]=str(row.ts)
        results["selected_expiry_file"]=str(ef[1]) if ef else None
        if ef:
            results["probe"]=probe_candidate(str(ef[1]),td,pd.Timestamp(row.ts),float(row.close))
    (out/"phase17a_diagnostic.json").write_text(json.dumps(results,indent=2,default=str))
    (out/"phase17a_diagnostic.txt").write_text(json.dumps(results,indent=2,default=str))
    print(json.dumps(results,indent=2,default=str))

if __name__=="__main__":
    import sys
    main(Path(sys.argv[1]),Path(sys.argv[2]))
