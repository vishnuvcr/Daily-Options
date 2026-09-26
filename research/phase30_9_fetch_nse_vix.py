#!/usr/bin/env python3
# Phase 30.9 workflow trigger: NSE VIX cache acquisition.
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

import pandas as pd
import requests

NSE_HOME = "https://www.nseindia.com/"
NSE_VIX_URL = "https://www.nseindia.com/api/historicalOR/vixhistory"


def fetch_vix(start: str, end: str) -> list[dict]:
    s = requests.Session()
    s.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "application/json,text/plain,*/*",
            "Referer": NSE_HOME,
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
        }
    )
    # NSE may return 403 on the public landing page from CI IPs.
    # The historical endpoint itself is the required data request.
    params = {
        "from": pd.Timestamp(start).strftime("%d-%m-%Y"),
        "to": pd.Timestamp(end).strftime("%d-%m-%Y"),
    }
    r = s.get(NSE_VIX_URL, params=params, timeout=60)
    if r.status_code == 403:
        # One deterministic retry with the browser-like headers most NSE clients use.
        retry_headers = {
            "User-Agent": s.headers["User-Agent"],
            "Referer": "https://www.nseindia.com/reports-indices-historical-vix",
            "Origin": "https://www.nseindia.com",
            "Accept": "application/json, text/plain, */*",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }
        r = s.get(NSE_VIX_URL, params=params, headers=retry_headers, timeout=60)
    r.raise_for_status()
    payload = r.json()
    if isinstance(payload, dict):
        rows = payload.get("data") or payload.get("records") or payload
    else:
        rows = payload
    if not isinstance(rows, list):
        raise RuntimeError(f"Unexpected NSE VIX response type: {type(rows)!r}")
    return rows


def normalize(rows: list[dict]) -> pd.DataFrame:
    if not rows:
        raise RuntimeError("NSE returned no VIX rows")

    df = pd.DataFrame(rows)
    aliases = {
        "EOD_TIMESTAMP": "date",
        "date": "date",
        "EOD_OPEN_INDEX_VAL": "open",
        "open": "open",
        "EOD_HIGH_INDEX_VAL": "high",
        "high": "high",
        "EOD_LOW_INDEX_VAL": "low",
        "low": "low",
        "EOD_CLOSE_INDEX_VAL": "close",
        "close": "close",
        "EOD_PREV_CLOSE": "prev_close",
        "prev_close": "prev_close",
        "VIX_PTS_CHG": "change",
        "change": "change",
        "VIX_PERC_CHG": "pct_change",
        "pct_change": "pct_change",
    }
    rename = {k: v for k, v in aliases.items() if k in df.columns}
    df = df.rename(columns=rename)

    required = ["date", "open", "high", "low", "close"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise RuntimeError(f"Missing required NSE VIX columns: {missing}; got {list(df.columns)}")

    df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce").dt.date
    for c in ["open", "high", "low", "close", "prev_close", "change", "pct_change"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.dropna(subset=["date", "open", "high", "low", "close"])
    df = df.drop_duplicates(subset=["date"], keep="last").sort_values("date")
    return df.reset_index(drop=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--metadata", required=True)
    args = ap.parse_args()

    start = date.fromisoformat(args.start)
    end = date.fromisoformat(args.end)
    if start > end:
        raise SystemExit("start must be <= end")

    rows = fetch_vix(args.start, args.end)
    df = normalize(rows)
    study = df[(df["date"] >= start) & (df["date"] <= end)].copy()
    if study.empty:
        raise RuntimeError("No VIX rows remain in requested study window")
    if study["date"].nunique() != len(study):
        raise RuntimeError("Duplicate VIX dates remain after normalization")
    coverage = {
        "requested_start": args.start,
        "requested_end": args.end,
        "rows": int(len(study)),
        "date_min": str(study["date"].min()),
        "date_max": str(study["date"].max()),
        "unique_dates": int(study["date"].nunique()),
        "source": NSE_VIX_URL,
    }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    study.to_csv(out, index=False, date_format="%Y-%m-%d")

    meta = Path(args.metadata)
    meta.parent.mkdir(parents=True, exist_ok=True)
    meta.write_text(json.dumps(coverage, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(coverage, indent=2))


if __name__ == "__main__":
    main()
