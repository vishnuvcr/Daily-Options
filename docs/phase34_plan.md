# Phase 34 — Portfolio research

## Objective
Combine only individually validated strategies and study weekly P&L correlation, margin overlap and joint drawdown.

## Inputs
Phase 33 survivors

## Outputs
reports/phase34_portfolio/

## Weekly research gate
The program target is **₹5,000 net per traded week** at a fixed declared reference position size. Position size may not be increased solely to satisfy the target.

## Completion gate
Do not manufacture target via leverage; report reference capital.

## Mandatory controls
- Keep strategy rules frozen once the phase's test definition is registered.
- Account for Paytm Money brokerage, NSE exchange charges, STT, SEBI fee, stamp duty, GST and explicit Base/Stress slippage.
- Preserve information barriers and historical lot sizes.
- Log every implementation/data error in `docs/error_log.md`.
- Update `docs/research_status.md` after each execution.
