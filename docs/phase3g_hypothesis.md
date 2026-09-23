# Phase 3G — Dynamic Break + Post-Break OI Confirmation

## Rationale

The prior fixed-strike OI-break family was retired. A recent 2026 NIFTY event study reports that OI repositioning around structural breaks is associated with the break but does not remain a robust advance predictor out of sample. This phase therefore tests OI as confirmation after price structure has already broken, not as a forecasting signal.

Source:
https://papers.ssrn.com/sol3/Delivery.cfm/7394780.pdf?abstractid=7394780&mirid=1

## Pre-registered signal

1. Build a 1-minute NIFTY spot series from the audited multi-year option dataset.
2. For each minute, compute the previous rolling 15-minute and 30-minute high/low, excluding the current bar.
3. A bullish structural break occurs when spot closes at least 0.05% above the prior rolling high. A bearish break occurs when spot closes at least 0.05% below the prior rolling low.
4. Compute normalized put-minus-call OI across ATM-2 through ATM+2 strikes.
5. Confirm only when the normalized OI differential moves in the same directional sign as the break over a 3-minute or 5-minute comparison window.
6. Enter on the next executable minute.
7. Express a bullish signal with a call debit spread and a bearish signal with a put debit spread.
8. Select the nearest executable ATM strike at entry and a 1-step or 2-step wing in the trade direction; hold absolute strikes through the path.
9. One trade per day per parameter variant; max daily loss remains the project risk limit.
10. Exit on a 50% loss of initial debit, a 75% gain in spread value, or the fixed 60/90-minute time limit, whichever comes first. Path collision is resolved conservatively.

## Small bounded grid

- Break lookback: 15, 30 minutes
- OI confirmation window: 3, 5 minutes
- OI normalized-change threshold: 0.01, 0.02
- Expiry class: WEEK, MONTH
- Spread width: 1, 2 strikes
- Max hold: 60, 90 minutes
- IV/RV filter: none, <= 1.25

Total pre-registered variants: 128.

No post-hoc expansion is allowed. A family is retired if it does not produce positive net OOS expectancy after costs or shows unstable test-window behavior.

## Execution and costs

Use next-minute entry, date-aware NIFTY lot size, the repository Paytm Money/NSE cost model, and 0.20 option-premium points round-trip slippage. A separate 2x slippage/stress rerun is required before any promotion.

## Validation

Train -> validation -> embargo -> untouched test, followed by blocked bootstrap confidence intervals and year/regime/session breakdowns. Final-test parameters are never selected.

## Stop rule

If the bounded grid fails the OOS gate, do not enlarge it. Retire Phase 3G and move to the next predefined hypothesis.
