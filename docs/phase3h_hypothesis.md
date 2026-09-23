# Phase 3H — Option-Price Lead/Lag

## Research question
Do short-horizon changes in near-ATM NIFTY option prices contain incremental information about the next few minutes of spot movement after controlling for the contemporaneous spot move?

## Rationale
Older NIFTY evidence reports that index options and futures can lead the cash index in price discovery. More recent high-frequency work shows that price-discovery effects can be measured at very short horizons, while recent NIFTY OI work finds OI itself is more reactive than predictive. This phase therefore tests the prices of the traded derivatives rather than OI sentiment.

## Pre-registered signal
1. At each eligible minute, identify the common nearest-ATM strike with both call and put observations.
2. Compute 1-minute and 3-minute call/put log returns and the contemporaneous spot return.
3. Build a directional lead score from the average call/put option return minus the contemporaneous spot return, standardized by recent option-return volatility.
4. Enter only when the option-price move is sufficiently larger than the spot move and its sign is persistent across the chosen lookback.
5. Entry occurs on the next executable minute after the signal.
6. Express a bullish signal with a call debit spread and a bearish signal with a put debit spread.
7. Use a fixed absolute ATM strike at entry, 1- or 2-step wing, and 15-, 30- or 60-minute hold.
8. One trade per day per variant.

## Small bounded grid
- Lead lookback: 1, 3 minutes
- Persistence: 1, 2 consecutive observations
- Lead threshold: 0.10%, 0.20%
- Expiry: WEEK, MONTH
- Spread width: 1, 2 strikes
- Hold: 15, 30, 60 minutes

The grid is intentionally small. A family is retired if it does not show positive net OOS expectancy or if performance disappears under 2x slippage. No post-hoc expansion is allowed.

## Cost model
Use the project date-aware NIFTY lot size and cost model, with 0.20 option-premium points per leg base slippage and 0.40 stress slippage.

## Validation
Use train -> validation -> 5-day embargo -> untouched test. Select parameters only from training and validation data. Report test-window P&L, positive-day rate, PF, drawdown, bootstrap confidence intervals, and regime/year breakdowns.

## Stop rule
If the bounded family fails, retire it without enlarging the grid and stop Phase 3 research rather than continuing unconstrained parameter mining.
