#!/usr/bin/env bash
set -euo pipefail
mkdir -p data/cache/hf_nifty_options
if ! find data/cache/hf_nifty_options -type f -name '*.parquet' -print -quit | grep -q .; then
  python -c 'from huggingface_hub import snapshot_download; snapshot_download(repo_id="artist-23/nifty-options-data", repo_type="dataset", revision="45e0a04", local_dir="data/cache/hf_nifty_options", allow_patterns=["NIFTY/**/*.parquet", "NIFTY/**"])'
fi
python -m research.phase3g_oi_confirmed_breakout --data data/cache/hf_nifty_options/NIFTY --out reports/phase3g_base --slippage 0.20
python -m research.phase3g_oi_confirmed_breakout --data data/cache/hf_nifty_options/NIFTY --out reports/phase3g_stress --slippage 0.40
