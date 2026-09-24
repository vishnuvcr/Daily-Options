from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from research.phase9_regime_credit_spread import leaderboard, walk_forward


def aggregate_downloads(download_root: Path, out_root: Path) -> dict:
    out_root.mkdir(parents=True, exist_ok=True)
    summary = {}
    for friction, slippage in (("base", 0.20), ("stress", 0.40)):
        files = sorted(download_root.rglob(f"{friction}_shard_*_trades.csv"))
        frames = [pd.read_csv(p) for p in files]
        trades = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
        friction_dir = out_root / f"phase9-{friction}"
        friction_dir.mkdir(parents=True, exist_ok=True)
        trades.to_csv(friction_dir / "phase9_trades.csv", index=False)
        board = leaderboard(trades)
        board.to_csv(friction_dir / "phase9_leaderboard.csv", index=False)
        wf, wfs = walk_forward(trades)
        wf.to_csv(friction_dir / "phase9_walk_forward.csv", index=False)
        payload = {
            "trades": int(len(trades)),
            "variants_observed": int(trades["variant_id"].nunique()) if not trades.empty else 0,
            "target_qualified_prelim": int((board["mean_active_day_net"] >= 1000).sum()) if not board.empty else 0,
            "best": board.iloc[0].to_dict() if not board.empty else None,
            "slippage_points": slippage,
            "walk_forward": wfs,
        }
        (friction_dir / "phase9_summary.json").write_text(json.dumps(payload, indent=2, default=str))
        summary[friction] = payload
    (out_root / "phase9_decision_summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print(json.dumps(summary, indent=2, default=str))
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--downloads", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    aggregate_downloads(args.downloads, args.out)


if __name__ == "__main__":
    main()
