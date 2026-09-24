# Research Plan

## 1. Research questions

Primary question:
Can a reproducible intraday NSE options strategy be identified that, under realistic Paytm Money costs and conservative execution assumptions, produces at least Rs 1,000 net P&L per active lot per trading day on average in a genuinely out-of-sample period?

Secondary questions:
1. Which underlying/expiry regime is most amenable to the target?
2. Does the edge arise from directional movement, volatility risk premium, mean reversion, momentum, opening-range behavior, OI/options microstructure, or a combination?
3. Which regime variables materially condition the edge?
4. How much performance disappears after spread, slippage, delay, brokerage and statutory charges?
5. Can the strategy survive parameter, regime and cost perturbations?

## 2. Hypotheses

H1: A regime-conditioned directional signal on the underlying, executed via a liquid option or defined-risk spread, can outperform an unfiltered option-buying baseline.

H2: Intraday option structure (moneyness, DTE, IV, OI and skew) adds information beyond the underlying price signal.

H3: Volatility-regime filters reduce false breakouts and option-theta losses.

H4: A no-trade filter is economically valuable; forcing a position every day can reduce net expectancy.

H5: A strategy that survives realistic costs and walk-forward validation is more useful than one with the largest raw backtest return.

## 3. Literature/data review already identified

- Indian NIFTY variance-risk-premium literature reports economically meaningful volatility risk premia and significant relationships between realized and implied variance.
- A 2026 preprint reports a NIFTY VRP study using more than 43 million one-minute option bars from Aug-2022 to Mar-2026; it is an external benchmark/data-source lead, not treated as ground truth.
- Zenodo provides one-minute NIFTY spot/futures/options data for 2017-2020; the options archive is about 312 MB.
- A Hugging Face NIFTY options dataset provides about 34M rows from 2020-12-29 to 2025-12-26, including OHLC, IV, volume, OI, strike, spot, expiry type, strike type and option type.
- An open-source NIFTY/BankNIFTY EMA 8/24/72 study reports mixed option results and warns that raw option-buying signals can lose to theta/whipsaw.
- Academic 0DTE studies show that option-market structure, gamma and liquidity-provider hedging can affect intraday volatility; this motivates gamma/flow regime tests.

## 4. Scientific methodology

### Universe
Primary: liquid NSE index options. Secondary: liquid stock/index options when reliable historical contract-level intraday data are available.

### Resolution
One-minute bars preferred. Five-minute aggregation used for robustness. Tick/depth data optional for execution refinement.

### Information barrier
Every feature at time t must use only information timestamped <= t. Entry is on the next executable bar/quote after signal generation unless the source explicitly supports same-bar execution without leakage.

### Contract selection
Expiry, strike and option type are chosen deterministically from information available at signal time. Historical expiry changes and lot-size changes use exchange reference files.

### Execution model
Use conservative bid/ask or adverse bar fills. Run slippage stress multipliers. Penalize market-order execution more than passive execution. Resolve stop/target collisions conservatively.

### Cost model
Round trips include brokerage, exchange transaction charges, SEBI turnover fee, STT, stamp duty, GST on applicable services/fees, and configurable slippage/spread.

### Validation
Nested walk-forward:
Train -> Validation -> Embargo -> Test.
Parameters are selected only on Train/Validation. Final Test remains untouched until the candidate is frozen.

### Statistical analysis
Report net mean/median daily P&L per lot, win rate, payoff ratio, expectancy, profit factor, max drawdown, ulcer index, Sharpe/Sortino with caveats, bootstrap confidence intervals, multiple-testing controls where feasible, regime/year/session breakdown, parameter heatmaps, cost/slippage sensitivity, trade-count and concentration diagnostics.

The primary estimate for the target is OOS mean net daily P&L per active lot, accompanied by confidence intervals and percentiles. The mean alone is not sufficient for promotion.


### Phase 3F data-quality precondition
Before any option-microstructure strategy optimization, every parquet partition in the pinned source revision is audited rather than sampling the first file. Required IV/OI/price fields must be present and numerically coherent. Any anomalous field is quarantined from feature construction until it is reconciled against an independent source or a deterministic transformation is proven safe. In particular, volume is not used merely because the schema contains a volume column.

## 5. Strategy families

A. Directional:
- opening-range breakout + volume/VIX filter
- VWAP trend continuation
- EMA/ADX continuation
- gap continuation/fade
- first-hour range + breadth
- underlying/futures momentum translated to option entries

B. Mean reversion:
- VWAP deviations
- overnight gap reversal
- volatility expansion/fade
- intraday z-score extremes

C. Option microstructure:
- IV versus realized-volatility gap
- skew/smile dislocations
- OI/price/volume changes
- put-call and dealer/gamma proxies
- near-expiry gamma regimes

D. Defined-risk structures:
- debit spreads
- credit spreads
- iron condor / iron fly
- calendars where data quality supports reliable marking

E. Hybrid/regime-conditioned:
- global overnight move + India open
- India VIX + realized volatility
- FII/DII and futures positioning where timestamps are valid
- trend/volatility/breadth ensemble
- ML ranker/probability model after rule-based baselines

## 6. Phase gates

Phase 1:
Coverage, timestamps, contract identity, expiry/strike/lot-size integrity, duplicates, missingness and liquidity checks pass.

Phase 2:
At least 20 baseline variants and multiple cost settings benchmarked. No baseline promoted on in-sample return alone.

Phase 3:
At least three economically distinct option-structure families survive preliminary OOS tests.

Phase 4:
Candidate clears nested walk-forward OOS tests with no final-test parameter selection.

Phase 5:
Candidate survives adverse slippage, transaction-cost inflation, latency and parameter perturbations.

Phase 6:
Paper/shadow execution over a predefined sample shows no systematic deterioration beyond the execution budget.

Phase 7:
Complete manuscript with methods, provenance, results, uncertainty, limitations and reproducibility.

## 7. Continue/stop logic

The search is now outcome-driven rather than time-boxed. The program continues through new scientifically distinct phases until a candidate clears the Rs 1,000 net per active lot per trading day promotion gate, or until a genuinely material external constraint makes further research impossible. Each family remains bounded and pre-registered; failure terminates that family, not the overall program.

## 8. Final deliverables

Abstract, introduction, research questions, literature review, data, methodology, cost model, candidate strategy definitions, statistical analysis, results, robustness checks, discussion, strengths, limitations, conclusion, future research, references, appendices, source manifest, reproducibility instructions and execution checklist.


## 9. Plan amendment — bounded Phase 3G after Phase 4 falsification

Phase 4 did not validate the intraday ATM short-straddle family. The research plan therefore adds one bounded hypothesis before any robustness/paper phase:

### Phase 3G — Dynamic price-structure break with post-break OI confirmation
- Primary event: a real-time intraday price-structure break, defined without future information.
- Confirmation: change in put-minus-call OI around the break, used only after price has already crossed the structure level; OI is not treated as an advance predictor.
- Trade expression: defined-risk call debit spread for upward breaks or put debit spread for downward breaks.
- Context filters: one compact pre-registered set of realized-volatility and IV/RV conditions; no large optimization grid.
- Execution: next executable minute after confirmation; date-aware lot size; Paytm Money/NSE cost model; 0.20-point base round-trip slippage and stressed-cost rerun.
- Validation: train/validation selection, embargo, untouched test, blocked bootstrap and stability checks. No final-test parameter selection.
- Stop rule: if the fixed pre-registered family has no positive net OOS expectancy after costs or shows unstable performance across test windows, retire it and move directly to the predefined next hypothesis rather than enlarging the grid.

This amendment is the only plan change caused by the Phase 4 result.


## 10. Plan amendment — Phase 3H option lead-lag / derivative price discovery

Phase 3G failed its bounded OOS gate, so the next predefined hypothesis is a distinct information-source test rather than a larger version of the failed break/OI grid.

### Phase 3H — Short-horizon ATM option lead-lag
- Primary question: do short-horizon changes in ATM call/put prices contain incremental information about the next 1–5 minute NIFTY spot move?
- Feature: directional option-pressure proxy = log return of ATM call minus log return of ATM put over a pre-registered 1/3/5-minute lookback.
- Signal barrier: feature uses only timestamps at or before signal time; entry is the next executable minute.
- Trade expression: bullish signal -> defined-risk call debit spread; bearish signal -> defined-risk put debit spread.
- Compact grid: 1/3/5-minute feature lookback, 1%/2%/3% pressure threshold, WEEK/MONTH expiry, 5/10/15-minute maximum hold, 1/2-strike spread width = 108 variants.
- One trade per day per variant. No volume feature is used because source volume remains quarantined.
- Cost model: repository NSE/Paytm Money baseline, date-aware lot size, 0.20 option-premium points per-leg slippage plus a 0.40 stress rerun.
- Primary decision gates: positive net OOS expectancy after costs; at least one test window >= Rs 1,000/lot/day is required for promotion; no family-level promotion if the bounded grid is negative.
- Walk-forward: 180-day train, 60-day validation, 5-day embargo, 60-day untouched test, 60-day step, with the same top-12 train -> best validation selection rule used in Phase 3G.
- Diagnostic requirement: report the option-pressure feature's forward spot-return conditional means/hit rates in addition to trading P&L, so a trading result cannot be mistaken for predictive evidence.
- Stop rule: if the fixed 108-variant family fails after cost and leakage-safe WFA, retire it and move to the next predefined hypothesis; do not enlarge thresholds or add ad hoc features.


## 11. Plan amendment — Phase 3I opening false-break mean reversion

Phase 3H found no tradable option-price lead-lag edge. The next bounded family returns to the underlying price process and tests opening-window false breaks rather than another option-chain microstructure signal.

### Phase 3I — Opening-range false-break reversion
- Build an auditable NIFTY spot series from the same multi-year options dataset.
- Define the opening range from the first 5, 15, or 30 minutes after the 09:15 IST open.
- A downside false break requires spot to trade at least 0.05% or 0.10% below the opening-range low and then re-enter above the low by at least 0.02% or 0.05%.
- An upside false break requires spot to trade at least 0.05% or 0.10% above the opening-range high and then re-enter below the high by at least 0.02% or 0.05%.
- The trade is the opposite direction of the failed break: downside false break -> call debit spread; upside false break -> put debit spread.
- Entry is the next executable minute after re-entry.
- Expiry WEEK/MONTH, spread width 1/2 strikes, maximum hold 15/30/60 minutes.
- One first qualifying false-break signal per day per variant.
- No volume feature is used because source volume remains quarantined.
- 144 pre-registered variants; no post-hoc threshold expansion.
- Base slippage 0.20 premium points per leg and 0.40 stress slippage.
- Same date-aware lot-size, transaction-cost, train/validation/5-day embargo/test WFA and stop/target logic used in the previous bounded families.
- Promotion requires positive net OOS expectancy and at least one untouched test window >= Rs 1,000/lot/day. A negative family is retired without enlargement.

This is intended as the last Phase 3 exploratory family before final synthesis/data-gap assessment unless a completely new independent historical data source becomes available.


## 12. User-directed continuation amendment — Rs 1,000/lot target

The user changed the program stopping rule on 2026-09-24: the study continues until a reproducible strategy reaches the Rs 1,000 net per active lot per trading day target under out-of-sample validation and realistic costs.

### Phase 8 — Hybrid momentum / option-premium confirmation

A public NIFTY tick-replay research system was reviewed as an external hypothesis source. Its published mechanism combines EMA/RSI/VWAP trend features, option-premium confirmation, regime filters and dynamic exits. Its published March-April 2026 sample is short, so it is treated only as a hypothesis source, not as validation.

Paytm Money's historical-data API documentation was also identified as a potential higher-history data path; the documentation states that its historical API provides 1-minute OHLC/volume/OI for NSE cash/F&O from 1 January 2017, including contract-wise NSE options and futures.

Phase 8A pre-registration:
- Trend continuation: EMA structure + RSI + short-horizon underlying momentum + option-premium confirmation.
- Mean reversion: only in weak-trend/volatility-extreme regimes.
- Fixed contract at entry; next executable minute; no moving-ATM path selection.
- Dynamic premium stop/target/trailing variants are frozen before formal test selection.
- Base slippage 0.20 premium points per leg; stress 0.40.
- 48 bounded variants; no post-result expansion.

Promotion:
- preliminary screen: mean active-trade-day net >= Rs 1,000/lot;
- formal promotion: positive OOS expectancy, at least one untouched test window >= Rs 1,000/lot/day, and no materially negative stress failure.

Phase 8B may add an ML probability filter only after the rule-based mechanism shows a credible but unstable edge. Feature model target: next 15-minute NIFTY move >= +0.10% / <= -0.10%, using chronological train/validation/test splits only.

A future authenticated-data adapter will support Paytm Money historical data without storing credentials in the repository.
