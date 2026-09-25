# Phase 26 — Complete channel inventory

## Objective
Enumerate every public video, transcript status, and strategy candidate. No backtesting.

## Inputs
data/equity_income/video_manifest.jsonl

## Outputs
data/equity_income/strategy_registry.csv

## Weekly research gate
The program target is **₹5,000 net per traded week** at a fixed declared reference position size. Position size may not be increased solely to satisfy the target.

## Completion gate
Archive must be complete: zero unresolved acquisition failures.

## Mandatory controls
- Keep strategy rules frozen once the phase's test definition is registered.
- Account for Paytm Money brokerage, NSE exchange charges, STT, SEBI fee, stamp duty, GST and explicit Base/Stress slippage.
- Preserve information barriers and historical lot sizes.
- Log every implementation/data error in `docs/error_log.md`.
- Update `docs/research_status.md` after each execution.
