from __future__ import annotations
import itertools,json
from pathlib import Path
import pandas as pd

ROOT=Path("data/cache/phase30_5_nifty_spot")
OUT=Path("reports/phase30_6_bear_put_signal_coverage.json")

LOOKBACKS=[30,60,120]
TOUCH=[0.001,0.002,0.004]
CRACK=[0.001,0.002,0.004]
GAP=[0.002,0.005,0.010]

def load():
    xs=[]
    for p in sorted(ROOT.glob("*.csv")):
        x=pd.read_csv(p)
        x["Timestamp"]=pd.to_datetime(x["Timestamp"],errors="coerce")
        if x["Timestamp"].dt.tz is None:
            x["Timestamp"]=x["Timestamp"].dt.tz_localize("Asia/Kolkata")
        else:
            x["Timestamp"]=x["Timestamp"].dt.tz_convert("Asia/Kolkata")
        for c in ["Open","High","Low","Close"]:
            x[c]=pd.to_numeric(x[c],errors="coerce")
        xs.append(x[["Timestamp","Open","High","Low","Close"]])
    z=pd.concat(xs,ignore_index=True).dropna().sort_values("Timestamp")
    z=z.drop_duplicates("Timestamp")
    z["date"]=z.Timestamp.dt.date
    return z

def scan_day(day,df,lookback,touch,kind,threshold):
    x=df[df.date==day].copy().sort_values("Timestamp").reset_index(drop=True)
    if len(x)<lookback+1:return None
    for i in range(lookback,len(x)):
        hist=x.iloc[i-lookback:i]
        r=float(hist.High.max())
        near=(hist.High >= r*(1-touch)).sum()
        if near<2: continue
        row=x.iloc[i]
        if kind=="crack":
            cond=float(row.Close) <= r*(1-threshold)
        else:
            cond=float(row.Open) <= r*(1-threshold)
        if cond:
            return {"signal_ts":row.Timestamp.isoformat(),"resistance":r,"open":float(row.Open),"close":float(row.Close)}
    return None

def main():
    df=load()
    days=sorted(df.date.unique())
    out=[]
    for lb,tol in itertools.product(LOOKBACKS,TOUCH):
        for kind,vals in [("crack",CRACK),("gapdown",GAP)]:
            for th in vals:
                sig=[]
                for day in days:
                    r=scan_day(day,df,lb,tol,kind,th)
                    if r:sig.append({"date":str(day),**r})
                # Approximate calendar-week coverage on ISO week.
                weeks=sorted({pd.Timestamp(s["date"]).isocalendar().week for s in sig})
                clocks=[pd.to_datetime(s["signal_ts"]).strftime("%H:%M") for s in sig]
                out.append({
                    "definition":f"lb{lb}|tol{tol:.3f}|{kind}|thr{th:.3f}",
                    "lookback_min":lb,"touch_tolerance":tol,"trigger":kind,
                    "threshold":th,"signal_days":len(sig),
                    "signal_weeks":len(weeks),
                    "median_clock":None if not clocks else sorted(clocks)[len(clocks)//2],
                    "signals":sig,
                })
    result={"cells":len(out),"definitions":out,"pnl_authorized":False}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,indent=2,default=str)+"\n")
    print(json.dumps({"cells":len(out),"signal_days_max":max(x["signal_days"] for x in out),
                      "signal_days_min":min(x["signal_days"] for x in out)},indent=2))

if __name__=="__main__": main()
