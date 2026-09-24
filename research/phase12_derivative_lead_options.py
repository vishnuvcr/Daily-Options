from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


MIN_TRADING_DAYS = 300
MIN_TIMESTAMP_OVERLAP = 0.90
MIN_OPTION_ENTRY_COVERAGE = 0.80


def normalize_futures(df: pd.DataFrame) -> pd.DataFrame:
    required = {"datetime", "close"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"missing futures columns: {sorted(missing)}")
    x = df.copy()
    x["datetime"] = pd.to_datetime(x["datetime"])
    x["close"] = pd.to_numeric(x["close"], errors="coerce")
    if "contract_month_key" not in x.columns:
        if "expiry" not in x.columns:
            raise ValueError("missing contract_month_key/expiry")
        exp = pd.to_datetime(x["expiry"], errors="coerce")
        x["contract_month_key"] = exp.dt.year * 100 + exp.dt.month
    x = x.dropna(subset=["datetime", "close", "contract_month_key"])
    x = x.loc[x["close"] > 0].copy()
    return x.sort_values(["datetime", "expiry"]).drop_duplicates(["datetime", "expiry"], keep="last")


def build_nearest_contract(df: pd.DataFrame) -> pd.DataFrame:
    x = normalize_futures(df)
    x["trade_date"] = x["datetime"].dt.date
    current_key = x["trade_date"].map(lambda d: d.year * 100 + d.month)
    valid = x.loc[x["contract_month_key"] >= current_key].copy()
    if valid.empty:
        raise ValueError("no non-current futures contract months available")
    idx = valid.groupby("datetime")["contract_month_key"].idxmin()
    out = valid.loc[idx].sort_values("datetime").reset_index(drop=True)
    out = out.rename(columns={"close": "futures_close"})
    return out


def data_gate(futures: pd.DataFrame, spot: pd.DataFrame) -> dict:
    f = build_nearest_contract(futures)
    s = spot.copy()
    s["datetime"] = pd.to_datetime(s["datetime"])
    s["spot_close"] = pd.to_numeric(s["spot_close"], errors="coerce")
    s = s.dropna(subset=["datetime", "spot_close"]).loc[lambda x: x.spot_close > 0]

    fd = f["datetime"].dt.date.nunique()
    overlap = len(set(f["datetime"]).intersection(set(s["datetime"])))
    denom = min(len(f), len(s))
    overlap_ratio = overlap / denom if denom else 0.0

    return {
        "futures_rows": int(len(f)),
        "spot_rows": int(len(s)),
        "futures_trading_days": int(fd),
        "exact_expiry_required_for_promotion": True,
        "timestamp_overlap_rows": int(overlap),
        "timestamp_overlap_ratio_min_side": float(overlap_ratio),
        "gate": "PASS"
        if fd >= MIN_TRADING_DAYS and overlap_ratio >= MIN_TIMESTAMP_OVERLAP
        else "FAIL",
    }


def lead_features(futures: pd.DataFrame, spot: pd.DataFrame, window: int) -> pd.DataFrame:
    f = build_nearest_contract(futures)[["datetime", "futures_close"]]
    s = spot.copy()
    s["datetime"] = pd.to_datetime(s["datetime"])
    s["spot_close"] = pd.to_numeric(s["spot_close"], errors="coerce")
    x = f.merge(s[["datetime", "spot_close"]], on="datetime", how="inner").sort_values("datetime")
    f_ret = x["futures_close"].pct_change(window)
    s_ret = x["spot_close"].pct_change(window)
    f_vol = f_ret.rolling(60, min_periods=60).std()
    s_vol = s_ret.rolling(60, min_periods=60).std()
    x["fut_z"] = f_ret / f_vol.replace(0, np.nan)
    x["spot_z"] = s_ret / s_vol.replace(0, np.nan)
    x["lead_gap"] = x["fut_z"] - x["spot_z"]
    x["direction"] = np.where(x["fut_z"] > 0, "CALL", np.where(x["fut_z"] < 0, "PUT", ""))
    return x


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--futures", type=Path, required=True)
    ap.add_argument("--spot", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    futures = pd.read_parquet(args.futures)
    spot = pd.read_parquet(args.spot)

    gate = data_gate(futures, spot)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "phase12_data_gate.json").write_text(json.dumps(gate, indent=2), encoding="utf-8")

    if gate["gate"] != "PASS":
        print(json.dumps(gate, indent=2))
        return

    parts = []
    for window in (1, 3):
        z = lead_features(futures, spot, window)
        z["lead_window"] = window
        parts.append(z)

    features = pd.concat(parts, ignore_index=True)
    features.to_parquet(args.out / "phase12_lead_features.parquet", index=False)
    print(json.dumps(gate, indent=2))
    print(json.dumps({
        "feature_rows": int(len(features)),
        "lead_windows": [1, 3],
        "thresholds": [0.75, 1.00, 1.50],
        "stage": "DATA_READY_PRELIMINARY",
    }, indent=2))


if __name__ == "__main__":
    main()
