from pathlib import Path
import json

ROOT = Path("data/cache")
required = {
    "nifty_index": ROOT / "phase31_trademarkk/index/NIFTY.parquet",
    "nifty_options_dir": ROOT / "phase31_trademarkk/options/NIFTY",
}
checks = {}
for k,p in required.items():
    checks[k] = {"path": str(p), "exists": p.exists(), "files": len(list(p.glob("*.parquet"))) if p.is_dir() else None}

# External/global features are intentionally a data gate; this phase does not silently substitute another source.
global_candidates = [
    ROOT / "global",
    ROOT / "phase31_global",
    ROOT / "phase30_global",
]
checks["global_data"] = {
    "available": any(p.exists() and any(p.rglob("*")) for p in global_candidates),
    "candidate_paths": [str(p) for p in global_candidates],
}
checks["india_vix"] = {
    "available": any(p.exists() for p in [
        ROOT / "phase30_9_india_vix",
        ROOT / "phase31_india_vix",
        ROOT / "india_vix.parquet",
    ])
}
out = Path("reports/phase31_4")
out.mkdir(parents=True, exist_ok=True)
(out / "data_gate.json").write_text(json.dumps(checks, indent=2) + "\n")
print(json.dumps(checks, indent=2))
