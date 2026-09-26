from __future__ import annotations
import itertools,json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path("data/cache/phase30_5_nifty_spot")
OUT=Path("reports/phase30_6_bear_put_signal_coverage.json")
STUDY_START=pd.Timestamp("2025-09-01",tz="Asia/Kolkata")
STUDY_END=pd.Timestamp("2026-08-31 23:59:59",tz="Asia/Kolkata")
LOOKBACKS=[30,60,120]
TOUCH=[0.001,0.002,0.004]
CRACK=[0.001,0.002,0.004]
GAP=[0.002,0.005,0.010]

def load():
    xs=[]
    for p in sorted(ROOT.glob("*.csv")):
        x=pd.read_csv(p)
        ts=pd.to_datetime(x["Timestamp"],errors="coerce")
        ts=ts.dt.tz_localize("Asia/Kolkata") if ts.dt.tz is None else ts.dt.tz_convert("Asia/Kolkata")
        x["Timestamp"]=ts
        for c in ["Open","High","Low","Close"]:
            x[c]=pd.to_numeric(x[c],errors="coerce")
        xs.append(x[["Timestamp","Open","High","Low","Close"]])
    z=pd.concat(xs,ignore_index=True).dropna().sort_values("Timestamp")
    z=z[(z["Timestamp"]>=STUDY_START)&(z["Timestamp"]<=STUDY_END)]
    return z.drop_duplicates("Timestamp").reset_index(drop=True)

def scan_day(day, grp, lookback, touch, kind, threshold):
    high=grp.High.to_numpy(float)
    op=grp.Open.to_numpy(float)
    cl=grp.Close.to_numpy(float)
    n=len(grp)
    if n<=lookback:
        return None
    # Each trigger bar i=lookback..n-1 uses only the preceding
    # lookback bars i-lookback..i-1. sliding_window_view creates one
    # extra window ending at the final bar, so drop that extra window.
    windows=np.lib.stride_tricks.sliding_window_view(high,lookback)[:-1]
    resistance=windows.max(axis=1)
    touch_count=(windows >= resistance[:,None]*(1-touch)).sum(axis=1)
    candidate=np.flatnonzero(touch_count>=2)
    if candidate.size==0:
        return None
    # candidate k corresponds to the trigger bar at index k+lookback.
    if kind=="crack":
        cond=cl[lookback:] <= resistance*(1-threshold)
    else:
        cond=op[lookback:] <= resistance*(1-threshold)
    hits=candidate[cond[candidate]]
    if hits.size==0:
        return None
    i=int(hits[0]+lookback)
    return {
        "date":str(day),
        "signal_ts":grp.Timestamp.iloc[i].isoformat(),
        "resistance":float(resistance[int(hits[0])]),
        "open":float(op[i]),
        "close":float(cl[i]),
    }

def main():
    df=load()
    by_day={day:g.sort_values("Timestamp").reset_index(drop=True)
            for day,g in df.assign(date=df.Timestamp.dt.date).groupby("date",sort=True)}
    out=[]
    for lb,tol in itertools.product(LOOKBACKS,TOUCH):
        for kind,vals in (("crack",CRACK),("gapdown",GAP)):
            for th in vals:
                sig=[]
                for day,g in by_day.items():
                    hit=scan_day(day,g,lb,tol,kind,th)
                    if hit:sig.append(hit)
                iso_weeks=sorted({pd.Timestamp(s["date"]).isocalendar()[:2] for s in sig})
                clocks=[pd.Timestamp(s["signal_ts"]).strftime("%H:%M") for s in sig]
                out.append({
                    "definition":f"lb{lb}|tol{tol:.3f}|{kind}|thr{th:.3f}",
                    "lookback_min":lb,"touch_tolerance":tol,"trigger":kind,"threshold":th,
                    "signal_days":len(sig),"signal_weeks":len(iso_weeks),
                    "median_clock":None if not clocks else sorted(clocks)[len(clocks)//2],
                    "signals":sig,
                })
    result={"cells":len(out),"definitions":out,"pnl_authorized":False,"implementation":"vectorized","study_window":["2025-09-01","2026-08-31"]}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"cells":len(out),"signal_days_min":min(x["signal_days"] for x in out),
                      "signal_days_max":max(x["signal_days"] for x in out)},indent=2))

if __name__=="__main__":main()
