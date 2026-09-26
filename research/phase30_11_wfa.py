from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

FOLDS = {
    1: {
        "train": ("2025-09-01", "2026-01-18"),
        "oos": ("2026-01-19", "2026-04-12"),
    },
    2: {
        "train": ("2025-10-27", "2026-03-15"),
        "oos": ("2026-03-16", "2026-06-07"),
    },
    3: {
        "train": ("2025-12-22", "2026-05-10"),
        "oos": ("2026-05-11", "2026-08-02"),
    },
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fold", type=int, choices=FOLDS.keys(), required=True)
    ap.add_argument("--data-root", type=Path, required=True)
    ap.add_argument("--spot-root", type=Path, required=True)
    ap.add_argument("--vix-file", type=Path, required=True)
    ap.add_argument("--out-root", type=Path, required=True)
    ap.add_argument("--slippage", type=float, required=True)
    ap.add_argument("--def-start", type=int, required=True)
    ap.add_argument("--def-count", type=int, default=8)
    args = ap.parse_args()

    engine = Path(__file__).with_name("phase30_10_strangle_air_defense_pnl.py")
    for stage in ("train", "oos"):
        start, end = FOLDS[args.fold][stage]
        out = args.out_root / f"fold_{args.fold}" / stage
        out.mkdir(parents=True, exist_ok=True)
        cmd = [
            sys.executable,
            str(engine),
            "--data-root", str(args.data_root),
            "--spot-root", str(args.spot_root),
            "--vix-file", str(args.vix_file),
            "--out-root", str(out),
            "--slippage", str(args.slippage),
            "--def-start", str(args.def_start),
            "--def-count", str(args.def_count),
            "--start", start,
            "--end", end,
        ]
        subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
