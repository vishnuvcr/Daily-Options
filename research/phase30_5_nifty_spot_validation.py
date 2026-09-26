#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,os
from pathlib import Path
import pandas as pd

ROOT=Path("data/cache/phase30_5_nifty_spot")
OUT=Path("reports/phase30_5_nifty_spot_validation.json")
FILES=[]
for p in sorted(ROOT.rglob("*.csv")):
    if p.stat().st_size:
        FILES.append(p)

def read_one(p):
    x=pd.read_csv(p)
    cols={c.lower():c for c in x.columns}
    tscol=cols.get("timestamp")
    if tscol is None:
        raise RuntimeError(f"missing Timestamp column: {p}")
    ts=pd.to_datetime(x[tscol],errors="coerce")
    if ts.dt.tz is None:
        ts=ts.dt.tz_localize("Asia/Kolkata")
    else:
        ts=ts.dt.tz_convert("Asia/Kolkata")
    x["_ts"]=ts
    for c in ["Open","High","Low","Close"]:
        if c not in x.columns:
            raise RuntimeError(f"missing {c}: {p}")
        x[c]=pd.to_numeric(x[c],errors="coerce")
    bad=(x[["Open","High","Low","Close"]].isna().any(axis=1)|
         (x["High"] < x[["Open","Close","Low"]].max(axis=1))|
         (x["Low"] > x[["Open","Close","High"]].min(axis=1))|
         (x[["Open","High","Low","Close"]] <= 0).any(axis=1))
    return x,bad

def main():
    rows=[]; all_ts=[]
    for p in FILES:
        x,bad=read_one(p)
        rows.append({"file":str(p),"rows":int(len(x)),"bad_ohlc":int(bad.sum()),
                     "duplicate_timestamps":int(x._ts.duplicated().sum()),
                     "start_ist":str(x._ts.min()),"end_ist":str(x._ts.max()),
                     "sha256":hashlib.sha256(p.read_bytes()).hexdigest(),
                     "bytes":p.stat().st_size})
        all_ts.append(x[["_ts"]])
    if not rows:
        raise RuntimeError("NO_SPOT_FILES")
    ts=pd.concat(all_ts,ignore_index=True)._ts
    result={
      "source_repo":"https://github.com/technovusin/nifty50-historical-data",
      "source_commit":"75f273a2dec36b10f4ded3a00721fae2172edccb",
      "file_count":len(rows),"files":rows,
      "global_start_ist":str(ts.min()),"global_end_ist":str(ts.max()),
      "duplicate_global_timestamps":int(ts.duplicated().sum()),
      "resistance_rule_frozen":False,
      "backtest_authorized":False
    }
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))

if __name__=="__main__": main()
