# Phase 31 — Regime robustness

## Objective
Segment by India VIX, trend/range, gap, expiry distance, global volatility and other applicable variables.

## Inputs
Phase 30 surviving weekly strategies

## Outputs
reports/phase31_regime/

## Weekly research gate
The program target is **₹5,000 net per traded week** at a fixed declared reference position size. Position size may not be increased solely to satisfy the target.

## Completion gate
No regime-specific retuning; only robustness diagnostics and predeclared conditional variants.

## Mandatory controls
- Keep strategy rules frozen once the phase's test definition is registered.
- Account for Paytm Money brokerage, NSE exchange charges, STT, SEBI fee, stamp duty, GST and explicit Base/Stress slippage.
- Preserve information barriers and historical lot sizes.
- Log every implementation/data error in `docs/error_log.md`.
- Update `docs/research_status.md` after each execution.
