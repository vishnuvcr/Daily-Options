# Phase 29 — Historical data feasibility

## Objective
Check data coverage, expiry identity, quote completeness, lot sizes, transaction costs and required regime variables.

## Inputs
Phase 28 canonical strategies

## Outputs
reports/phase29_data_feasibility.csv

## Weekly research gate
The program target is **₹5,000 net per traded week** at a fixed declared reference position size. Position size may not be increased solely to satisfy the target.

## Completion gate
Only strategies with sufficient non-leaky data proceed.

## Mandatory controls
- Keep strategy rules frozen once the phase's test definition is registered.
- Account for Paytm Money brokerage, NSE exchange charges, STT, SEBI fee, stamp duty, GST and explicit Base/Stress slippage.
- Preserve information barriers and historical lot sizes.
- Log every implementation/data error in `docs/error_log.md`.
- Update `docs/research_status.md` after each execution.
