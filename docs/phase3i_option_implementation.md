# Phase 3I — Option Implementation

## Promotion into executable option testing

The strict underlying predictive gate passed with exactly two qualifying signal families:

1. 3-minute futures-minus-spot lead gap, absolute threshold 10 bps, continuation.
2. 3-minute basis change, absolute threshold 10 bps, continuation.

Both had positive mean forward spot return and hit rate above 55% in two forward horizons, with positive directional sign and hit rate above 50% in both halves of the 2017–2020 sample.

The option implementation therefore tests both qualifying families without selecting one in advance.

## Execution grid

For each qualifying signal:

- expiry: WEEK, MONTH;
- vertical width: 1 or 2 OTM strike steps;
- holding period: exactly 5, 10 or 15 minutes;
- bullish futures/spot signal -> NIFTY call debit spread;
- bearish futures/spot signal -> NIFTY put debit spread;
- signal window: 09:30–12:30 IST;
- first qualifying signal per trading day per signal family;
- entry: next executable option minute, allowing at most two minutes after the one-minute signal delay;
- exit: deterministic time exit at the requested holding period, using the last paired option quote no more than one minute before the target exit time;
- no stop/target tuning in this stage;
- date-aware NIFTY lot size;
- base slippage: 0.20 premium points per leg round-trip;
- stress slippage: 0.40 premium points per leg round-trip;
- brokerage/statutory/exchange costs from the repository 2026 Paytm Money/NSE model.

This produces 24 pre-registered execution variants.

## Data source

Option execution uses the pinned `artist-23/nifty-options-data` revision `45e0a04`, already used and cached in Phase 3H. No new parameter tuning is allowed based on the option results.

## Leakage controls

- Futures/spot signal uses only timestamps at or before the signal minute.
- Option strike selection uses only prices available at the executable entry timestamp.
- Exit uses no information after the target hold end.
- Walk-forward selection uses 180 training days, 60 validation days, 5-day embargo, 60 untouched test days, 60-day step.
- Test data are not used for parameter selection.

## Promotion gate

The existing project gate is retained:

- positive net OOS expectancy after all modeled costs;
- at least one untouched test window with net >= Rs 1,000 per active lot/day;
- base and doubled-slippage results are both reported.

A negative family is retired without expanding the grid.

## Research interpretation

A pass here would establish a tradeable implementation candidate, not a claim of live profitability. Paper/shadow validation remains a later phase.
