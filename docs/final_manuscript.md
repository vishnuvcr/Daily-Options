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

