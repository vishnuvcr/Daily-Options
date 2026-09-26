#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

import pandas as pd
import requests

NSE_VIX_URL = "https://www.nseindia.com/api/historicalOR/vixhistory"
NIFTYINDICES_VIX_URL = "https://www.niftyindices.com/Backpage.aspx/BindHistoricalIndiaVixData"


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
        }
    )
    return s


def fetch_nse_vix(start: str, end: str) -> list[dict]:
    s = _session()
    params = {
        "from": pd.Timestamp(start).strftime("%d-%m-%Y"),
        "to": pd.Timestamp(end).strftime("%d-%m-%Y"),
    }
    r = s.get(
        NSE_VIX_URL,
        params=params,
        headers={
            "Referer": "https://www.nseindia.com/reports-indices-historical-vix",
            "Origin": "https://www.nseindia.com",
        },
        timeout=60,
    )
    if r.status_code == 403:
        r = s.get(
            NSE_VIX_URL,
            params=params,
            headers={
                "Referer": "https://www.nseindia.com/reports-indices-historical-vix",
                "Origin": "https://www.nseindia.com",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
            },
            timeout=60,
        )
    r.raise_for_status()
    payload = r.json()
    if isinstance(payload, dict):
        rows = payload.get("data") or payload.get("records") or payload
    else:
        rows = payload
    if not isinstance(rows, list):
        raise RuntimeError(f"Unexpected NSE VIX response type: {type(rows)!r}")
    return rows


def fetch_niftyindices_vix(start: str, end: str) -> list[dict]:
    s = _session()
    body = (
        "{'name':'India VIX',"
        f"'startDate':'{pd.Timestamp(start).strftime('%d %b %Y')}',"
        f"'endDate':'{pd.Timestamp(end).strftime('%d %b %Y')}}}"
    )
    r = s.post(
        NIFTYINDICES_VIX_URL,
        data=body,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Referer": "https://www.niftyindices.com/reports",
            "Origin": "https://www.niftyindices.com",
        },
        timeout=60,
    )
    r.raise_for_status()
    payload = r.json()
    if isinstance(payload, dict) and "d" in payload:
        payload = payload["d"]
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                if payload.strip().lower() == "false":
                    payload = []
                else:
                    raise
    if not isinstance(payload, list):
        raise RuntimeError(f"Unexpected Nifty Indices VIX response type: {type(payload)!r}")
    return payload


def normalize(rows: list[dict]) -> pd.DataFrame:
    if not rows:
        raise RuntimeError("VIX source returned no rows")

    df = pd.DataFrame(rows)
    aliases = {
        "EOD_TIMESTAMP": "date",
        "date": "date",
        "EOD_INDEX_NAME": "index_name",
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
    df = df.rename(columns={k: v for k, v in aliases.items() if k in df.columns})

    required = ["date", "open", "high", "low", "close"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise RuntimeError(f"Missing VIX columns: {missing}; got {list(df.columns)}")

    df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce").dt.date
    for c in ["open", "high", "low", "close", "prev_close", "change", "pct_change"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=required)
    df = df.drop_duplicates(subset=["date"], keep="last").sort_values("date")
    return df.reset_index(drop=True)


def compare_overlap(a: pd.DataFrame, b: pd.DataFrame) -> dict:
    if a.empty or b.empty:
        return {"overlap_dates": 0}
    x = a[["date", "open", "high", "low", "close"]].merge(
        b[["date", "open", "high", "low", "close"]],
        on="date", suffixes=("_a", "_b"),
    )
    if x.empty:
        return {"overlap_dates": 0}
    diffs = {
        c: float((x[f"{c}_a"] - x[f"{c}_b"]).abs().max())
        for c in ["open", "high", "low", "close"]
    }
    return {"overlap_dates": int(len(x)), "max_abs_diff": diffs}


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

    nse_rows = fetch_nse_vix(args.start, args.end)
    nse_df = normalize(nse_rows)
    nse_study = nse_df[(nse_df["date"] >= start) & (nse_df["date"] <= end)].copy()

    # NSE's historical endpoint currently returns a bounded window even when
    # a wider from/to range is supplied. Do not silently accept partial coverage.
    nse_complete = (
        not nse_study.empty
        and nse_study["date"].min() <= start
        and nse_study["date"].max() >= end
    )

    source = "nse_historical_vix"
    chosen = nse_study
    fallback_df = pd.DataFrame()
    if not nse_complete:
        fallback_rows = fetch_niftyindices_vix(args.start, args.end)
        fallback_df = normalize(fallback_rows)
        fallback_study = fallback_df[
            (fallback_df["date"] >= start) & (fallback_df["date"] <= end)
        ].copy()
        if fallback_study.empty:
            raise RuntimeError("NSE VIX was incomplete and Nifty Indices fallback returned no study-window rows")
        if fallback_study["date"].min() > start or fallback_study["date"].max() < end:
            raise RuntimeError(
                "Neither NSE nor Nifty Indices supplied complete study-window coverage"
            )
        chosen = fallback_study
        source = "niftyindices_india_vix_fallback_after_nse_partial"

    chosen = chosen.drop_duplicates("date").sort_values("date").reset_index(drop=True)
    if len(chosen) != chosen["date"].nunique():
        raise RuntimeError("Duplicate VIX dates remain after normalization")

    coverage = {
        "requested_start": args.start,
        "requested_end": args.end,
        "rows": int(len(chosen)),
        "date_min": str(chosen["date"].min()),
        "date_max": str(chosen["date"].max()),
        "unique_dates": int(chosen["date"].nunique()),
        "selected_source": source,
        "nse_rows_in_window": int(len(nse_study)),
        "nse_date_min": str(nse_study["date"].min()) if not nse_study.empty else None,
        "nse_date_max": str(nse_study["date"].max()) if not nse_study.empty else None,
        "nse_complete": bool(nse_complete),
        "nse_vs_niftyindices_overlap": compare_overlap(nse_study, fallback_df),
        "sources": {
            "nse": NSE_VIX_URL,
            "niftyindices_fallback": NIFTYINDICES_VIX_URL,
        },
    }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    chosen.to_csv(out, index=False)

    meta = Path(args.metadata)
    meta.parent.mkdir(parents=True, exist_ok=True)
    meta.write_text(json.dumps(coverage, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps(coverage, indent=2, default=str))


if __name__ == "__main__":
    main()
