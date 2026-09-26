#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import requests

NSE_HOME = "https://www.nseindia.com/"
NSE_VIX = "https://www.nseindia.com/api/historicalOR/vixhistory"

def daterange_chunks(start: date, end: date, days: int = 365):
    cur = start
    while cur <= end:
        nxt = min(end, cur + timedelta(days=days))
        yield cur, nxt
        cur = nxt + timedelta(days=1)

def session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140 Safari/537.36",
        "Accept": "application/json,text/plain,*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": NSE_HOME,
        "Connection": "keep-alive",
    })
    r = s.get(NSE_HOME, timeout=30)
    r.raise_for_status()
    return s

def extract_rows(payload):
    if isinstance(payload, dict):
        data = payload.get("data", payload.get("records", payload))
    else:
        data = payload
    if isinstance(data, dict):
        data = data.get("data", data.get("records", []))
    if not isinstance(data, list):
        raise ValueError(f"Unexpected NSE VIX payload type: {type(data)!r}")
    return data

def normalize(rows):
    if not rows:
        return pd.DataFrame(columns=["date","open","high","low","close"])
    raw = pd.DataFrame(rows)
    aliases = {
        "date": ["date","EOD_TIMESTAMP","TIMESTAMP","Date"],
        "open": ["open","EOD_OPEN_INDEX_VAL","OPEN","Open"],
        "high": ["high","EOD_HIGH_INDEX_VAL","HIGH","High"],
        "low": ["low","EOD_LOW_INDEX_VAL","LOW","Low"],
        "close": ["close","EOD_CLOSE_INDEX_VAL","CLOSE","Close"],
    }
    out = pd.DataFrame()
    for target, keys in aliases.items():
        hit = next((k for k in keys if k in raw.columns), None)
        if hit is None:
            raise ValueError(f"Missing NSE VIX field {target}; columns={list(raw.columns)}")
        out[target] = raw[hit]
    out["date"] = pd.to_datetime(out["date"], dayfirst=True, errors="coerce").dt.normalize()
    for c in ["open","high","low","close"]:
        out[c] = pd.to_numeric(out[c], errors="coerce")
    out = out.dropna(subset=["date","close"]).sort_values("date").drop_duplicates("date").reset_index(drop=True)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--metadata", required=True)
    args = ap.parse_args()
    start, end = date.fromisoformat(args.start), date.fromisoformat(args.end)
    if start > end:
        raise SystemExit("start > end")

    sess = session()
    rows = []
    raw_sha_parts = []
    for cstart, cend in daterange_chunks(start, end):
        params = {"from": cstart.strftime("%d-%m-%Y"), "to": cend.strftime("%d-%m-%Y")}
        last_exc = None
        for attempt in range(4):
            try:
                resp = sess.get(NSE_VIX, params=params, timeout=45)
                resp.raise_for_status()
                payload = resp.json()
                chunk = extract_rows(payload)
                rows.extend(chunk)
                raw_sha_parts.append(hashlib.sha256(resp.content).hexdigest())
                break
            except Exception as exc:
                last_exc = exc
                time.sleep(1.5 * (attempt + 1))
        else:
            raise RuntimeError(f"NSE VIX chunk failed {cstart}..{cend}: {last_exc}")

    df = normalize(rows)
    if df.empty:
        raise RuntimeError("NSE VIX response normalized to zero rows")
    df = df[(df.date.dt.date >= start) & (df.date.dt.date <= end)].copy()
    expected_days = max((end - start).days + 1, 1)
    if len(df) < 900:
        raise RuntimeError(f"Suspiciously low India VIX coverage: {len(df)} rows for {expected_days} calendar days")
    if not df.date.is_monotonic_increasing or not df.date.is_unique:
        raise RuntimeError("India VIX date integrity failed")
    if df.close.isna().any() or (df.close <= 0).any():
        raise RuntimeError("India VIX close contains non-positive/missing values")
    if df.date.min().date() > start + timedelta(days=10):
        raise RuntimeError(f"Unexpected start coverage: {df.date.min().date()}")
    if df.date.max().date() < end - timedelta(days=10):
        raise RuntimeError(f"Unexpected end coverage: {df.date.max().date()}")

    out = Path(args.output); meta = Path(args.metadata)
    out.parent.mkdir(parents=True, exist_ok=True); meta.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False, date_format="%Y-%m-%d")
    sha = hashlib.sha256(out.read_bytes()).hexdigest()
    manifest = {
        "source": "NSE India VIX historical API",
        "endpoint": NSE_VIX,
        "homepage": NSE_HOME,
        "start": str(start),
        "end": str(end),
        "rows": int(len(df)),
        "min_date": str(df.date.min().date()),
        "max_date": str(df.date.max().date()),
        "file_sha256": sha,
        "response_chunk_sha256": raw_sha_parts,
        "fetched_at_utc": datetime.utcnow().isoformat(timespec="seconds")+"Z",
    }
    meta.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))

if __name__ == "__main__":
    main()
