from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

KEYS = [
    "entry_day", "entry_time", "expiry_choice", "strike_method",
    "trigger", "action", "risk",
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--out-root", type=Path, required=True)
    args = ap.parse_args()

    files = sorted(args.root.rglob("leaderboard.csv"))
    if not files:
        raise RuntimeError("No shard leaderboards found")

    frames = []
    for f in files:
        regime = "stress" if "stress" in f.parts else "base" if "base" in f.parts else None
        if regime is None:
            raise RuntimeError(f"Cannot infer regime from artifact path: {f}")
        z = pd.read_csv(f)
        z["regime"] = regime
        frames.append(z)

    allz = pd.concat(frames, ignore_index=True)
    if len(allz) != 1440:
        raise RuntimeError(f"Expected 1440 aggregated rows, got {len(allz)}")

    for regime in ("base", "stress"):
        z = allz[allz.regime == regime].copy()
        if len(z) != 720:
            raise RuntimeError(f"{regime}: expected 720 rows, got {len(z)}")
        if z.duplicated(KEYS).any():
            raise RuntimeError(f"{regime}: duplicate cells detected")
        out = args.out_root / regime
        out.mkdir(parents=True, exist_ok=True)
        z = z.sort_values(["gate", "mean_weekly_net"], ascending=[False, False])
        z.to_csv(out / "leaderboard.csv", index=False)

        passed = int(z["gate"].sum())
        best = z.iloc[0].to_dict()
        summary = {
            "regime": regime,
            "registered_cells": 720,
            "aggregated_cells": int(len(z)),
            "duplicate_cells": 0,
            "passed_gate": passed,
            "best_cell": best,
            "pnl_authorized": True,
            "study_window": ["2025-09-01", "2026-08-31"],
        }
        (out / "summary.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")
        diagnostics = {
            "shard_files": int(sum(1 for f in files if regime in f.parts)),
            "trade_records": int(z["trades"].sum()),
            "max_execution_coverage": float(z["execution_coverage"].max()),
            "vix_rows_expected": 248,
        }
        (out / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2, default=str) + "\n")

    overall = {
        "registered_cells_per_regime": 720,
        "regimes": ["base", "stress"],
        "total_rows": 1440,
        "base_passed": int(allz[allz.regime == "base"]["gate"].sum()),
        "stress_passed": int(allz[allz.regime == "stress"]["gate"].sum()),
        "pnl_authorized": True,
    }
    args.out_root.mkdir(parents=True, exist_ok=True)
    (args.out_root / "overall_summary.json").write_text(json.dumps(overall, indent=2) + "\n")
    print(json.dumps(overall, indent=2))


if __name__ == "__main__":
    main()
