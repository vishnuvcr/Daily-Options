# Phase 3H Results — Option Price Lead/Lag

## Canonical run
- GitHub Actions run: 35918269274
- Accepted artifact: 10776640997
- Dataset revision: artist-23/nifty-options-data 45e0a04
- Features: 441,700
- Signals: 117,408
- Executable paths: 117,408
- Pre-registered variants: 96

## Base friction — 0.20 option-premium points
- All 96 variants had negative mean calendar-day net.
- Best variant: WEEK expiry, 3-minute lead lookback, 15-minute hold, 1-step width, 0.20% threshold.
- Best mean calendar-day net: **-Rs 196.50/lot/day**.
- Best positive-day rate: **13.82%**.
- Best profit factor: **0.107**.
- Best variant max drawdown: about **-Rs 240.2k/lot**.
- Target-qualified variants: 0.

## Stress friction — 0.40 option-premium points
- All 96 variants remained negative.
- Best mean calendar-day net: **-Rs 256.50/lot/day**.
- Best positive-day rate: **8.99%**.
- Best profit factor: **0.062**.
- Best variant max drawdown: about **-Rs 313.5k/lot**.
- Target-qualified variants: 0.

## Nested walk-forward
The repository walk-forward rule used 180 trading days of training, 60 validation days, a 5-day embargo and 60 test days, stepping 60 trading days. Parameters were selected from training/validation only.

### Base
- Test windows: 16
- Positive test windows: 0/16
- Target-qualified test windows: 0/16
- Mean test-window net: **-Rs 205.39/lot**
- Median test-window net: **-Rs 201.09/lot**
- Bootstrap 95% interval for the mean test-window net: approximately **[-Rs 241.81, -Rs 167.84]**

### Stress
- Test windows: 16
- Positive test windows: 0/16
- Target-qualified test windows: 0/16
- Mean test-window net: **-Rs 265.39/lot**
- Median test-window net: **-Rs 261.09/lot**
- Bootstrap 95% interval: approximately **[-Rs 301.81, -Rs 227.84]**

## Decision
**Phase 3H FAIL_PRELIMINARY; retire the option-price lead/lag family.**

The family fails the target by a wide margin, has very low positive-day frequency, large cumulative drawdowns, and remains negative under walk-forward selection and doubled slippage.

## Limitations
- Public option-chain data are closing-price based, not full executable bid/ask/depth.
- ATM feature construction can be affected by sparse strike timestamps.
- This result is specific to the tested option-price score and bounded grid; it does not prove that all option-price microstructure signals are useless.

## Next hypothesis
Test **NIFTY futures-to-spot lead/lag as a causal signal**, then use a defined-risk option debit spread for execution. India-specific literature reports robust futures-to-spot price discovery at intraday horizons, including recent work using 5-minute NIFTY/SGX-NSE futures data. The data source must first pass a schema/date/session validation gate.
