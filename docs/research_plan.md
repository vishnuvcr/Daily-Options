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

The search is open-ended within the scientific phases but not unbounded. A research family is retired after repeated OOS/cost/robustness failure. A new branch is created for a materially new hypothesis. The program terminates with either a strategy that clears promotion gates or a reproducible negative/near-miss result plus the highest-value next hypothesis.

## 8. Final deliverables

Abstract, introduction, research questions, literature review, data, methodology, cost model, candidate strategy definitions, statistical analysis, results, robustness checks, discussion, strengths, limitations, conclusion, future research, references, appendices, source manifest, reproducibility instructions and execution checklist.


## Phase 20 preregistration — global-gated late-day volatility acceleration

The frozen Phase 13 384-cell late-day volatility-acceleration mechanism is tested only on sessions passing a fixed inherited regime gate: absolute GLOBAL3 standardized prior-session return >= 0.5 and absolute NIFTY opening gap >= 0.75%. No Phase 13 signal/entry/expiry/hold/risk/cost parameter is changed. The corrected simulator emits one outcome per input `risk_id`. Base/stress slippage remain ₹0.20/₹0.40 per premium point per leg.
