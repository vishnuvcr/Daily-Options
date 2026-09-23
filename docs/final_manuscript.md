# Final Research Manuscript

## Title
Daily Intraday NSE Options Strategy Research: A Cost-Aware, Leakage-Safe Multi-Phase Evaluation

## Abstract
The research program tested bounded intraday NSE options strategy families under explicit transaction costs, delayed execution, data-quality controls and nested walk-forward validation. No tested family satisfied the promotion gate of positive out-of-sample expectancy with at least one untouched test window reaching Rs 1,000 net per active lot per day. The final exploratory family, opening-range false-break reversion, produced 0/144 positive variants at base and stress friction and negative results in every walk-forward test window. The program therefore closes the current public-data exploratory phase and moves to final synthesis and a data-gap assessment.

## 1. Research questions and hypotheses

### Primary research question
Can a reproducible intraday NSE options strategy be identified that, under realistic Paytm Money/NSE costs and conservative execution assumptions, produces at least Rs 1,000 net P&L per active lot per trading day in genuinely out-of-sample data?

### Secondary questions
1. Which underlying and expiry regimes are most amenable to intraday option trading?
2. Does an edge arise from direction, volatility risk premia, mean reversion, momentum, opening-range behavior, or option microstructure?
3. Do IV, OI, skew and option-pressure variables add information beyond the underlying?
4. Does futures-versus-spot price discovery contain a stable short-horizon signal?
5. How much nominal performance disappears after brokerage, exchange/statutory charges, spread/slippage and delayed execution?
6. Can a candidate survive walk-forward, parameter, regime and cost perturbation?

### Hypotheses
H1: A regime-conditioned directional signal on NIFTY, implemented through a liquid option or defined-risk spread, can outperform unfiltered single-leg option buying.

H2: Option moneyness, IV, OI, skew and related structure contain incremental information useful for entry selection.

H3: Volatility-regime filters can reduce whipsaw and theta losses.

H4: Selective trading can be economically preferable to forcing a position every day.

H5: A strategy that survives realistic costs and walk-forward testing is more informative than one with a larger in-sample return but unstable out-of-sample behavior.

## 2. Literature and market-structure review

Published work on NIFTY high-frequency data provides motivation for futures/spot lead-lag research, including evidence of meaningful futures contribution to price discovery. NIFTY volatility-risk-premium research motivates volatility-aware hypotheses, but does not guarantee that short-volatility implementation remains profitable after tails and execution costs.

Modern option pricing also reflects IV, gamma, OI, liquidity and dealer/inventory dynamics. NSE defines India VIX from NIFTY option quotes and uses it as a measure of expected 30-day volatility. NSE publishes FII/FPI and DII activity reports, and its derivatives corporate-action documentation shows that historical strike, position and lot specifications can change.

The wider market context includes global rates, crude oil, USD/INR, global index futures, geopolitical events and overnight information. These are legitimate future regime variables, but were not retrofitted into the final failed family because the project's bounded stop rules prohibit post-hoc expansion.

## 3. Data and provenance

The principal multi-year option dataset was the pinned `artist-23/nifty-options-data` revision `45e0a04`, audited across all 84 parquet partitions. The project audit recorded about 33.96 million rows across 1,228 dates, with IV/OI/spot fields present; 16 negative-volume rows were quarantined and 485 extreme IV observations were flagged.

The project also used a public one-year one-minute NIFTY sample for early baselines and a Zenodo NIFTY spot/futures/options archive covering 2017-2020 for a separate futures/spot research branch.

A recurring limitation is that public option archives are close/bar oriented rather than complete executable bid/ask/depth histories. Consequently, queue position, true spread and market impact cannot be reconstructed exactly.

## 4. Scientific methodology

### Information barrier
Every feature at time t uses information timestamped at or before t. Entry is delayed to the next executable minute/quote.

### Contract selection
Expiry, strike and option type are chosen deterministically from information available at signal time. NIFTY lot size is resolved by trade date.

### Execution
Most directional tests use defined-risk debit spreads. Costs include brokerage, statutory/exchange charges, spread/slippage assumptions and delayed execution. Base exploratory slippage is 0.20 option-premium points per leg, with 0.40-point stress runs.

### Validation
The core nested design is 180 trading-day training, 60-day validation, 5-day embargo, 60-day untouched test, then a 60-day step. Test data are never used for parameter selection.

### Statistics
Reported measures include mean/median net daily P&L, win rate, positive-day rate, profit factor, drawdown, test-window counts and bootstrap intervals where implemented.

## 5. Cost and broker treatment

The repository uses a conservative Rs 20 per executed order default, with option-sale STT, stamp duty, SEBI turnover fee, GST, exchange charges and slippage. Current public Paytm Money materials have shown different pricing by account/cohort and current FAQ materials can show Rs 10 per unique F&O order; therefore any paper/live stage must use the actual account tariff rather than assume the research default.

NSE's current STT schedule states 0.15% on option sale effective 1 April 2026. The exact brokerage ambiguity does not overturn the major negative findings because several families were substantially negative even before stress slippage.

## 6. Strategy families and empirical results

| Phase | Family | Key result | Decision |
|---|---|---|---|
| 2 | Single-leg directional options | 242 trades; mean all-day net Rs -304.90/lot/day; PF 0.690 | Retired |
| 3 | Vertical spreads / VRP filters | Best tested configurations remained negative | Retired |
| 3 focused | ATM short straddle | Preliminary mean about Rs +233/day, but weak daily consistency and large drawdown | Validate formally |
| 3E | VWAP/RSI momentum | 1,296 variants; best mean all-day net Rs -558.10/day; PF 0.457 | Retired |
| 3F | IV/OI/volume imbalance | 972 variants; best mean all-day net about Rs -17.62/day; PF 0.148 | Retired |
| 3F | IV-skew shock/reversion | 162 variants; best mean all-day net about Rs -3.02/day; PF 0.014 | Retired |
| 4 | Nested short-straddle validation | 432 variants; mean selected test-window net Rs -64.23; 0/22 target-qualified | Retired |
| 3G | Price break + post-break OI confirmation | 128 variants; best base mean all-day net Rs -61.11/day; WFA mean -192.79 | Retired |
| 3H | ATM option price lead-lag | 108 variants; best base mean all-day net Rs -181.83/day; 16/16 WFA windows negative | Retired |
| 3I | Opening-range false-break reversion | 144 variants; best base mean all-day net Rs -854.06/day; 14/14 WFA windows negative | Final exploratory closure |

### 6.1 The short-straddle near-miss

The strongest preliminary result came from an intraday ATM short-straddle configuration. A focused historical screen produced a mean near Rs 233/day, profit factor 1.60 and positive expectancy before formal out-of-sample validation.

The nested Phase 4 result reversed that conclusion:
- 7,331 observations;
- 432 parameter variants;
- 14 walk-forward windows;
- 22 selected test windows;
- 8 positive test windows;
- 0 target-qualified test windows;
- mean selected test-window net Rs -64.23/lot;
- median -Rs 43.69/lot;
- mean selected-test positive-day rate 47.65%;
- no selected-test bootstrap lower 95% bound was positive.

This is the clearest demonstration of why the program required walk-forward validation.

### 6.2 Phase 3G: price break + OI confirmation

The bounded 128-variant family used price-structure breaks as the primary event and OI change only as post-break confirmation. Base slippage produced 0/128 positive mean calendar-day configurations, with best mean -Rs 61.11/lot/day. Stress slippage kept all 128 negative, with best mean -Rs 79.55.

Corrected walk-forward testing produced 13 test windows. Only one base-friction window was positive and none were positive under stress. Mean test-window net was -Rs 192.79 at base friction and -Rs 252.79 under stress.

### 6.3 Phase 3H: option price lead-lag

The 108-variant family tested ATM call/put price pressure over 1/3/5 minutes. The corrected run evaluated 438,043 feature rows and 132,072 executable trades.

Every variant was negative at both friction levels:
- base best mean all-day net: -Rs 181.83/lot/day;
- stress best mean all-day net: -Rs 241.83/lot/day;
- 16/16 walk-forward test windows negative at both frictions;
- base mean test-window net -Rs 191.39;
- stress mean -Rs 251.39.

Forward spot diagnostics also failed to show a stable directional hit-rate advantage.

### 6.4 Final exploratory family: opening-range false-break reversion

The final family used a first 5/15/30-minute opening range, false-break excursions of 0.05%/0.10%, re-entry confirmation of 0.02%/0.05%, WEEK/MONTH expiry, 1/2-strike spreads and 15/30/60-minute holds.

Canonical run 35919447949:
- 404,235 spot feature rows;
- 119,196 signal rows;
- 118,860 executable trades;
- 144 pre-registered variants;
- base: 0/144 positive;
- base best mean all-calendar-day net -Rs 854.06/lot/day;
- best PF 0.0357;
- best trade win rate 20.05%;
- 14/14 WFA test windows negative;
- base mean test-window net -Rs 1,626.99/lot;
- stress best mean all-day net -Rs 886.27/lot/day;
- stress mean test-window net -Rs 1,686.99/lot.

Forward spot diagnostics produced correct-direction hit rates near 48.8%, 50.0% and 50.9% at 15, 30 and 60 minutes respectively, which did not support a stable reversal edge.

## 7. Statistical interpretation

The target was Rs 1,000 net per active lot per day. No accepted family reached this threshold in an untouched test window while also satisfying the broader validation gate.

The negative findings should be interpreted as **bounded evidence about the tested families and datasets**, not as a mathematical proof that no profitable intraday NIFTY strategy exists.

The research design reduced selection bias by fixing each family before looking at its test result. The absence of positive test windows in the final three exploratory families is materially different from a strategy that is merely noisy around zero.

Where bootstrap intervals were calculated, they remained below zero for the important failed walk-forward families. This reduces the plausibility that the negative mean arose only from one or two extreme observations.

