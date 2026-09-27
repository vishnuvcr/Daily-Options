#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from datetime import date, datetime, timedelta, timezone
import argparse, csv, hashlib, json, time
import pandas as pd
import threading

START=date(2021,7,1)
END=date(2026,8,31)
PARTICIPANTS=("FII","DII","PRO","CLIENT")
try:
    from curl_cffi import requests as http_requests
except Exception:
    import requests as http_requests

_thread_local=threading.local()

def get_session():
    if not hasattr(_thread_local,"session"):
        sess=http_requests.Session(impersonate="chrome124") if "curl_cffi" in getattr(http_requests,"__name__","") else http_requests.Session()
        sess.headers.update({
            "User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140 Safari/537.36",
            "Accept":"text/csv,text/plain,*/*",
            "Referer":"https://www.nseindia.com/all-reports-derivatives",
            "Accept-Language":"en-US,en;q=0.9",
        })
        try:
            sess.get("https://www.nseindia.com/all-reports-derivatives",timeout=20)
        except Exception:
            pass
        _thread_local.session=sess
    return _thread_local.session

URL_TEMPLATES=(
    "https://nsearchives.nseindia.com/content/nsccl/fao_participant_oi_{date}.csv",
    "https://archives.nseindia.com/content/nsccl/fao_participant_oi_{date}.csv",
)

def sha256_bytes(b:bytes)->str:
    return hashlib.sha256(b).hexdigest()

def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1<<20),b""):
            h.update(chunk)
    return h.hexdigest()

def load_nifty_days(root:Path)->list[date]:
    import duckdb
    con=duckdb.connect()
    q=f"""
      SELECT DISTINCT CAST(timestamp AS DATE) AS trade_date
      FROM read_parquet('{str(root/'index/NIFTY.parquet').replace("'","''")}')
      WHERE CAST(timestamp AS DATE) BETWEEN DATE '{START}' AND DATE '{END}'
      ORDER BY trade_date
    """
    x=con.execute(q).df()
    con.close()
    return [pd.Timestamp(v).date() for v in x["trade_date"].tolist()]

def parse_csv_bytes(raw:bytes)->pd.DataFrame:
    text=raw.decode("utf-8-sig","replace")
    rows=list(csv.reader(text.splitlines()))
    rows=[r for r in rows if any(str(c).strip() for c in r)]
    if len(rows)<3:
        raise ValueError("participant OI CSV has insufficient rows")
    # NSE participant file has a title row then the column header.
    header_idx=1
    header=[str(c).strip() for c in rows[header_idx]]
    data=rows[header_idx+1:]
    width=len(header)
    data=[r[:width]+[""]*max(0,width-len(r)) for r in data]
    df=pd.DataFrame(data,columns=header)
    df=df.loc[:,[c for c in df.columns if str(c).strip()]]
    df=df.dropna(how="all")
    return df

def norm_col(c:str)->str:
    return str(c).strip().upper().replace(" ","").replace("_","").replace("-","")

def find_col(cols, *patterns):
    nmap={norm_col(c):c for c in cols}
    for p in patterns:
        p0=norm_col(p)
        if p0 in nmap:
            return nmap[p0]
    for c in cols:
        nc=norm_col(c)
        if all(part in nc for part in patterns if part):
            return c
    return None

def normalize_participant(df:pd.DataFrame, trade_date:date)->pd.DataFrame:
    cols=list(df.columns)
    participant_col=None
    for c in cols:
        vals=set(str(x).strip().upper() for x in df[c].dropna().head(20))
        if {"FII","DII","PRO","CLIENT"} & vals:
            participant_col=c
            break
    if participant_col is None:
        raise ValueError("participant column not found")

    # Known NSE naming from public participant-OI parsers:
    # Client Type, Futures Index Long, Futures Index Short, ...
    long_col=find_col(cols,"FUTUREINDEXLONG") or find_col(cols,"FUTURESINDEXLONG") or find_col(cols,"FUTIDX","LONG")
    short_col=find_col(cols,"FUTUREINDEXSHORT") or find_col(cols,"FUTURESINDEXSHORT") or find_col(cols,"FUTIDX","SHORT")
    if long_col is None or short_col is None:
        raise ValueError(f"index-futures long/short columns not found: {cols}")

    out=df[[participant_col,long_col,short_col]].copy()
    out.columns=["participant","fut_idx_long","fut_idx_short"]
    out["participant"]=out["participant"].astype(str).str.strip().str.upper()
    out=out[out["participant"].isin(PARTICIPANTS)].copy()
    out["fut_idx_long"]=pd.to_numeric(out["fut_idx_long"].astype(str).str.replace(",","",regex=False),errors="coerce")
    out["fut_idx_short"]=pd.to_numeric(out["fut_idx_short"].astype(str).str.replace(",","",regex=False),errors="coerce")
    out["trade_date"]=pd.Timestamp(trade_date)
    out["idx_net"]=out["fut_idx_long"]-out["fut_idx_short"]
    den=out["fut_idx_long"]+out["fut_idx_short"]
    out["idx_net_ratio"]=out["idx_net"]/den.where(den!=0)
    return out.dropna(subset=["fut_idx_long","fut_idx_short"])

def fetch_one(session, d:date):
    stamp=d.strftime("%d%m%Y")
    last=None
    for base in URL_TEMPLATES:
        url=base.format(date=stamp)
        for attempt in range(3):
            try:
                r=session.get(url,timeout=45,allow_redirects=True)
                if r.status_code==404:
                    last=FileNotFoundError(url)
                    break
                r.raise_for_status()
                if len(r.content)<200:
                    raise RuntimeError("short response")
                return r.content,url
            except Exception as exc:
                last=exc
                time.sleep(1.5*(attempt+1))
    raise last or RuntimeError(f"no source for {d}")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--nifty-root",default="data/cache/phase31_trademarkk")
    ap.add_argument("--out",default="data/cache/phase31_10_institutional")
    args=ap.parse_args()

    nifty_root=Path(args.nifty_root); out=Path(args.out)
    out.mkdir(parents=True,exist_ok=True)


    days=load_nifty_days(nifty_root)
    rows=[]; manifest=[]; missing=[]
    for i,d in enumerate(days,1):
        try:
            raw,url=fetch_one(get_session(),d)
            norm=normalize_participant(parse_csv_bytes(raw),d)
            rows.append(norm)
            manifest.append({
                "date":str(d),"url":url,"raw_sha256":sha256_bytes(raw),
                "rows":int(len(norm)),"participants":sorted(norm.participant.unique().tolist())
            })
        except FileNotFoundError:
            missing.append(str(d))
        except Exception as exc:
            manifest.append({"date":str(d),"error":repr(exc)})
        if i%25==0:
            print(f"processed {i}/{len(days)}")
        time.sleep(0.02)

    panel=pd.concat(rows,ignore_index=True) if rows else pd.DataFrame(
        columns=["participant","fut_idx_long","fut_idx_short","trade_date","idx_net","idx_net_ratio"]
    )
    panel.to_parquet(out/"participant_oi_normalized.parquet",index=False)
    manifest_obj={
        "source":"NSE participant-wise F&O open-interest archive",
        "parser_version":"v2-future-index-header",
        "study_start":str(START),"study_end":str(END),
        "nifty_sessions":len(days),"files_ok":len(manifest)-sum(1 for x in manifest if "error" in x),
        "missing_files":missing,
        "manifest_rows":manifest,
        "normalized_sha256":sha256_file(out/"participant_oi_normalized.parquet"),
        "retrieved_utc":datetime.now(timezone.utc).isoformat(),
    }
    (out/"manifest.json").write_text(json.dumps(manifest_obj,indent=2,default=str),encoding="utf-8")
    summary=panel.groupby("participant")["trade_date"].nunique().to_dict() if not panel.empty else {}
    print(json.dumps({"manifest":manifest_obj,"participant_date_coverage":summary},indent=2,default=str))

if __name__=="__main__":
    main()
