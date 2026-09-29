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


## Phase 31.10 — Institutional Positioning × Opening-Gap Translation

This phase is the next distinct branch after the validated negative Phase 31.9 result. It tests prior-session NSE participant-wise F&O index-futures positioning rather than reusing VIX/global signals. The frozen family consists of FII index-futures net-position z-score, DII index-futures net-position z-score, and FII-minus-DII divergence z-score; two absolute thresholds; and two fixed exits. The opening gap is a registered diagnostic/stratification variable, not a post-result selection filter.

Branch: `phase-31.10-institutional-positioning-gap-v1`.
Plan: `docs/phase31_10_plan.md`.
Literature review: `docs/phase31_10_literature_review.md`.
Primary source: official NSE participant-wise F&O OI archive.
Primary target: ₹5,000 net per completed trading week under the existing Base/Stress friction model.


## Phase 32 — Options Skew / Smile Dislocation

A materially distinct option-surface family is preregistered on `phase-32-options-skew-smile-dislocation-v1`. It uses 09:30 NIFTY option-implied skew and smile curvature from the pinned one-minute options cache, prior-only 60-session z-scores, thresholds 1.0/1.5 and fixed exits 10:30/13:30/15:10. The frozen discovery matrix is 12 true cells plus five complete-panel null permutations per cell and Base/Stress friction. Strict next-expiry selection avoids same-day expiry in the surface signal. No WFA/OOS is authorized unless a frozen cell clears the existing mean/median ₹5,000-week and ≥70% positive-week gate in both Base and Stress.

## Phase 32 — Options Skew / Smile Dislocation — CLOSED

Phase 32 completed its preregistered finite experiment on branch `phase-32-options-skew-smile-dislocation-v1`. The data gate and artifact validation passed on authoritative run **36339168867**, but all 12 true cells failed the economic promotion gate in both Base and Stress. No WFA/OOS was authorized and no post-result tuning is permitted.

Result manuscript: `reports/phase32/final_result.md` on the Phase 32 branch.

### Next materially distinct families
The next phase, if authorized, should be a new preregistered family rather than an optimization of Phase 32. Candidate directions are dealer/gamma exposure proxies, multi-expiry volatility-surface structure, or cross-market/global transmission combined with an independently defined options-state variable.

## Phase 33 — Dealer Gamma Exposure

Phase 33 is a new preregistered family testing prior-session NIFTY dealer-gamma proxies: GEX_Z, gamma-flip distance and ATM gamma concentration. Frozen matrix: 12 true cells plus five full-panel null seeds per cell, Base/Stress friction, and no WFA/OOS until the existing ₹5,000 mean/median weekly and 70% positive-week gate clears in both regimes. See the Phase 33 branch plan and literature review.


## Phase 33 — Dealer Gamma Exposure — CLOSED DATA-LIMITED

Authoritative run **36340721257** passed corrected unit/data reconstruction but failed the frozen feature-completeness gate because FLIP_DISTANCE_Z coverage was only **26.54%** after the prior-only warm-up. No P&L was accepted and no post-result feature redesign is permitted.

## Phase 34 — Multi-Expiry Volatility Term Structure — next planned family

The next bounded family will use prior-session NIFTY option-implied volatility across two fixed expiries. The hypothesis is that unusually steep/inverted front-versus-back IV term structure may predict short-horizon mean reversion of a defined-risk calendar structure. A finite preregistered grid, Base/Stress friction, null controls, strict prior-information timing, and the same ₹5,000/week economic gate are mandatory before testing.


## Phase 39 — NIFTY Option-Implied vs Realized Opening-Move Dislocation

Phase 39 is the next distinct source-faithful family after the closures of Phases 34–38. It tests whether the size of the first 15-minute NIFTY move relative to the contemporaneous option-implied 15-minute move contains short-horizon directional information.

### Frozen research question
Does a NIFTY opening move that is unusually large or unusually small relative to the 09:30 ATM option-implied 15-minute move predict continuation or reversal strongly enough to generate at least ₹5,000 net per completed trading week after realistic costs?

### Frozen signal construction
- Session opening reference: NIFTY 09:15 bar open.
- Realized opening return: (NIFTY close at 09:29 − 09:15 open) / 09:15 open.
- ATM reference: nearest ₹50 strike to NIFTY 09:30 close.
- Implied-volatility source: nearest NIFTY expiry strictly after the trade date; 09:30 CE/PE close-derived IV; average CE/PE IV.
- Implied 15-minute move: spot × ATM IV × sqrt(15/390).
- Realized-to-implied ratio: absolute realized opening return divided by implied 15-minute move percentage.
- Standardization: strictly prior 60 completed sessions of the raw ratio.
- State HIGH_DISLOCATION if z >= +0.75; LOW_DISLOCATION if z <= −0.75; otherwise no trade.
- Direction: sign of the same-session 09:15→09:29 return.

### Frozen execution
- CONTINUE: option side follows opening direction.
- FADE: option side is opposite opening direction.
- One-lot 200-point debit spread.
- Entry 09:31 IST using option open.
- Exits 10:30 and 15:10 IST using option close.
- Historical NIFTY lot sizes.
- Existing Paytm Money/NSE/statutory cost model.
- Base/Stress slippage ₹0.20/₹0.40 per option-price unit/order.

### Frozen discovery matrix
2 states × 2 mappings × 2 exits = 8 true cells, plus five fixed full-panel permutation null seeds. A true cell must meet mean weekly net ≥₹5,000, median weekly net ≥₹5,000 and positive-week rate ≥70% in both Base and Stress, with ≥95% execution coverage and clean accounting, before WFA/OOS.

### Stop rule
No post-result adjustment of the 60-session lookback, ±0.75 thresholds, 09:15–09:29 interval, IV horizon scaling, expiry rule, direction mapping, spread width, exits, or cost model.
## Phase 40 — Prior-Day ATM IV / RV State × Overnight-Gap Implied-Move Dislocation

### Frozen research question
Does the next NIFTY session's overnight opening gap become directionally informative when its magnitude is unusually large or small relative to the prior session's ATM option-implied one-session move, conditioned on the prior-day implied-volatility versus realized-volatility state?

### Information timing
- Signal date t is known by 09:15 on date t.
- Prior-day option signal uses the previous completed NIFTY session's 15:10 close and its nearest NIFTY expiry strictly after that prior session date.
- ATM strike is nearest ₹50 to prior-session 15:10 NIFTY close using deterministic half-up rounding.
- ATM IV is the simple average of valid CE and PE IV from the prior session's 15:10 option closes.
- Prior realized volatility is annualized close-to-close standard deviation of the previous 20 completed NIFTY returns ending on the prior session.
- Overnight gap = current 09:15 NIFTY open divided by prior session 15:10 NIFTY close minus one.
- One-session implied move = prior ATM IV × sqrt(1/252).
- GAP_RATIO = absolute overnight gap / one-session implied move.
- GAP_RATIO_Z uses only the previous 60 completed signal-day GAP_RATIO observations.

### Frozen states and execution
- HIGH_GAP_DISLOCATION if GAP_RATIO_Z >= +0.75.
- LOW_GAP_DISLOCATION if GAP_RATIO_Z <= −0.75.
- Zero-gap direction is NO_TRADE.
- CONTINUE follows the overnight gap direction.
- FADE takes the opposite direction.
- 09:31 option-open entry; 10:30 and 15:10 option-close exits.
- One-lot 200-point debit spread, historical lot sizes.

### Discovery matrix
2 states × 2 mappings × 2 exits = 8 true cells, plus five fixed permutation-null seeds. Promotion requires in both Base and Stress: mean weekly net ≥₹5,000, median weekly net ≥₹5,000, positive-week rate ≥70%, ≥95% execution coverage and clean accounting.

### Data gates
- ≥95% post-warm-up feature eligibility;
- ≥95% prior-day ATM IV input coverage;
- ≥95% overnight-gap data coverage;
- zero prior-information violations;
- deterministic expiry/strike/lot mapping;
- ≥95% execution quote coverage for every true cell;
- accounting reconciliation.

### Stop rule
No post-result adjustment of RV window, 60-session z window, ±0.75 thresholds, IV/RV construction, one-session scaling, expiry rule, gap direction mapping, spread width, entry, exit or cost model.

## Phase 41 — NIFTY Option-Gamma Concentration × Opening-Gap Direction

### Frozen research question
Does prior-session OI-weighted option-gamma concentration around the NIFTY ATM strike condition whether the next session's opening gap continues or reverses strongly enough to generate at least ₹5,000 net per completed trading week after realistic costs?

### Frozen construction
- Prior signal session: previous completed NIFTY session's 15:10 close.
- Reference spot: prior-session 15:10 NIFTY close.
- Reference strike: deterministic nearest ₹50 ATM, half-up rounding.
- Reference expiry: nearest NIFTY expiry strictly after the prior signal date.
- Chain window: strikes within ±₹500 of ATM.
- Core window: strikes within ±₹100 of ATM.
- For each CE/PE strike, use the latest valid positive option close at or before 15:10, the option OI at that observation, and Black-Scholes implied volatility solved from that price.
- Gamma per option is the standard European gamma using the prior spot, strike, IV and time to expiry.
- Gamma mass at a strike = OI × gamma × historical lot size.
- GAMMA_CONCENTRATION = gamma mass in the ±₹100 core window / gamma mass in the ±₹500 chain window.
- Standardization uses the strictly prior 60 valid GAMMA_CONCENTRATION observations; missing observations are not imputed or forward-filled.
- HIGH_GAMMA_CONCENTRATION if z ≥ +0.75; LOW_GAMMA_CONCENTRATION if z ≤ −0.75; otherwise no trade.

### Frozen execution signal
- Current-session opening gap = 09:15 NIFTY open / prior-session 15:10 close − 1.
- Zero gap = no trade.
- FOLLOW_GAP: follow the opening-gap direction.
- FADE_GAP: take the opposite direction.
- Entry 09:31 option open; exits 10:30 and 15:10 option close.
- One-lot 200-point ATM directional debit spread.
- Nearest expiry on/after the current trading date.
- Historical NIFTY lot sizes.

### Frozen matrix and controls
2 gamma states × 2 gap mappings × 2 exits = 8 true cells plus five fixed permutation-null seeds 101, 202, 303, 404, 505.
Nulls permute only the prior-only gamma-concentration z values across feature-eligible dates; same-day gap direction and all execution prices remain unchanged.

### Data gates
- ≥95% post-warm-up feature eligibility;
- ≥95% prior-session gamma-chain coverage;
- ≥95% core/total gamma observation completeness;
- zero prior-information violations;
- deterministic expiry, strike and lot mapping;
- ≥95% execution quote coverage in every true cell;
- accounting reconciliation.

### Promotion gate
In both Base and Stress: mean weekly net ≥₹5,000, median weekly net ≥₹5,000, positive-week rate ≥70%, execution coverage ≥95%, and clean accounting. No WFA/OOS otherwise.

### Stop rule
No post-result changes to the ATM/chain widths, 60-valid-observation lookback, ±0.75 z thresholds, expiry rule, gap mapping, entry, exits, spread width, IV construction, cost model or lot sizing.


## Phase 43 — NIFTY Weekday × Opening-Gap Direction

### Research question
Does the trading weekday condition whether the current NIFTY opening gap continues or reverses strongly enough to generate at least ₹5,000 net per completed trading week after realistic costs?

### Literature basis
Recent NIFTY research finds that day-of-week effects are time-varying rather than stable across all periods, supporting a bounded preregistered test rather than post-hoc weekday selection. Dhankhar et al. (2025) study Nifty 50 day-of-week effects using rolling windows and GARCH/EGARCH methods; Sahoo (2021) also documents that weekday effects changed between pre-COVID and COVID periods. These studies motivate testing the weekday interaction without assuming a particular weekday is profitable.

### Frozen feature and execution
- State is the trading weekday: Monday, Tuesday, Wednesday, Thursday, Friday.
- Current opening gap = 09:15 NIFTY open / prior completed 15:10 close − 1; zero gap = no trade.
- FOLLOW_GAP and FADE_GAP are both tested for every weekday.
- Entry 09:31 option open; exits 10:30 and 15:10 option close.
- One-lot 200-point ATM directional debit spread; nearest NIFTY expiry on/after trade date; historical lot sizes.
- Existing Paytm Money/NSE/statutory transaction-cost model; Base/Stress slippage ₹0.20/₹0.40 per option-price unit/order.

### Discovery matrix and controls
5 weekdays × 2 gap mappings × 2 exits = 20 true cells. Five fixed full-panel permutation null seeds 101,202,303,404,505 permute weekday labels across eligible dates while leaving same-day gap and execution data unchanged.

### Data gates
- ≥95% session eligibility and opening-gap coverage;
- deterministic expiry, ATM strike and lot mapping;
- zero prior-information violations;
- ≥95% execution quote coverage in every true cell;
- accounting reconciliation.

### Promotion gate
In both Base and Stress, a promoted cell must have mean weekly net ≥₹5,000, median weekly net ≥₹5,000, positive-week rate ≥70%, execution coverage ≥95% and clean accounting. No WFA/OOS unless at least one frozen true cell clears all promotion criteria in both Base and Stress; if none does, the phase closes negative.

### Stop rule
No post-result weekday selection, threshold tuning, execution-time substitution, strike/expiry substitution, cost-model changes or gap-mapping changes.


## Phase 44 — NIFTY Opening-Gap Magnitude × Gap Direction

Frozen states: SMALL_GAP (<0.50%), MEDIUM_GAP (0.50%–<1.00%), LARGE_GAP (≥1.00%). Test FOLLOW_GAP and FADE_GAP at 10:30 and 15:10 using the validated one-lot 200-point debit-spread execution engine, historical lots, existing Paytm Money/NSE/statutory costs and Base/Stress slippage. Twelve true cells plus five fixed label-permutation nulls per cell. Promotion requires mean and median weekly net ≥₹5,000 and positive-week rate ≥70% in both Base and Stress, with ≥95% execution coverage and clean accounting. No threshold changes after results.


## Phase 45 — NIFTY Opening-Gap Failure/Continuation Confirmation

Research question: does a meaningful opening gap that fails or continues during the first 15 minutes contain a stronger directional signal than the raw gap alone? Frozen minimum gap magnitude is 0.50%. GAP_FAILURE means the first 15-minute return is opposite the gap direction; GAP_CONTINUATION means it is in the same direction; NO_CONFIRMATION is otherwise. Test all three states × FOLLOW/FADE × 10:30/15:10 (12 true cells) with five fixed state-label permutation nulls, historical lots, existing Paytm Money/NSE/statutory costs and Base/Stress slippage. Promotion requires mean and median weekly net ≥₹5,000, positive-week rate ≥70%, ≥95% execution coverage and clean accounting in both Base and Stress. No post-result state selection or threshold changes.


## Phase 47 — Opening-Gap Magnitude Normalized by Prior-Day Range × Gap Direction

### Research question
Does the NIFTY opening gap, measured relative to the immediately preceding session's high-low range, condition continuation versus reversal strongly enough to produce at least ₹5,000 net per completed trading week after realistic costs?

### Frozen states
- SMALL_REL_GAP: absolute gap / prior-day range < 0.20
- MEDIUM_REL_GAP: 0.20–<0.40
- LARGE_REL_GAP: >=0.40

### Frozen execution
FOLLOW_GAP and FADE_GAP; 09:31 entry; 10:30 and 15:10 exits; one-lot 200-point ATM debit spread; nearest expiry on/after trade date; historical lots; existing Paytm Money/NSE/statutory friction; Base/Stress ₹0.20/₹0.40 slippage.

### Controls and gates
12 true cells plus five fixed state-permutation null seeds. Require >=95% feature and execution coverage, zero prior-information violations and clean accounting. Promotion requires mean weekly net >=₹5,000, median weekly net >=₹5,000 and >=70% positive weeks in both Base and Stress.

### External rationale
Range-normalized gap sizing is supported as a volatility-normalization idea in prior gap research, while recent NIFTY analyses also distinguish gap behavior by magnitude. These sources motivate the hypothesis only; no external profitability result is imported.

### Phase boundary
No post-result threshold, state, exit or mapping tuning is permitted. Phase 47 is now closed negative after authoritative run 36538234322.


## Phase 48 — Prior-Session Return Direction × Opening-Gap Direction

Frozen interaction: PRIOR_UP/PRIOR_DOWN from the immediately preceding 15:10-to-15:10 NIFTY return, crossed with current opening-gap direction. Test CONTINUE/FADE at 10:30/15:10 using the one-lot 200-point ATM debit spread, historical lots, exact expiry mapping and existing Base/Stress friction. Eight true cells plus five state-permutation nulls per cell. Phase 48 closed negative: authoritative run 36538835468, all 8 true cells negative under both frictions. No threshold or mapping retuning and no WFA/OOS.


## Phase 49 — Prior-Session Range Regime × Opening-Gap Direction

Frozen regime: prior-session NIFTY range percentage classified LOW/MID/HIGH by 33.333rd and 66.667th empirical percentiles of the last 60 valid completed range observations strictly before the prior session. Cross with opening-gap FOLLOW/FADE at 10:30/15:10. Twelve true cells plus five permutation nulls. Phase 49 closed negative: authoritative run 36539451804; best cell ₹88/week Base and ₹9/week Stress with negative medians; no WFA/OOS.


## Phase 50 — Opening Location Relative to Prior Range × Gap Direction

Frozen states: INSIDE_RANGE, ABOVE_RANGE, BELOW_RANGE based on the current 09:15 open relative to the previous completed 15:10 high-low range. Cross with FOLLOW_GAP/FADE_GAP at 10:30 and 15:10 using the validated one-lot 200-point ATM debit spread, historical lots, exact expiry mapping and existing Base/Stress friction. Twelve true cells plus five state-permutation nulls. Phase 50 closed negative: authoritative run 36539948879; best cell INSIDE_RANGE/FADE/15:10 yielded ₹163/week Base and ₹116 Stress, but median and positive-week gates failed. No WFA/OOS.


## Phase 51 — Prior-Session ATM IV Level Regime × Opening-Gap Direction

Frozen feature: prior-session 15:10 ATM CE/PE implied-volatility average from the nearest expiry strictly after the prior session date; classify LOW/MID/HIGH by the last 60 valid prior-session ATM-IV observations. Cross with opening-gap FOLLOW/FADE at 10:30/15:10. Twelve true cells plus five permutation nulls. Phase 51 closed DATA-LIMITED because valid ATM-IV coverage was 94.01% and final feature eligibility 93.58%, below the 95% gate. No Base/Stress P&L, WFA or OOS accepted; no coverage relaxation authorized.


## Phase 52 — Same-Session 09:30 ATM IV Level Regime × Opening Direction

Frozen feature: same-session 09:30 ATM CE/PE IV average from the nearest expiry strictly after the current trading date, with LOW/MID/HIGH empirical terciles from the last 60 valid prior observations. Cross with opening-direction FOLLOW/FADE at 10:30/15:10. Twelve cells plus five permutation nulls. Phase 52 closed negative in authoritative workflow 36548301179; all 12 cells were negative under Base and Stress. Best cell MID_IV/FADE/15:10 was -₹100.61/week Base and -₹182.60 Stress. No WFA/OOS.


## Phase 52 — Same-Session 09:30 ATM IV Level Regime × Opening Direction

Frozen feature: 09:30 ATM CE/PE IV average using the nearest strict-next expiry, with LOW/MID/HIGH terciles from the preceding 60 valid same-session observations. Cross with FOLLOW/FADE opening direction at 10:30/15:10. Twelve cells plus five permutation nulls. Phase 52 closed negative after authoritative run 36548301179: all 12 cells negative under Base and Stress; best MID_IV/FADE/15:10 was -₹100.61/week Base and -₹182.60 Stress. No WFA/OOS or result-driven tuning.


## Phase 52 — Same-Session 09:30 ATM IV Level Regime × Opening Direction

Frozen feature: same-session 09:30 ATM CE/PE IV average for the nearest expiry strictly after the current date, classified LOW/MID/HIGH using the prior 60 valid same-session observations. Cross with opening-direction FOLLOW/FADE at 10:30 and 15:10 using the validated one-lot 200-point ATM debit spread, historical lots, Paytm Money/NSE/statutory friction and Base/Stress slippage. Twelve true cells plus five state-permutation nulls. Phase 52 closed negative: authoritative run 36548301179; best MID_IV/FADE/15:10 was -₹100.61/week Base and -₹182.60 Stress; no WFA/OOS.


## Phase 53 — Same-Session 09:30 ATM-Adjacent IV Skew × Opening Direction

Frozen feature: 09:30 OTM put IV at ATM−₹50 minus 09:30 OTM call IV at ATM+₹50, nearest strict-next expiry, with LOW/MID/HIGH terciles from the preceding 60 valid same-session observations. Cross with FOLLOW/FADE at 10:30/15:10. Twelve cells plus five permutation nulls. Phase 53 closed negative after authoritative run 36548934744: all 12 cells negative under Base and Stress; best LOW_SKEW/FADE/10:30 was -₹198/week Base and -₹293 Stress. No WFA/OOS.


## Phase 53 — Same-Session 09:30 Near-ATM IV Skew × Opening Direction — CLOSED

Frozen skew = 09:30 IV of ATM-50 put minus ATM+50 call, classified LOW/MID/HIGH from the previous 60 valid same-session observations. Cross with opening-gap FOLLOW/FADE at 10:30/15:10. Phase 53 authoritative run 36549121608 passed all data and accounting gates but all 12 cells failed the ₹5,000 mean/median weekly and 70% positive-week gate in both Base and Stress. No WFA/OOS and no retuning.

## Phase 54 — Same-Session 09:30 Front-vs-Next-Expiry ATM IV Term Structure × Opening Direction

### Frozen research question
Does the current-session 09:30 ATM IV slope between the nearest expiry on/after the trade date and the next later listed NIFTY expiry condition opening-gap continuation/reversal strongly enough to generate at least ₹5,000 net per completed trading week after realistic costs?

### Frozen feature
- 09:30 NIFTY spot and nearest ₹50 ATM strike.
- Front expiry = nearest listed NIFTY expiry on/after the trade date.
- Back expiry = next listed NIFTY expiry strictly after the front expiry.
- ATM IV for each expiry from 09:30 ATM CE/PE closes, averaged across valid call/put IV.
- TERM_SLOPE = back IV - front IV in volatility percentage points.
- STEEP_TERM when TERM_SLOPE >= 0; INVERTED_TERM when TERM_SLOPE < 0.
- Zero opening gap = no trade.
- All state information is known by 09:30; entry is 09:31.

### Frozen execution
FOLLOW/FADE opening gap; 09:31 option-open entry; 10:30 and 15:10 exits; one-lot 200-point ATM debit spread; nearest expiry on/after current trade date; historical lots; Paytm Money/NSE/statutory charges; Base/Stress ₹0.20/₹0.40 slippage.

### Controls/gates
2 term states × 2 mappings × 2 exits = 8 true cells; five state-permutation nulls. Require >=95% feature and execution coverage, zero information violations and clean accounting. Promotion requires mean weekly net >=₹5,000, median >=₹5,000 and >=70% positive weeks in both Base and Stress. No WFA/OOS otherwise.

### Stop rule
No sign-boundary, expiry selection, IV construction, exit, gap mapping, spread width, lookback or cost retuning after results.


## Phase 53 — Same-Session 09:30 Near-ATM IV Skew × Opening Direction

Frozen feature: 09:30 OTM-put IV at ATM-₹100 minus OTM-call IV at ATM+₹100 for the nearest expiry strictly after the current date, classified LOW/MID/HIGH using the prior 60 valid same-session skew observations. Cross with FOLLOW/FADE at 10:30/15:10. Twelve true cells plus five permutation nulls. Phase 53 closed negative: authoritative run 36548991737; best MID_SKEW/FADE/15:10 was -₹177.32/week Base and -₹252.72 Stress; no WFA/OOS.


## Phase 54 — Same-Session 09:30 Matched ATM IV Call-Put Spread × Opening Direction — CLOSED

Matched same-strike ATM IV spread (PE IV minus CE IV) at 09:30, crossed with opening-gap FOLLOW/FADE and 10:30/15:10 exits. Authoritative run 36549550020 passed all integrity gates but all 12 cells failed the dual-friction economic promotion gate. Best cell LOW_SPREAD/FADE/15:10 was -₹49/week Base and -₹143 Stress. No WFA/OOS and no retuning.

## Phase 55 — Same-Session 09:30 Front-vs-Next-Expiry ATM IV Term Structure × Opening Direction

### Frozen research question
Does the current-session 09:30 ATM IV term slope between the nearest and next later NIFTY expiries condition opening-gap continuation/reversal strongly enough to produce at least ₹5,000 net per completed trading week after realistic costs?

### Frozen feature
- Reference spot: 09:30 NIFTY close; ATM = nearest ₹50.
- Front expiry: nearest NIFTY expiry on or after the trade date.
- Back expiry: next listed NIFTY expiry strictly after the front expiry.
- At 09:30, invert ATM CE/PE IV for both expiries using the common spot/strike.
- ATM IV for each expiry = mean of valid CE and PE IV.
- TERM_SLOPE = BACK_IV − FRONT_IV in volatility percentage points.
- STEEP_TERM when TERM_SLOPE >= 0; INVERTED_TERM when TERM_SLOPE < 0.
- State is known by 09:30; entry is 09:31.
- Zero opening gap = no trade.

### Frozen execution
FOLLOW_OPEN / FADE_OPEN; 09:31 entry; 10:30 and 15:10 exits; one-lot 200-point ATM debit spread; execution expiry nearest on/after date; historical lots; existing Paytm Money/NSE/statutory costs; Base/Stress ₹0.20/₹0.40 slippage.

### Controls/gates
2 term states × 2 mappings × 2 exits = 8 true cells; five state-permutation nulls. Require ≥95% feature and execution coverage, 0 prior-information violations, and clean accounting. Promotion requires mean and median weekly net ≥₹5,000 and ≥70% positive weeks in both Base and Stress. No WFA/OOS otherwise.

### Stop rule
No post-result change to expiry pair definition, sign boundary, IV inversion, execution expiry, entry/exit, gap mapping, spread width, or cost model.


## Phase 54 — Same-Session 09:30 Matched-ATM IV Call-Put Spread × Opening Direction

Frozen feature: same-strike 09:30 ATM CE IV minus ATM PE IV at the nearest strict-next expiry; terciles from the preceding 60 valid same-session observations. Cross with FOLLOW/FADE and 10:30/15:10 one-lot 200-point ATM debit-spread execution. Twelve true cells plus five permutation nulls. Phase 54 closed negative after authoritative run 36549550020: all 12 cells negative under Base and Stress; best LOW_SPREAD/FADE/15:10 was -₹49/week Base and -₹143 Stress. No WFA/OOS or tuning.


## Phase 54 — Same-Session 09:30 ATM Put–Call IV Spread × Opening Direction

Frozen feature: 09:30 ATM PE IV minus ATM CE IV for the nearest expiry strictly after the current date, classified LOW/MID/HIGH with the prior 60 valid same-session observations. Cross with FOLLOW/FADE at 10:30/15:10. Twelve true cells plus five permutation nulls. Phase 54 closed negative: authoritative run 36549663605; best HIGH_SPREAD/FADE/15:10 had -₹49.18/week Base and -₹142.70 Stress, despite positive gross P&L; no WFA/OOS.


## Phase 55 — Same-Session Front-vs-Next-Expiry ATM IV Term Structure × Opening Direction — CLOSED DATA-LIMITED

Frozen term state = BACK_ATM_IV − FRONT_ATM_IV, with front expiry nearest on/after date and back expiry the next listed expiry. Current-session 09:30 CE/PE observations were required for both maturities. Gate run 36550269685 found only 72.77% complete post-warm-up coverage versus the frozen 95% threshold, so no P&L was accepted and no coverage relaxation is authorized.

## Phase 56 — Prior-Session Candle Conviction Regime × Opening-Gap Direction

### Frozen research question
Does the directional conviction of the immediately preceding NIFTY session, measured by its candle body relative to its high-low range, condition whether the next session's opening gap continues or reverses strongly enough to produce at least ₹5,000 net per completed trading week after realistic costs?

### Frozen feature
- Prior session body ratio = abs(prior 15:10 close − prior 09:15 open) / (prior high − prior low).
- Prior session body direction = sign(prior 15:10 close − prior 09:15 open).
- Conviction ratio is classified by a strictly prior 60-session empirical distribution into LOW/MID/HIGH terciles.
- Current opening direction = sign(current 09:15 open / prior 15:10 close − 1); zero gap = no trade.
- The state uses no option quotes, so the feature gate must rely on price-data completeness and the established 09:15/15:10 index timestamp barrier.

### Frozen execution
FOLLOW_OPEN / FADE_OPEN; 09:31 option-open entry; 10:30/15:10 exits; one-lot 200-point ATM debit spread; nearest expiry on/after date; historical lots; existing Paytm Money/NSE/statutory charges; Base/Stress ₹0.20/₹0.40 slippage.

### Discovery matrix and controls
3 conviction states × 2 mappings × 2 exits = 12 true cells; five state-permutation nulls. Promotion requires mean/median weekly net ≥₹5,000, ≥70% positive weeks, ≥95% execution coverage and clean accounting in both Base and Stress. No WFA/OOS otherwise.

### Stop rule
No post-result body-ratio threshold, state boundary, mapping, exit, expiry, spread width or cost retuning.
