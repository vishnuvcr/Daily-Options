from __future__ import annotations
import json
from pathlib import Path
import duckdb, pandas as pd

ROOT=Path("data/cache/phase30_2_rissin")
OUT=Path("reports/phase30_2_falcon_gate_diagnostic.json")
CHECKS=[("2025-09-09","2025-09-16","2025-09-03"),("2025-09-16","2025-09-23","2025-09-10")]
TIMES=["09:30:00","10:00:00","11:00:00","13:00:00","14:00:00"]
TARGETS=[20.0,25.0,30.0]

def norm(raw):
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

def load(con, expiry, start, end):
    q=f"""
    SELECT CAST(timestamp AS VARCHAR) ts_raw, CAST(expiry AS DATE) expiry,
           CAST(strike AS DOUBLE) strike, upper(option_type) option_type,
           CAST(open AS DOUBLE) open_px, CAST(close AS DOUBLE) close_px
    FROM read_parquet('{ROOT}/NIFTY_*.parquet')
    WHERE upper(underlying)='NIFTY' AND granularity='1min'
      AND CAST(expiry AS DATE)=DATE '{expiry}'
      AND CAST(date AS DATE) BETWEEN DATE '{start}' AND DATE '{end}'
      AND CAST(timestamp AS TIMESTAMP) BETWEEN TIMESTAMP '{start} 09:00:00'
      AND TIMESTAMP '{end} 15:15:00'
      AND open>0 AND close>0
    """
    x=con.execute(q).df()
    if x.empty:return x
    x["ts"]=norm(x.ts_raw)
    return x.drop(columns=["ts_raw"]).dropna(subset=["ts"]).drop_duplicates(["ts","strike","option_type"])

def pick(x,side,target,ref=None,outward=False):
    y=x[x.option_type==side].copy()
    if ref is not None:
        if outward:
            y=y[y.strike>=float(ref)] if side=="CE" else y[y.strike<=float(ref)]
        else:y=y[y.strike==float(ref)]
    if y.empty:return None
    return y.iloc[(y.close_px-target).abs().argmin()]

def inspect(con,ne,fe,d):
    n=load(con,ne,d,d); f=load(con,fe,d,d)
    out={"entry_date":d,"near_expiry":ne,"far_expiry":fe,"near_rows":len(n),"far_rows":len(f),"times":{}}
    for t in TIMES:
        sig=pd.Timestamp(f"{d} {t}"); fill=sig+pd.Timedelta(minutes=1)
        ns=n[n.ts==sig]; nf=n[n.ts==fill]; fs=f[f.ts==sig]; ff=f[f.ts==fill]
        rec={"near_signal":len(ns),"far_signal":len(fs),"near_fill":len(nf),"far_fill":len(ff),"targets":{}}
        for p in TARGETS:
            ce,pe=pick(ns,"CE",p),pick(ns,"PE",p)
            p_rec={"near":None,"far_same":None,"far_diag":None}
            if ce is not None and pe is not None:
                p_rec["near"]={"ce_strike":float(ce.strike),"pe_strike":float(pe.strike),"ce_px":float(ce.close_px),"pe_px":float(pe.close_px)}
                for mode,outward in [("far_same",False),("far_diag",True)]:
                    fce,fpe=pick(fs,"CE",p,ce.strike,outward),pick(fs,"PE",p,pe.strike,outward)
                    if fce is None or fpe is None:
                        p_rec[mode]={"selectable":False}
                        continue
                    nce=nf[(nf.option_type=="CE")&(nf.strike==ce.strike)]
                    npe=nf[(nf.option_type=="PE")&(nf.strike==pe.strike)]
                    fce2=ff[(ff.option_type=="CE")&(ff.strike==fce.strike)]
                    fpe2=ff[(ff.option_type=="PE")&(ff.strike==fpe.strike)]
                    ok=not any(z.empty for z in [nce,npe,fce2,fpe2])
                    if not ok:
                        p_rec[mode]={"selectable":True,"fill_complete":False,"far_strikes":[float(fce.strike),float(fpe.strike)]}
                    else:
                        sc,sp,fc,fp=[float(z.iloc[0].open_px) for z in [nce,npe,fce2,fpe2]]
                        credit=5*(sc+sp)-3*(fc+fp)
                        p_rec[mode]={"selectable":True,"fill_complete":True,"far_strikes":[float(fce.strike),float(fpe.strike)],"entry_prices":[sc,sp,fc,fp],"credit":credit,"positive_credit":credit>0}
            rec["targets"][str(p)]=p_rec
        out["times"][t]=rec
    return out

def main():
    con=duckdb.connect(); con.execute("SET TimeZone='Asia/Kolkata'")
    report={"source_revision":"8f7739cab3f38abdcbc6332a6d0a83e1341326e3","checks":[inspect(con,*x) for x in CHECKS]}
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
if __name__=="__main__": main()
