from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


REQUIRED = [
    "datetime", "date", "open", "high", "low", "close",
    "iv", "volume", "oi", "strike_price", "spot",
    "expiry_type", "strike_type", "option_type",
]


def audit(path: Path) -> dict:
    df = pd.read_parquet(path, columns=REQUIRED)
    out = {
        "rows": int(len(df)),
        "date_min": str(pd.to_datetime(df["datetime"]).min()),
        "date_max": str(pd.to_datetime(df["datetime"]).max()),
        "unique_days": int(df["date"].nunique()),
        "iv_nonnull_fraction": float(df["iv"].notna().mean()),
        "oi_nonnull_fraction": float(df["oi"].notna().mean()),
        "volume_nonnull_fraction": float(df["volume"].notna().mean()),
        "spot_nonnull_fraction": float(df["spot"].notna().mean()),
        "option_types": sorted(df["option_type"].dropna().astype(str).str.upper().unique().tolist()),
        "expiry_types": sorted(df["expiry_type"].dropna().astype(str).unique().tolist()),
        "strike_types": sorted(df["strike_type"].dropna().astype(str).unique().tolist()),
    }
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=Path("reports/phase3f_data_audit.json"))
    args = ap.parse_args()
    result = audit(args.data)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
