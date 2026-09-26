from __future__ import annotations
import json, re
from pathlib import Path
import duckdb, pandas as pd

ROOT=Path("data/cache/phase30_2_rissin")
OUT=Path("reports/phase30_2_signal_diagnostic.json")
EXPIRIES=[("2025-09-09","2025-09-03"),("2025-09-16","2025-09-10")]
ENTRY_TIMES=["09:30:00","10:00:00","11:00:00","13:00:00","14:00:00"]
TARGETS=[20.0,25.0,30.0]

def normalize(raw):
    raw=pd.Series(raw,copy=False).astype(str).str.strip()
    aware=raw.str.contains(r"(?:[+-]\d{2}:?\d{2}|Z)$",regex=True,na=False)
    ts=pd.Series(pd.NaT,index=raw.index,dtype="datetime64[ns]")
    if aware.any():
        p=pd.to_datetime(raw[aware],errors="coerce",utc=True)
        ts.loc[aware]=p.dt.tz_convert("Asia/Kolkata").dt.tz_localize(None)
    naive=~aware
    if naive.any():
        p=pd.to_datetime(raw[naive],errors="coerce")
        ts.loc[naive]=p.dt.tz_localize("Asia/Kolkata").dt.tz_localize(None)
    return ts.dt.floor("min")

def inspect(con, expiry, entry_date):
    path=str(ROOT/"NIFTY_*.parquet")
    q=f"""
    SELECT CAST(timestamp AS VARCHAR) AS ts_raw,
           CAST(expiry AS DATE) AS expiry,
           CAST(strike AS DOUBLE) AS strike,
           upper(option_type) AS option_type,
           CAST(open AS DOUBLE) AS open_px,
           CAST(close AS DOUBLE) AS close_px
    FROM read_parquet('{path}')
    WHERE upper(underlying)='NIFTY'
      AND granularity='1min'
      AND CAST(expiry AS DATE)=DATE '{expiry}'
      AND CAST(date AS DATE) BETWEEN DATE '{entry_date}' AND DATE '{entry_date}'
      AND CAST(timestamp AS TIMESTAMP) BETWEEN TIMESTAMP '{entry_date} 09:00:00'
          AND TIMESTAMP '{entry_date} 15:15:00'
      AND open > 0 AND close > 0
    ORDER BY option_type,strike,ts_raw
    """
    df=con.execute(q).df()
    if df.empty:
        return {"expiry":expiry,"entry_date":entry_date,"rows":0}
    df["ts"]=normalize(df["ts_raw"])
    signal_rows=df[df.ts.isin([pd.Timestamp(f"{entry_date} {t}") for t in ENTRY_TIMES])]
    fill_rows=df[df.ts.isin([pd.Timestamp(f"{entry_date} {t}")+pd.Timedelta(minutes=1) for t in ENTRY_TIMES])]
    sample_raw=sorted(df.ts_raw.dropna().unique().tolist())[:12]
    result={"expiry":expiry,"entry_date":entry_date,"rows":int(len(df)),
            "raw_timestamp_sample":sample_raw,
            "normalized_min":str(df.ts.min()),
            "normalized_max":str(df.ts.max()),
            "rows_at_signal_times":int(len(signal_rows)),
            "rows_at_fill_times":int(len(fill_rows)),
            "signal_counts":{},"fill_counts":{},"target_examples":{}}
    for t in ENTRY_TIMES:
        ts=pd.Timestamp(f"{entry_date} {t}")
        s=signal_rows[signal_rows.ts==ts]
        f=fill_rows[fill_rows.ts==ts+pd.Timedelta(minutes=1)]
        result["signal_counts"][t]={"rows":int(len(s)),"CE":int((s.option_type=="CE").sum()),"PE":int((s.option_type=="PE").sum())}
        result["fill_counts"][t]={"rows":int(len(f)),"CE":int((f.option_type=="CE").sum()),"PE":int((f.option_type=="PE").sum())}
        ex={}
        for side in ["CE","PE"]:
            ss=s[s.option_type==side]
            vals={}
            for target in TARGETS:
                if ss.empty:
                    vals[str(target)]=None
                else:
                    row=ss.iloc[(ss.close_px-target).abs().argmin()]
                    vals[str(target)]={"strike":float(row.strike),"close_px":float(row.close_px),
                                       "has_fill_same_strike":not f[(f.option_type==side)&(f.strike==row.strike)].empty}
            ex[side]=vals
        result["target_examples"][t]=ex
    return result

def main():
    con=duckdb.connect()
    con.execute("SET TimeZone='Asia/Kolkata'")
    report={"source":str(ROOT),"checks":[inspect(con,e,d) for e,d in EXPIRIES]}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(report,indent=2,default=str)+"\n")
    print(json.dumps(report,indent=2,default=str))

if __name__=="__main__":
    main()
