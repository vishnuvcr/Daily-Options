# Phase 21 — Regime-Switching Gamma/Vega Strategy

## Research question

Can a fixed regime-switching NIFTY strategy improve consistency by using long gamma only in expansion regimes and short vega only in calm regimes, under the same exact-expiry data and realistic Paytm Money/NSE costs?

## Pre-registration

### Expansion regime
Pass when either:
- |GLOBAL3 z| >= 0.50, or
- |NIFTY opening gap| >= 0.75%.

Trade: long ATM CE + long ATM PE (long straddle).

Fixed risk:
- stop at 0.65× combined entry premium
- target at 1.50× combined entry premium
- time exits: 15 or 30 minutes

### Calm regime
Require all:
- expansion gate fails
- |10-minute NIFTY return| <= 0.30%
- intraday RV20 / prior-120-minute mean RV20 <= 1.00

Trade: short strangle at symmetric OTM offsets 3 or 4 strikes.

Fixed risk grid:
- stop 1.25× or 1.50× entry credit
- target 0.50× entry credit
- time exits: 15 or 30 minutes

### Frozen grid
- 3 entry times: 14:30, 14:45, 15:00 IST
- 2 expiry modes: WEEK, MONTH
- 2 holds: 15, 30 minutes
- expansion: 1 fixed risk profile
- calm: 2 OTM offsets × 2 stop profiles

Total: 60 frozen strategy cells.

## Execution

Exact-expiry TradeMarkk NIFTY options, cached revision 51ca58c.
Earliest common CE/PE execution minute within 3 minutes after the signal.
Entry uses option open; exits use conservative high/low trigger logic and close for the realized exit mark.
NIFTY lot sizes are date-aware.
Base/stress slippage: ₹0.20/₹0.40 premium points per leg.
Costs use the repository Paytm Money/NSE model.

## Validation

Nested walk-forward Train → Validation → Embargo → Test.
No parameter selection on the final test.
Promotion requires:
- positive stress performance,
- adequate trade/day coverage,
- at least one untouched test window >= ₹1,000 net/active lot/day,
- no dependence on a single calendar year,
- no material deterioration under doubled slippage.

No Phase21 parameter will be changed after seeing results.
