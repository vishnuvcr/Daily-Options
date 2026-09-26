#!/usr/bin/env python3
from pathlib import Path
from datetime import date, timedelta, datetime, timezone
import argparse, hashlib, json
import pandas as pd
import yfinance as yf

START=date(2021,7,1)
END=date(2026,8,31)
TICKERS={
    "GSPC":"^GSPC",
    "IXIC":"^IXIC",
    "N225":"^N225",
    "HSI":"^HSI",
    "GDAXI":"^GDAXI",
    "KS11":"^KS11",
}

def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda:f.read(1<<20),b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",default="data/cache/phase31_8_global")
    args=ap.parse_args()
    out=Path(args.out); out.mkdir(parents=True,exist_ok=True)
    manifest={"source":"Yahoo Finance via yfinance","start":str(START),"end":str(END),"retrieved_utc":datetime.now(timezone.utc).isoformat(),"yfinance_version":yf.__version__,"tickers":{}}
    for key,ticker in TICKERS.items():
        path=out/f"{key}.parquet"
        if path.exists() and path.stat().st_size>0:
            df=pd.read_parquet(path)
        else:
            df=yf.Ticker(ticker).history(
                start=str(START),
                end=str(END+timedelta(days=1)),
                auto_adjust=False,
                actions=False,
            )
            if df.empty:
                raise RuntimeError(f"no data returned for {ticker}")
            df=df.reset_index()
            date_col="Date" if "Date" in df.columns else df.columns[0]
            df["date"]=pd.to_datetime(df[date_col]).dt.date
            df=df[(df.date>=START)&(df.date<=END)]
            df=df[["date","Open","High","Low","Close","Volume"]].rename(
                columns={"Open":"open","High":"high","Low":"low","Close":"close","Volume":"volume"}
            )
            df.to_parquet(path,index=False)
        df["date"]=pd.to_datetime(df["date"]).dt.date
        if df.empty:
            raise RuntimeError(f"empty persisted data for {ticker}")
        manifest["tickers"][key]={
            "symbol":ticker,
            "rows":int(len(df)),
            "first_date":str(df.date.min()),
            "last_date":str(df.date.max()),
            "sha256":sha256(path),
        }
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    print(json.dumps(manifest,indent=2))
if __name__=="__main__":
    main()
