from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


SESSION_START = "09:15"
SESSION_END = "15:30"


@dataclass(frozen=True)
class Variant:
    feature: str
    lookback: int
    threshold_bps: float
    mode: str

    def key(self) -> str:
        return json.dumps({
            "feature": self.feature,
            "lookback": self.lookback,
            "threshold_bps": self.threshold_bps,
            "mode": self.mode,
        }, sort_keys=True)


def diagnostic_grid() -> list[Variant]:
    return [
        Variant(feature, lb, th, mode)
        for feature in ("futures_return", "lead_gap", "basis_change")
        for lb in (1, 3, 5)
        for th in (0.0, 2.0, 5.0, 10.0)
        for mode in ("continuation", "contrarian")
    ]


def normalize_table(df: pd.DataFrame) -> pd.DataFrame:
    def key(name: object) -> str:
        return re.sub(r"[^a-z0-9]", "", str(name).strip().lower())

    cols = {key(c): c for c in df.columns}

    date_col = next((cols[k] for k in ("tradedate", "tradedt", "date", "datetime", "timestamp") if k in cols), None)
    time_col = next((cols[k] for k in ("tradetime", "time") if k in cols), None)
    close_col = next((cols[k] for k in ("close", "ltp", "last") if k in cols), None)
    if date_col is None or time_col is None or close_col is None:
        raise ValueError(f"Unable to identify date/time/close columns: {list(df.columns)}")

    out = df.copy()
    if time_col is None and date_col is not None:
        out["datetime"] = pd.to_datetime(out[date_col], errors="coerce")
    else:
        out["datetime"] = pd.to_datetime(
            out[date_col].astype(str).str.strip() + " " + out[time_col].astype(str).str.strip(),
            errors="coerce",
        )
    for field in ("open", "high", "low", "close", "volume"):
        if field in cols:
            out[field] = pd.to_numeric(out[cols[field]], errors="coerce")
    out["close"] = pd.to_numeric(out[close_col], errors="coerce")
    out = out.loc[out["datetime"].notna() & out["close"].gt(0)].copy()
    out["trade_date"] = out["datetime"].dt.date
    out = out.sort_values("datetime").drop_duplicates("datetime", keep="last")
    return out


def candidate_files(root: Path) -> list[Path]:
    files = [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in {".xlsx", ".xls", ".csv"}]
    if not files:
        raise FileNotFoundError(f"No CSV/XLS/XLSX files found under {root}")
    return files


def read_table(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    return pd.read_excel(path)


def identify_spot_futures(root: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    files = candidate_files(root)

    def classify(path: Path) -> str | None:
        name = path.name.lower()
        if name == "nifty_f1.csv" or "nifty_f1" in name:
            return "futures"
        if name == "nifty.csv" or (("nifty" in name) and "future" not in name and "option" not in name):
            return "spot"
        return None

    spot_paths = [p for p in files if classify(p) == "spot"]
    futures_paths = [p for p in files if classify(p) == "futures"]

    if not spot_paths or not futures_paths:
        raise RuntimeError({
            "files": [str(p) for p in files],
            "spot_paths": [str(p) for p in spot_paths],
            "futures_paths": [str(p) for p in futures_paths],
        })

    def load_many(paths: list[Path]) -> tuple[pd.DataFrame, dict]:
        frames = []
        file_meta = []
        for path in sorted(paths):
            raw = read_table(path)
            frame = normalize_table(raw)
            if frame.empty:
                raise ValueError(f"No valid rows after normalization: {path}")
            frames.append(frame)
            file_meta.append({
                "path": str(path),
                "raw_rows": int(len(raw)),
                "normalized_rows": int(len(frame)),
            })
        out = pd.concat(frames, ignore_index=True)
        out = out.sort_values("datetime").drop_duplicates("datetime", keep="last").reset_index(drop=True)
        return out, {"files": file_meta, "rows_after_concat": int(len(out))}

    spot, spot_meta = load_many(spot_paths)
    fut, fut_meta = load_many(futures_paths)

    meta = {
        "spot_files": spot_meta,
        "futures_files": fut_meta,
        "all_files": [str(p) for p in sorted(files)],
        "spot_date_min": str(spot["trade_date"].min()) if not spot.empty else None,
        "spot_date_max": str(spot["trade_date"].max()) if not spot.empty else None,
        "futures_date_min": str(fut["trade_date"].min()) if not fut.empty else None,
        "futures_date_max": str(fut["trade_date"].max()) if not fut.empty else None,
    }
    return spot, fut, meta

def quality_audit(spot: pd.DataFrame, fut: pd.DataFrame) -> dict:
    def session_minutes(df: pd.DataFrame) -> pd.Series:
        mins = df["datetime"].dt.strftime("%H:%M")
        return df.loc[mins.between(SESSION_START, "15:29")].groupby("trade_date")["datetime"].nunique()

    overlap = len(set(spot["datetime"]) & set(fut["datetime"]))
    common_dates = sorted(set(spot["trade_date"]) & set(fut["trade_date"]))
    smins = session_minutes(spot)
    fmins = session_minutes(fut)

    if common_dates:
        common_s = smins.reindex(common_dates)
        common_f = fmins.reindex(common_dates)
        completeness = float((common_s.ge(350) & common_f.ge(350)).mean())
    else:
        completeness = 0.0

    basis = None
    merged = spot[["datetime", "close"]].rename(columns={"close": "spot_close"}).merge(
        fut[["datetime", "close"]].rename(columns={"close": "fut_close"}),
        on="datetime", how="inner"
    )
    if not merged.empty:
        basis = float((merged["fut_close"] / merged["spot_close"] - 1.0).median() * 10000.0)

    return {
        "spot_rows": int(len(spot)),
        "futures_rows": int(len(fut)),
        "spot_dates": int(spot["trade_date"].nunique()),
        "futures_dates": int(fut["trade_date"].nunique()),
        "common_dates": int(len(common_dates)),
        "timestamp_overlap_rows": int(overlap),
        "timestamp_overlap_ratio": float(overlap / max(min(len(spot), len(fut)), 1)),
        "common_day_session_completeness_ge350": completeness,
        "spot_duplicate_timestamps_after_normalize": 0,
        "futures_duplicate_timestamps_after_normalize": 0,
        "median_basis_bps": basis,
        "date_min": str(min(common_dates)) if common_dates else None,
        "date_max": str(max(common_dates)) if common_dates else None,
        "gate": (
            "PASS"
            if common_dates and completeness >= 0.90 and overlap / max(min(len(spot), len(fut)), 1) >= 0.90
            else "FAIL"
        ),
    }


def build_features(spot: pd.DataFrame, fut: pd.DataFrame) -> pd.DataFrame:
    x = spot[["datetime", "trade_date", "close"]].rename(columns={"close": "spot"})
    y = fut[["datetime", "close"]].rename(columns={"close": "futures"})
    z = x.merge(y, on="datetime", how="inner").sort_values("datetime")
    z["trade_date"] = z["datetime"].dt.date
    z = z.sort_values(["trade_date", "datetime"]).copy()
    z["basis_bps"] = (z["futures"] / z["spot"] - 1.0) * 10000.0
    grouped = z.groupby("trade_date", sort=False)
    for k in (1, 3, 5):
        z[f"fut_ret_{k}"] = grouped["futures"].transform(lambda s: np.log(s / s.shift(k)))
        z[f"spot_ret_{k}"] = grouped["spot"].transform(lambda s: np.log(s / s.shift(k)))
        z[f"lead_gap_{k}_bps"] = (z[f"fut_ret_{k}"] - z[f"spot_ret_{k}"]) * 10000.0
        z[f"basis_change_{k}_bps"] = grouped["basis_bps"].transform(lambda s: s - s.shift(k))
        z[f"fwd_spot_{k}_bps"] = grouped["spot"].transform(
            lambda s: np.log(s.shift(-k) / s) * 10000.0
        )
    z = z.loc[
        z["datetime"].dt.strftime("%H:%M:%S").between("09:30:00", "12:30:00")
    ].copy()
    return z


def diagnostic(features: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for v in diagnostic_grid():
        if v.feature == "futures_return":
            raw = features[f"fut_ret_{v.lookback}"] * 10000.0
        elif v.feature == "lead_gap":
            raw = features[f"lead_gap_{v.lookback}_bps"]
        else:
            raw = features[f"basis_change_{v.lookback}_bps"]
        x = features.loc[raw.abs().ge(v.threshold_bps)].copy()
        if x.empty:
            continue
        if v.mode == "continuation":
            x["direction"] = np.sign(raw.loc[x.index])
        else:
            x["direction"] = -np.sign(raw.loc[x.index])
        x = x.loc[x["direction"].ne(0)].sort_values(["trade_date", "datetime"])
        x = x.drop_duplicates(["trade_date"], keep="first")
        for horizon in (1, 3, 5):
            fwd = x[f"fwd_spot_{horizon}_bps"]
            signed = fwd * x["direction"]
            rows.append({
                "variant": v.key(),
                "lookback": v.lookback,
                "threshold_bps": v.threshold_bps,
                "mode": v.mode,
                "horizon": horizon,
                "events": int(len(x)),
                "mean_signed_fwd_bps": float(signed.mean()),
                "median_signed_fwd_bps": float(signed.median()),
                "hit_rate": float((signed > 0).mean()),
            })
    return pd.DataFrame(rows)


def run(root: Path, out_dir: Path) -> dict:
    spot, fut, meta = identify_spot_futures(root)
    audit = quality_audit(spot, fut)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "phase3i_source_manifest.json").write_text(json.dumps(meta, indent=2, default=str))
    (out_dir / "phase3i_data_quality.json").write_text(json.dumps(audit, indent=2, default=str))

    if audit["gate"] != "PASS":
        summary = {"stage": "DATA_GATE", "gate": "FAIL", "audit": audit}
        (out_dir / "phase3i_summary.json").write_text(json.dumps(summary, indent=2, default=str))
        print(json.dumps(summary, indent=2, default=str))
        return summary

    features = build_features(spot, fut)
    diag = diagnostic(features)
    diag.to_csv(out_dir / "phase3i_leadlag_diagnostic.csv", index=False)

    informative = diag.loc[
        (diag["horizon"].isin([1, 3, 5])) &
        (diag["hit_rate"] >= 0.55) &
        (diag["mean_signed_fwd_bps"] >= 2.0)
    ]
    summary = {
        "stage": "PREDICTIVE_DIAGNOSTIC",
        "data_gate": "PASS",
        "features": int(len(features)),
        "diagnostic_variants": 72,
        "diagnostic_rows": int(len(diag)),
        "informative_rows": int(len(informative)),
        "predictive_gate": "PASS" if not informative.empty else "FAIL",
        "next_stage": "OPTION_IMPLEMENTATION" if not informative.empty else "RETIRE",
    }
    (out_dir / "phase3i_summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print(json.dumps(summary, indent=2, default=str))
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=Path("reports/phase3i"))
    args = ap.parse_args()
    run(args.data, args.out)


if __name__ == "__main__":
    main()
