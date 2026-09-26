# Research Plan

## 1. Research questions

### Current Equity Income weekly question
Can a source-faithful weekly NSE options strategy reconstructed from the Equity Income YouTube archive produce **at least ₹5,000 net per completed trading week** at a fixed declared reference position size, after realistic Paytm Money/NSE costs and conservative Base/Stress execution assumptions, while trading consistently across weeks and surviving untouched walk-forward/out-of-sample validation?

### Legacy intraday question
The earlier Phase 0–25 program asked whether an intraday strategy could produce at least ₹1,000 net per active lot per trading day. That target remains historical only and is **not** the current promotion criterion for the Equity Income program.

Secondary questions:
1. Which underlying/expiry regime is most amenable to the target?
2. Does the edge arise from directional movement, volatility risk premium, mean reversion, momentum, opening-range behavior, OI/options microstructure, or a combination?
3. Which regime variables materially condition the edge?
4. How much performance disappears after spread, slippage, delay, brokerage and statutory charges?
5. Can the strategy survive parameter, regime and cost perturbations?

## 2. Research hypotheses

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

### Current weekly economic target and consistency gate

For Equity Income strategies, the primary economic unit is a fixed, declared **reference strategy position** because the source may specify four-leg or ratio structures rather than a single option lot.

Promotion target for a frozen strategy on untouched OOS weeks:
- mean weekly net P&L ≥ ₹5,000;
- median weekly net P&L ≥ ₹5,000;
- ≥70% of eligible OOS weeks net-positive;
- ≥80% of eligible OOS weeks executed, unless the source rule itself explicitly defines a no-trade week;
- Base and doubled-slippage Stress both reported;
- no test-period parameter selection;
- weekly worst loss, drawdown, expected shortfall/CVaR, profit factor and concentration reported.

The ₹5,000 threshold is evaluated **after** Paytm Money brokerage, date-aware NSE/statutory charges and the registered slippage model. Hidden scaling, selective week omission and lot-size cherry-picking are prohibited.

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

For the current Equity Income weekly program:

**Phase 26:** Python-only archive completeness and transcript-integrity gate.

**Phase 27–29:** source-rule reconstruction, data readiness, exact-expiry contract coverage and evidence-quality gates. No P&L accepted while material entry/adjustment/exit fields remain unresolved.

**Phase 29.5:** freeze a bounded, source-anchored interpretation matrix; verify date-specific expiry/lot mappings; verify mandatory contract-leg coverage; freeze the execution/cost model. No P&L.

**Phase 30:** run the frozen weekly candidates with Base/Stress friction, then nested WFA and independent later-period OOS. Primary target is ₹5,000 net per completed trading week at the declared reference size.

**Phase 31+:** only after a weekly candidate survives Phase 30 should robustness, paper/shadow execution and final-manuscript promotion be opened. Any new source-faithful family gets its own branch and preregistered grid.

Legacy Phase 1–7 gates below are retained for audit continuity.

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

The Equity Income search is bounded by the phase plan and does not revert to the old ₹1,000/day rule.

A candidate family is retired after repeated OOS/cost/robustness failure. A materially new source-faithful mechanism becomes a new branch with a frozen hypothesis grid. No weekly candidate is promoted from a raw leaderboard alone.

The search terminates when a candidate either:
1. clears the ₹5,000/week economic and consistency gate plus robustness/OOS requirements; or
2. reaches the end of the defined Equity Income phases with a reproducible negative/near-miss result and a documented next research direction.

The program must not tune endlessly toward a weekly target. A research family is retired after repeated OOS/cost/robustness failure. A new branch is created for a materially new hypothesis. The program terminates with either a strategy that clears promotion gates or a reproducible negative/near-miss result plus the highest-value next hypothesis.

## 8. Final deliverables

Abstract, introduction, research questions, literature review, data, methodology, cost model, candidate strategy definitions, statistical analysis, results, robustness checks, discussion, strengths, limitations, conclusion, future research, references, appendices, source manifest, reproducibility instructions and execution checklist.

 
## Phase 31.9 — India VIX × realized volatility × opening-gap direction
 
Phase 31.8 closed with 0/12 promotion passes in both friction regimes. The next bounded family is therefore a distinct regime-conditioned hypothesis: prior-session India VIX relative to prior-only NIFTY RV20, used to condition a simple NIFTY opening-gap FOLLOW/FADE rule.
 
Frozen before computation:
- 3 VIX/RV regimes: LOW ≤0.90, MID (0.90,1.10], HIGH >1.10;
- 2 directions: FOLLOW_GAP and FADE_GAP;
- 2 exits: 10:30 and 15:10;
- 12 true cells and 5 fixed full-panel null permutations per cell;
- entry 09:31, nearest expiry, ATM ±200-point debit spread, historical lot size;
- Base/Stress ₹0.20/₹0.40 slippage plus the existing Paytm Money/NSE/statutory cost model;
- official NSE India VIX data and pinned NIFTY 1-minute parquet cache;
- 20-session prior-only RV warm-up and strict no-lookahead merge barrier.
 
A cell must meet the existing ₹5,000 mean/median weekly and ≥70% positive-week gate in both Base and Stress before WFA/OOS is considered. No post-result regime-threshold tuning is permitted.
 
[Phase 31.9 plan](https://github.com/vishnuvcr/Daily-Options/blob/phase-31.9-vix-rv-gap-opening-direction-v1/docs/phase31_9_plan.md) · [literature review](https://github.com/vishnuvcr/Daily-Options/blob/phase-31.9-vix-rv-gap-opening-direction-v1/docs/phase31_9_literature_review.md) · [branch](https://github.com/vishnuvcr/Daily-Options/tree/phase-31.9-vix-rv-gap-opening-direction-v1)
