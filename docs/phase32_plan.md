# Phase 32 — Nested walk-forward

## Objective
Perform train/validation/test selection without test leakage.

## Inputs
Phase 31 survivors

## Outputs
reports/phase32_wfa/

## Weekly research gate
The program target is **₹5,000 net per traded week** at a fixed declared reference position size. Position size may not be increased solely to satisfy the target.

## Completion gate
Weekly ₹5,000 target must survive untouched test windows.

## Mandatory controls
- Keep strategy rules frozen once the phase's test definition is registered.
- Account for Paytm Money brokerage, NSE exchange charges, STT, SEBI fee, stamp duty, GST and explicit Base/Stress slippage.
- Preserve information barriers and historical lot sizes.
- Log every implementation/data error in `docs/error_log.md`.
- Update `docs/research_status.md` after each execution.
