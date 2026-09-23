#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
import pandas as pd

REQUIRED = ["timestamp", "open", "high", "low", "close"]

def load(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    if path.suffix.lower() in {".parquet", ".pq"}:
        return pd.read_parquet(path)
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    raise ValueError(f"unsupported file type: {path}")

def audit(path: Path) -> dict:
    df = load(path)
    columns = {c.lower(): c for c in df.columns}
    missing = [c for c in REQUIRED if c not in columns]

    result = {
        "file": str(path),
        "rows": int(len(df)),
        "columns": list(df.columns),
        "required_columns_missing": missing,
        "duplicate_rows": int(df.duplicated().sum()),
        "null_counts": {c: int(df[c].isna().sum()) for c in df.columns},
        "invalid_ohlc_rows": 0,
        "timestamp_parse_failures": 0,
    }

    if not missing:
        ts = pd.to_datetime(df[columns["timestamp"]], errors="coerce", utc=True)
        result["timestamp_parse_failures"] = int(ts.isna().sum())

        o = pd.to_numeric(df[columns["open"]], errors="coerce")
        h = pd.to_numeric(df[columns["high"]], errors="coerce")
        l = pd.to_numeric(df[columns["low"]], errors="coerce")
        c = pd.to_numeric(df[columns["close"]], errors="coerce")

        bad = (o <= 0) | (h <= 0) | (l <= 0) | (c <= 0) | (h < l) | (h < o) | (h < c) | (l > o) | (l > c)
        result["invalid_ohlc_rows"] = int(bad.fillna(False).sum())
        if not result["timestamp_parse_failures"]:
            result["start_utc"] = str(ts.min())
            result["end_utc"] = str(ts.max())

    return result

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path", type=Path)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()

    result = audit(args.path)
    payload = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)

    bad = (
        result["required_columns_missing"]
        or result["duplicate_rows"] > 0
        or result["invalid_ohlc_rows"] > 0
        or result["timestamp_parse_failures"] > 0
    )
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main())
