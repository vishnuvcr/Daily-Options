# Phase 24b data manifest — Rissin/Upstox

Source: https://huggingface.co/datasets/rissin/nse-options-intraday
 pinned revision: 8f7739cab3f38abdcbc6332a6d0a83e1341326e3
Track: upstox_intraday
Underlying: NIFTY
Partitions used: 2024, 2025, 2026
Granularity: 1 minute
Schema fields required by Phase 24b: date, timestamp, underlying, expiry, strike, option_type, open, close.

The workflow runs a hard coverage preflight before any P&L stage. Coverage is computed from the actual cached Parquet content, not from the cache directory's existence.

This source is independent of the TradeMarkk cache used in Phase 24. It is used only to reproduce the already-frozen 270-cell Falcon grid; no parameters are selected or retuned from this source.