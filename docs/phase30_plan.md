# Phase 30 — Weekly deterministic backtest

## Objective
Run frozen weekly strategies with Paytm Money/NSE costs and base/stress slippage.

## Inputs
Phase 29 READY strategies

## Outputs
reports/phase30_weekly_results/

## Weekly research gate
The program target is **₹5,000 net per traded week** at a fixed declared reference position size. Position size may not be increased solely to satisfy the target.

## Completion gate
Report weekly P&L, median, profitable-week rate, worst week, drawdown and capital efficiency.

## Mandatory controls
- Keep strategy rules frozen once the phase's test definition is registered.
- Account for Paytm Money brokerage, NSE exchange charges, STT, SEBI fee, stamp duty, GST and explicit Base/Stress slippage.
- Preserve information barriers and historical lot sizes.
- Log every implementation/data error in `docs/error_log.md`.
- Update `docs/research_status.md` after each execution.
