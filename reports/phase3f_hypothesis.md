# Phase 3F — Option Microstructure / Volatility-Regime Hypothesis

## Research question
Does information contained in the option chain (IV, OI, strike distribution and option-flow changes) identify intraday volatility/direction regimes that improve net NIFTY option trading after realistic costs?

## Why this is next
Phase 3E failed after correcting its feature specification. Further tuning of RSI/VWAP/EMA would be diminishing-return parameter search. The next hypothesis must add economically different information.

Recent public evidence is consistent with testing option-market positioning and OI dynamics, but these sources are hypotheses rather than proof of profitability. A 2026 Indian-derivatives study reports that volatility shocks are associated with increased option trading activity and position adjustment; a recent NIFTY study reports an association between OI repositioning and intraday price-structure breaks. These motivate an auditable OI/IV regime test.

## Candidate signals
1. ATM IV level and 5/15/30-minute IV change.
2. IV minus realized-volatility proxy.
3. ATM and near-ATM call/put OI imbalance and its change.
4. Call/put volume imbalance.
5. Strike-band OI concentration and its migration.
6. Gamma proxy computed from IV, spot, strike, time-to-expiry and OI, with explicit caveat that OI does not reveal dealer sign.
7. Regime interaction: trend vs range, high vs low realized volatility, and opening gap.

## Trading structures
A. Directional debit spread when chain imbalance + price regime agree.
B. Defined-risk short-volatility spread when IV is elevated and realized volatility is contracting.
C. No-trade when signals disagree.

Naked short options are not the default structure in this phase; risk is capped for robustness.

## Information barrier
All chain features at time t use bars timestamped <= t. Contract selection is deterministic. Entry is delayed to the next executable bar. Same-bar OHLC ambiguity is resolved conservatively.

## Promotion gate
Do not optimize toward the target on the first pass. First require:
- enough observations across multiple years/regimes;
- positive net expectancy after costs;
- stability across parameter neighborhoods;
- no single year/day dominates;
- adverse slippage remains viable.

Only then run the Rs 1,000/day target tournament.

## Data priority
Primary external candidate: artist-23/nifty-options-data (2020-12-29 to 2025-12-26; 33.96M rows; includes IV, OI, volume, spot, strike and expiry metadata).
Secondary candidate: thetrademarkk/india-index-options-1m (~2021-2026; 377M rows; OHLCV+OI).
The primary dataset is preferred for Phase 3F because IV and OI are explicit in the schema.
