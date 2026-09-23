# Phase 3F Iron-Fly Volatility Regime — Result

Run: GitHub Actions `35907469676`
Dataset: pinned `artist-23/nifty-options-data` revision `45e0a04`

## Stage 1 decision-grade screen

162 parameter/expiry combinations were evaluated after signal and entry-quote validation. The full Stage-1 grid used elevated IV/RV plus low trend/low OI-imbalance/low volume-imbalance regime conditions, a 120-minute time exit, defined-risk ATM short straddle with ±2-strike wings, and the project cost model with eight executed orders and 0.20-point per-leg slippage.

No Stage-1 configuration reached positive net expectancy.

Best Stage-1 configuration:
- MONTH expiry
- IV/RV >= 1.50
- absolute 15-minute spot return <= 0.05%
- absolute OI imbalance <= 5%
- absolute volume imbalance <= 5%
- 29 trades
- mean active-day net: -₹445.14
- mean all-calendar-day net: -₹10.56
- trade win rate: 0.00%
- positive-day rate: 0.00%
- profit factor: 0.000
- total net: -₹12,908.97
- max drawdown: -₹12,386.34
- mean entry credit: 89.27 index points

The WEEK expiry counterpart also remained negative (mean all-day net -₹10.99, win rate 15.69%, profit factor 0.177).

## Stage 2

Stage 2 was intentionally not promoted because the entire Stage-1 grid failed the pre-specified positive-expectancy/profit-factor gate. An implementation issue that could have combined Stage-1 bases in a Stage-2 result was found after the run and corrected; no Stage-2 statistic is used in the research decision.

## Decision

**FAIL_PRELIMINARY — retire the iron-fly volatility-regime hypothesis.**

The strategy family is not carried forward to parameter tuning. The next materially different Phase 3F hypothesis is OI repositioning/change around intraday price-structure breaks, using fixed daily strike bands to avoid mixing dynamically changing ATM contracts.
