# Phase 4 Candidate: Nested Walk-Forward Validation of the Short-Straddle Near-Miss

## Why this candidate
The Phase 3 short-straddle family was the only tested family with positive in-sample net expectancy and profit factor above 1, although it remained far below the ₹1,000/day target. Phase 3F alternatives using IV/OI/skew structure all failed preliminary promotion.

Phase 4 therefore does not search for a new parameter winner. It asks a stricter question: does the short-straddle near-miss survive honest sequential model selection?

## Validation design
- Universe: NIFTY WEEK and MONTH expiry data in the pinned 2020-12-29 to 2025-12-26 dataset.
- Candidate grid: entry time, stop multiple, target decay, hold period, gap filter, first-15-minute range filter, IV/RV filter.
- Expanding windows: 300 trading-day train, 60-day validation, 5-day embargo, 60-day untouched test, 60-day step.
- Parameter selection occurs only on the validation slice, with a minimum 20 trade-days and positive validation mean.
- The selected configuration is then evaluated once on the untouched test slice.
- Test mean daily net is supplemented by block-bootstrap 95% intervals, profit factor, positive-day rate, total net and drawdown.
- Costs include the project Paytm/NSE assumptions and 0.20-point slippage per leg.

## Promotion gate
A Phase 4 candidate must show positive test expectancy across the walk-forward windows and bootstrap lower bounds above zero. Reaching the user's ₹1,000/day target in most untouched test windows is required for promotion to robustness testing.

A negative or unstable Phase 4 result ends this near-miss family without more parameter tuning.
