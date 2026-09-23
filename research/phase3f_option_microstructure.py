from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
import pyarrow.dataset as ds


REQUIRED = [
    "datetime",
    "date",
    "open",
    "high",
    "low",
    "close",
    "iv",
    "volume",
    "oi",
    "strike_price",
    "spot",
    "expiry_type",
    "strike_type",
    "option_type",
]


def discover_parquets(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    files = sorted(path.rglob("*.parquet"))
    if not files:
        raise FileNotFoundError(f"No parquet files found under {path}")
    return files


def audit(path: Path) -> dict:
    files = discover_parquets(path)
    dataset = ds.dataset([str(p) for p in files], format="parquet")
    names = set(dataset.schema.names)
    missing = [c for c in REQUIRED if c not in names]
    if missing:
        return {
            "status": "FAIL_SCHEMA",
            "files": len(files),
            "missing_columns": missing,
            "columns": dataset.schema.names,
        }

    counters = {
        "rows": 0,
        "iv_null": 0,
        "oi_null": 0,
        "volume_null": 0,
        "spot_null": 0,
        "negative_volume": 0,
        "negative_oi": 0,
        "nonpositive_spot": 0,
        "nonpositive_strike": 0,
        "nonpositive_close": 0,
        "invalid_ohlc": 0,
        "iv_over_300": 0,
    }
    days: set[str] = set()
    option_types: set[str] = set()
    expiry_types: set[str] = set()
    strike_types: set[str] = set()
    date_min = None
    date_max = None
    negative_volume_examples: list[dict] = []
    iv_over_300_examples: list[dict] = []

    scanner = dataset.scanner(columns=REQUIRED, batch_size=250_000)
    for batch in scanner.to_batches():
        df = batch.to_pandas()
        counters["rows"] += len(df)

        ts = pd.to_datetime(df["datetime"], errors="coerce")
        if ts.notna().any():
            bmin = ts.min()
            bmax = ts.max()
            date_min = bmin if date_min is None else min(date_min, bmin)
            date_max = bmax if date_max is None else max(date_max, bmax)

        d = df["date"].dropna().astype(str)
        days.update(d.tolist())
        option_types.update(
            df["option_type"].dropna().astype(str).str.upper().tolist()
        )
        expiry_types.update(df["expiry_type"].dropna().astype(str).tolist())
        strike_types.update(df["strike_type"].dropna().astype(str).tolist())

        counters["iv_null"] += int(df["iv"].isna().sum())
        counters["oi_null"] += int(df["oi"].isna().sum())
        counters["volume_null"] += int(df["volume"].isna().sum())
        counters["spot_null"] += int(df["spot"].isna().sum())

        neg = df["volume"] < 0
        iv_high = df["iv"] > 300
        counters["negative_volume"] += int(neg.fillna(False).sum())
        counters["negative_oi"] += int((df["oi"] < 0).fillna(False).sum())
        counters["nonpositive_spot"] += int((df["spot"] <= 0).fillna(False).sum())
        counters["nonpositive_strike"] += int((df["strike_price"] <= 0).fillna(False).sum())
        counters["nonpositive_close"] += int((df["close"] <= 0).fillna(False).sum())
        counters["iv_over_300"] += int(iv_high.fillna(False).sum())

        for mask, sink, limit in (
            (neg, negative_volume_examples, 50),
            (iv_high, iv_over_300_examples, 50),
        ):
            if len(sink) >= limit:
                continue
            cols = [
                "datetime", "date", "iv", "volume", "oi",
                "strike_price", "spot", "expiry_type", "strike_type",
                "option_type", "close",
            ]
            sample = df.loc[mask.fillna(False), cols].head(limit - len(sink))
            sink.extend(sample.astype(str).to_dict(orient="records"))

        high = df["high"]
        low = df["low"]
        oc_max = df[["open", "close"]].max(axis=1)
        oc_min = df[["open", "close"]].min(axis=1)
        counters["invalid_ohlc"] += int(
            ((high < oc_max) | (low > oc_min) | (high < low)).fillna(False).sum()
        )

    rows = counters["rows"] or 1
    result = {
        "status": "PASS" if counters["negative_volume"] == 0 and counters["negative_oi"] == 0
        else "QUARANTINE_DATA_QUALITY",
        "source_path": str(path),
        "files": len(files),
        "file_examples": [str(p) for p in files[:10]],
        "rows": counters["rows"],
        "date_min": str(date_min) if date_min is not None else None,
        "date_max": str(date_max) if date_max is not None else None,
        "unique_days": len(days),
        "iv_nonnull_fraction": 1.0 - counters["iv_null"] / rows,
        "oi_nonnull_fraction": 1.0 - counters["oi_null"] / rows,
        "volume_nonnull_fraction": 1.0 - counters["volume_null"] / rows,
        "spot_nonnull_fraction": 1.0 - counters["spot_null"] / rows,
        "option_types": sorted(option_types),
        "expiry_types": sorted(expiry_types),
        "strike_types": sorted(strike_types),
        "quality_counters": counters,
        "negative_volume_examples": negative_volume_examples,
        "iv_over_300_examples": iv_over_300_examples,
        "required_columns": REQUIRED,
        "strategy_use_note": (
            "Volume features remain disabled until negative-volume rows are explained or "
            "reconciled against an independent source."
            if counters["negative_volume"] > 0
            else "Core IV/OI/price fields pass the basic numerical screen."
        ),
    }
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True, help="Parquet file or directory")
    ap.add_argument("--out", type=Path, default=Path("reports/phase3f_data_audit.json"))
    args = ap.parse_args()

    result = audit(args.data)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    if result.get("status") == "FAIL_SCHEMA":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
