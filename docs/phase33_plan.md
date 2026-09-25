# Phase 33 — Later-period OOS

## Objective
Test the unchanged rule on later unseen data.

## Inputs
Phase 32 survivors

## Outputs
reports/phase33_oos/

## Weekly research gate
The program target is **₹5,000 net per traded week** at a fixed declared reference position size. Position size may not be increased solely to satisfy the target.

## Completion gate
Pass Base, Stress, drawdown and weekly robustness gates.

## Mandatory controls
- Keep strategy rules frozen once the phase's test definition is registered.
- Account for Paytm Money brokerage, NSE exchange charges, STT, SEBI fee, stamp duty, GST and explicit Base/Stress slippage.
- Preserve information barriers and historical lot sizes.
- Log every implementation/data error in `docs/error_log.md`.
- Update `docs/research_status.md` after each execution.
