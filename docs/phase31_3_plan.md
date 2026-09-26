# Phase 31.3 — Friction-corrected Phase 31.1 reproduction

## Status
ACTIVE — final reproduction before any optimization.

## Purpose
Freeze one unambiguous accounting definition for the Phase 31.1 strategy and produce the authoritative friction-corrected result over the full study period.

## Frozen strategy
- NIFTY 09:30 entry; ATM nearest ₹50.
- Buy 2 lots ATM+200 CE; buy 2 lots ATM-200 PE; sell 1 lot ATM-400 PE.
- Exit 15:10.
- Nearest available expiry on/after the trading date.
- Date-aware lot-size schedule from Phase 31.1.
- Base slippage ₹0.20/order; Stress ₹0.40/order.

## Frozen accounting
- Raw gross = mark-to-market P&L before execution friction.
- Slippage is applied to every execution and therefore reduces execution gross.
- Transaction/statutory charges are calculated separately.
- Net P&L = execution gross − transaction/statutory charges.
- Total friction = slippage + transaction/statutory charges.
- Weekly net is summed from daily net; no double subtraction of slippage.

## Validation gates
1. Full-period executable-day coverage reconciles to Phase 31.2.
2. Lot-size and expiry rules match Phase 31.2.
3. Base and Stress are both completed.
4. No missing/duplicate trading-day anomalies.
5. Weekly aggregation has no nonexistent-field dependency.
6. Base net equals raw gross − slippage − transaction/statutory charges to numerical tolerance.

## Stop rule
Once Base and Stress are fully reproduced and the accounting identity passes, freeze the authoritative Phase 31.1 result. Do not optimize in this phase. The result determines whether a separate strategy-development phase is warranted.