# Phase 32 — Options Skew / Smile Dislocation
## Final Research Manuscript

**Status:** Closed — negative discovery result; no trading strategy promoted  
**Authoritative workflow run:** 36339168867  
**Branch:** `phase-32-options-skew-smile-dislocation-v1`  
**Study window:** 2021-07-01 through 2026-08-31  
**Dataset revision:** `thetrademarkk/india-index-options-1m@51ca58c`

---

## Abstract

This phase tested whether short-horizon information in the NIFTY implied-volatility surface could support a cost-aware, defined-risk strategy capable of meeting the project's target of ₹5,000 net per week. Two frozen surface features were evaluated: downside-versus-upside implied-volatility skew and near-ATM smile curvature. Each was standardized using a prior-only 60-session z-score. The preregistered discovery grid contained two thresholds (|z| ≥ 1.0 and |z| ≥ 1.5) and three exits (10:30, 13:30 and 15:10 IST), producing 12 true cells. Each cell was evaluated under Base and Stress friction and against five full-panel null permutations.

The data gate passed. There were 1,225 NIFTY 09:30 sessions, 100% strict-next-expiry coverage, 1,143/1,165 warm-up-complete sessions with a valid four-quote IV surface (98.11%), and zero prior-look-ahead violations. Execution coverage across the 12 cells ranged from 96.74% to 100.00%.

The economic result was uniformly negative. All 12 Base cells and all 12 Stress cells had negative mean and median weekly net P&L. The least-negative Base mean weekly result was ₹-408.84 (SKEW_Z, |z|≥1.5, 10:30), and the corresponding Stress result was ₹-521.02. The highest positive-week share was only 16.42% in Base and 11.94% in Stress, far below the 70% promotion requirement. Zero of 12 Base cells and zero of 12 Stress cells passed the promotion gate. In both friction regimes, every true cell had a lower mean weekly result than its five-seed null-control mean.

Therefore Phase 32 is closed without WFA/OOS promotion. The result is evidence against this particular, preregistered NIFTY option-surface mean-reversion family under the tested execution and cost assumptions; it is not evidence that all option-surface information is useless.

---

## 1. Research question

Can a fixed, prior-only measure of NIFTY option-implied volatility skew or smile curvature, observed at 09:30 IST and converted into a bounded-risk four-leg structure executed from 09:31 IST, generate at least ₹5,000 of net weekly P&L after realistic Indian option-trading frictions?

### Primary hypothesis

Extreme relative richness/cheapness in local option-surface shape should mean-revert sufficiently quickly for a deterministic four-leg structure to capture the dislocation.

### Null hypothesis

Surface-state signals do not provide economically useful predictive content beyond what would arise from randomized feature timing, once the same execution and cost model is applied.

---

## 2. Aims and objectives

### Aim

Test whether local NIFTY implied-volatility surface shape contains monetizable short-horizon information that survived the earlier ORB, OI/volume, IV-RV, VIX/gap and institutional-positioning research families.

### Objectives

1. Reconstruct 09:30 NIFTY local volatility-surface features from executable option prices.
2. Prevent forward leakage by using only a prior 60-session standardization window.
3. Use a strictly next-expiry contract to avoid same-day expiry singularity.
4. Test a finite, preregistered 12-cell strategy grid.
5. Evaluate Base and Stress friction with historical lot sizes and the audited Paytm Money/NSE cost model.
6. Compare true cells with five full-panel null permutations.
7. Stop after the frozen experiment without post-result threshold, strike, exit or structure tuning.

---

## 3. Background and literature review

Equity-index option markets encode market-implied information in the cross-section of strikes and maturities. Exchange option chains expose strike, option type, volume, open interest and implied-volatility information, while India VIX is itself derived from NIFTY options. The local skew/smile construction used here therefore targets a directly observable option-surface state rather than a proxy built only from underlying returns.

Published research provides reasons to test, but also reasons for caution. Work on option-implied skewness has documented relations with index-option pricing and hedged option returns, while showing that moneyness, market state, holding period and trading costs matter. Research on volatility-surface construction shows that surface estimators can materially change option-implied measures. More recent work also emphasizes that apparent option-information predictability can be confounded by other market frictions. These findings support a finite, cost-aware test with a frozen surface definition rather than adaptive model selection.

The project's preceding IV-RV family was kept separate. Phase 32 specifically tested whether the *shape* of the option surface contained information not represented by a simple level-minus-realized-volatility variable.

Primary literature and source references are preserved in:
- `docs/phase32_literature_review.md`
- NSE option-chain and derivatives references
- Hugging Face pinned dataset documentation
- Jha & Kalimipalli (2010)
- Kim & Park (2018)
- 2021 option-implied-skewness/hedged-return research
- Ulrich & Walther (2020)
- 2025 JFE research on implied-volatility information

---

## 4. Data and sample construction

### Pinned numerical source

- Dataset: `thetrademarkk/india-index-options-1m`
- Revision: `51ca58c`
- Index cache: `index/NIFTY.parquet`
- Options cache: `options/NIFTY/*.parquet`

The run used the project's persistent cache rather than downloading the dataset afresh after cache restoration.

### Session construction

The underlying NIFTY close at 09:30 IST determined the nearest ₹50 ATM strike. For each trade date, the next available NIFTY expiry strictly after the trade date was selected.

### Surface observations

At 09:30 IST the surface required:

- ATM CE
- ATM PE
- ATM-100 PE
- ATM+100 CE

Option closes were inverted to Black-Scholes implied volatility using the project's fixed q=0 and r=0 convention. No alternative surface model, interpolation family or calibration was selected after observing results.

### Data-gate diagnostics

- Raw NIFTY 09:30 sessions: **1,225**
- Warm-up-complete sessions: **1,165**
- Strict-next-expiry coverage: **100.00%**
- Valid four-quote IV surface coverage after warm-up: **98.11% (1,143/1,165)**
- Prior-surface barrier violations: **0**
- Feature-eligible sessions after prior-only 60-session standardization: **691**
- Quote rows read for the required local surface/execution panel: **189,016**
- Unique normalized quote keys: **138,282**
- Duplicate quote rows across the raw panel: **50,734**

The 22 warm-up surface failures were attributable to 15 missing/non-positive ATM CE observations, 3 failed ATM PE IV inversions, 3 missing/non-positive ATM PE observations and 1 failed ATM CE IV inversion.

The feature-eligible count is lower than the valid-surface count because the preregistered rolling z-score requires 60 prior observations without filling or backfilling missing feature values.

---

## 5. Preregistered signal definitions

### 5.1 Skew

`SKEW_VOLPTS = IV(ATM-100 PE) - IV(ATM+100 CE)`

The feature was standardized using the previous 60 completed raw-feature observations only.

### 5.2 Smile curvature

`SMILE_VOLPTS = 0.5×[IV(ATM-100 PE)+IV(ATM+100 CE)] - 0.5×[IV(ATM CE)+IV(ATM PE)]`

Again, the z-score used only prior observations.

### 5.3 Trading structures

For positive skew z-score:

- Buy CE ATM+50
- Sell CE ATM+100
- Sell PE ATM-100
- Buy PE ATM-50

For negative skew z-score the leg directions were reversed.

For positive smile z-score:

- Sell PE ATM-50
- Buy PE ATM-100
- Sell CE ATM+50
- Buy CE ATM+100

For negative smile z-score the leg directions were reversed.

Each signal was one NIFTY lot with no discretionary adjustment, stop, target, roll or leverage change.

### 5.4 Frozen grid

- Features: SKEW_Z, SMILE_Z
- Thresholds: |z|≥1.0, |z|≥1.5
- Exits: 10:30, 13:30, 15:10 IST
- True cells: **12**
- Null seeds: **101, 202, 303, 404, 505**

Entry was at the 09:31 option open. Exit was at the declared exit timestamp close.

---

## 6. Cost and friction methodology

The experiment retained the project's date-aware NIFTY lot-size schedule and Paytm Money/NSE/statutory charge model. Net P&L was computed as:

**net P&L = execution gross P&L − slippage − transaction/statutory costs**

Base slippage was ₹0.20 per option-price unit per order. Stress slippage was ₹0.40. The same order-count, exchange, SEBI, STT, stamp-duty, GST and brokerage conventions were applied throughout.

The execution-price key was normalized by **date, expiry, local time, option type and strike**, matching the validated Phase 31.7 execution architecture.

---

## 7. Statistical analysis

For each true and null cell the study recorded:

- trade count
- active weeks
- total net P&L
- mean weekly net P&L
- median weekly net P&L
- positive-week rate
- worst trade
- worst week
- maximum drawdown
- raw gross P&L
- slippage cost
- transaction/statutory costs

Weekly net P&L was the resampling unit for a 1,000-draw bootstrap interval of mean weekly net P&L. The bootstrap is descriptive and was not used for post-result tuning.

---

## 8. Coverage and primary results

All 12 cells met the preregistered 95% execution-coverage floor.

| Feature | |z| | Exit | Base mean/wk | Base median/wk | Base positive weeks | Stress mean/wk | Stress median/wk | Stress positive weeks | Coverage |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| SKEW_Z | 1.0 | 10_30 IST | ₹-554.38 | ₹-460.50 | 0.95% | ₹-705.08 | ₹-577.74 | 0.00% | 97.86% |
| SKEW_Z | 1.0 | 13_30 IST | ₹-550.47 | ₹-505.83 | 3.81% | ₹-702.17 | ₹-631.63 | 2.86% | 98.40% |
| SKEW_Z | 1.0 | 15_10 IST | ₹-523.42 | ₹-502.23 | 9.52% | ₹-675.87 | ₹-644.04 | 5.71% | 98.93% |
| SKEW_Z | 1.5 | 10_30 IST | ₹-408.84 | ₹-349.48 | 2.99% | ₹-521.02 | ₹-429.44 | 0.00% | 96.74% |
| SKEW_Z | 1.5 | 13_30 IST | ₹-438.71 | ₹-438.04 | 9.09% | ₹-552.60 | ₹-545.62 | 6.06% | 96.74% |
| SKEW_Z | 1.5 | 15_10 IST | ₹-428.75 | ₹-459.17 | 16.42% | ₹-542.12 | ₹-577.41 | 11.94% | 97.83% |
| SMILE_Z | 1.0 | 10_30 IST | ₹-462.49 | ₹-361.42 | 0.00% | ₹-578.64 | ₹-459.70 | 0.00% | 99.01% |
| SMILE_Z | 1.0 | 13_30 IST | ₹-511.06 | ₹-493.65 | 2.60% | ₹-626.75 | ₹-608.29 | 0.00% | 100.00% |
| SMILE_Z | 1.0 | 15_10 IST | ₹-581.14 | ₹-573.50 | 6.49% | ₹-696.82 | ₹-697.90 | 2.60% | 100.00% |
| SMILE_Z | 1.5 | 10_30 IST | ₹-424.47 | ₹-355.09 | 0.00% | ₹-527.11 | ₹-444.91 | 0.00% | 98.21% |
| SMILE_Z | 1.5 | 13_30 IST | ₹-505.79 | ₹-517.50 | 6.00% | ₹-607.98 | ₹-629.44 | 2.00% | 100.00% |
| SMILE_Z | 1.5 | 15_10 IST | ₹-600.53 | ₹-625.06 | 10.00% | ₹-702.72 | ₹-705.02 | 6.00% | 100.00% |


The Base and Stress economics were uniformly negative. The maximum Base mean weekly net P&L across the 12 cells was **₹-408.84**. The maximum Stress mean weekly net P&L was **₹-521.02**. Both are negative.

The maximum Base median weekly net P&L was **₹-349.48**, while the maximum Stress median weekly net P&L was **₹-429.44**.

The highest Base positive-week rate was **16.42%**. The highest Stress positive-week rate was **11.94%**.

No cell reached the target of ₹5,000 mean and median weekly net P&L, and none approached the 70% positive-week requirement.

---

## 9. Costs and economic interpretation

The least-negative Base cell was SKEW_Z with |z|≥1.5 and a 10:30 exit. It generated raw gross P&L of approximately **₹1,668.50** across its observed trades, but incurred approximately **₹7,520** of slippage and **₹21,540.54** of transaction/statutory costs, leaving approximately **-₹27,392.04 total net** and **-₹408.84 mean weekly net**.

Stress doubled the slippage assumption. The same cell produced approximately **-₹34,908.29 total net** and **-₹521.02 mean weekly net**.

The results therefore do not indicate that a positive pre-cost effect was being erased only by a small frictional margin. The tested structures were economically negative after costs, and the sign of the result was already poor at the raw-gross level for many cells.

---

## 10. Null-control analysis

There were **60 null summary rows in Base and 60 in Stress**, corresponding to five complete-panel permutations for each of the 12 cells.

In both friction regimes, **0/12 true cells exceeded the mean weekly result of their own five-seed null controls**.

The true-minus-null mean-weekly difference ranged from approximately **-₹190.60 to -₹32.80 per week in Base** and **-₹195.55 to -₹42.89 per week in Stress**.

This pattern is inconsistent with a result that merely reflects the unconditional mechanics of selecting extreme surface states. Within the frozen design, randomized full-panel controls performed better on mean weekly net for every cell.

---

## 11. Bootstrap results

All twelve Base 95% bootstrap intervals for mean weekly net P&L were entirely below zero. The same was true in Stress.

For the least-negative Base mean cell (SKEW_Z, |z|≥1.5, 10:30), the bootstrap interval was approximately **-₹476.79 to -₹351.89 per week**.

For the corresponding Stress cell, the bootstrap interval was approximately **-₹599.48 to -₹454.92 per week**.

These intervals are descriptive uncertainty summaries, not multiplicity-adjusted hypothesis tests.

---

## 12. Promotion gate

The preregistered economic gate required, in both Base and Stress:

- mean weekly net ≥ ₹5,000
- median weekly net ≥ ₹5,000
- positive-week rate ≥ 70%
- execution coverage ≥ 80%
- no post-result design change

Results:

| Regime | True cells | Promotion passes |
|---|---:|---:|
| Base | 12 | **0** |
| Stress | 12 | **0** |

Execution coverage itself passed for all 12 cells, but the economic conditions failed universally.

**WFA/OOS promotion is therefore not authorized.**

---

## 13. Discussion

The tested hypothesis was that extreme local option-surface shape contains a short-horizon, mean-reverting pricing opportunity that can be harvested with a bounded-risk structure. The data-quality portion of the experiment was adequate: surface coverage was above the preregistered threshold, expiry selection was complete, prior-only barriers were clean, and execution coverage for all true cells exceeded the required 95% floor.

The economic evidence was nevertheless consistently negative. Both surface features, both thresholds and all three exits produced negative mean and median weekly P&L in Base and Stress. Positive-week frequencies were very low. The null controls were also negative, but the true signal cells were lower still across all 12 matched configurations.

One interpretation is that local skew/smile extremes, as defined here, may primarily reflect compensation for risks and microstructure frictions rather than a rapidly monetizable mean-reversion edge. The experiment cannot distinguish that explanation from other possibilities such as stale marks, bid/ask asymmetry absent from the OHLC source, or the particular four-leg payoff geometry. Those are hypotheses for future research, not tuning instructions for this closed phase.

The result also shows why the project keeps a separate cost-aware stress regime: modest surface-state effects can be overwhelmed by brokerage, statutory charges and repeated four-leg option turnover. In this experiment, the net sign did not survive even under the less severe Base friction.

---

## 14. Strengths

1. **Preregistration and finite search.** The surface definitions, thresholds, exits, legs, costs and promotion rule were frozen before numerical discovery.
2. **Leakage controls.** Surface inputs were fixed at 09:30, z-scores used only prior sessions, and execution began at 09:31.
3. **Realistic costs.** Historical lot sizes and the project's date-aware brokerage/statutory cost model were retained.
4. **Independent null controls.** Five complete-panel permutations per friction reduced the risk that apparent performance was a mechanical consequence of the conditioning procedure.
5. **Execution coverage validation.** All true cells passed the 95% executable-price coverage threshold after the final engineering correction.

---

## 15. Limitations

1. The surface was local and strike-based rather than a full arbitrage-free volatility surface.
2. The Black-Scholes inversion used a simple q=0/r=0 convention and therefore ignores forward-price/dividend refinements.
3. The pinned dataset is OHLC-style one-minute data and does not provide historical order-book depth/queue position.
4. The 60-session z-score requires complete prior observations, leaving 691 feature-eligible sessions out of 1,225 raw 09:30 sessions.
5. Only one next-expiry surface was used; term-structure information across multiple expiries was not tested.
6. The four-leg structures were intentionally frozen and therefore do not test alternative payoff geometries.
7. The experiment was discovery-only. No independent out-of-sample promotion was earned.

---

## 16. Conclusion

Phase 32 does **not** produce a viable ₹5,000/week trading strategy under the preregistered conditions.

The data and execution gates passed, but all 12 true cells failed the economic promotion gate in both Base and Stress. No cell had positive mean weekly net P&L; the strongest mean weekly result remained negative in both regimes. No WFA/OOS promotion is authorized.

This phase should be treated as **closed negative discovery evidence**, not as a reason to retune strike distances, z-score thresholds, expiry selection, exit times or payoff construction after observing the outcomes.

---

## 17. Future research directions

The next materially distinct research family should not optimize Phase 32. The pre-existing research plan identifies three relevant directions:

1. **Dealer/gamma exposure proxies**, especially time-aligned local gamma/vanna/charm state constructed from option open interest and IV rather than surface skew alone.
2. **Volatility-surface term structure**, testing cross-expiry shape and relative-value conditions rather than another local skew threshold.
3. **Cross-market/global transmission combined with independent options structure**, where the global variable is defined independently before looking at option outcomes.

A new phase should repeat the same pattern: literature/data review → preregistration → finite grid → Base/Stress → null controls → final manuscript → no post-result tuning.

---

## 18. Reproducibility and audit trail

Authoritative run: **36339168867**

Primary phase files:
- `docs/phase32_plan.md`
- `docs/phase32_literature_review.md`
- `research/phase32_options_skew_smile_dislocation.py`
- `tests/test_phase32_options_skew_smile_dislocation.py`
- `.github/workflows/phase-32-options-skew-smile-dislocation.yml`
- `reports/phase32/gate/data_gate.json`
- `reports/phase32/base/true_cell_summary_base.csv`
- `reports/phase32/stress/true_cell_summary_stress.csv`
- `reports/phase32/base/null_summary_base.csv`
- `reports/phase32/stress/null_summary_stress.csv`
- `reports/phase32/base/bootstrap_summary_base.csv`
- `reports/phase32/stress/bootstrap_summary_stress.csv`
- `reports/phase32/mean_weekly_net_base_stress.png`
- `reports/phase32/best_base_cumulative.png`

The GitHub Actions workflow includes a manual `workflow_dispatch` path on the main launcher and a branch-local trigger used for the authoritative run. All implementation errors encountered during the phase were recorded in `docs/error_log.md`.

---

## Appendix A — Frozen experiment matrix

2 features × 2 thresholds × 3 exits = **12 true cells**.

Null controls: 5 seeds × 12 cells × 2 frictions = **120 null summaries**.

---

## Appendix B — Data-gate failure diagnostics

Before the final successful run, the engineering sequence encountered and closed several pre-P&L defects:

- IV inversion boundary handling
- degenerate synthetic z-score fixture
- DuckDB reserved SQL alias
- trigger/checkout synchronization
- tuple-vs-list DataFrame indexing
- surface quote-key normalization
- execution-key omission of expiry
- empty-trade weekly aggregation
- incorrect filtered-`all()` coverage accounting

None of these defects changed the preregistered hypothesis, threshold, strike, expiry, exit, cost or promotion rule.

---

## Appendix C — Economic result range

- Base mean weekly net range across cells: approximately **-₹408.84 to -₹600.53**
- Stress mean weekly net range across cells: approximately **-₹521.02 to -₹702.72**
- Base maximum positive-week share: **16.42%**
- Stress maximum positive-week share: **11.94%**
- Base promotion passes: **0/12**
- Stress promotion passes: **0/12**
- WFA/OOS authorized: **No**

---

## Appendix D — Figures and supplementary artifacts

- `mean_weekly_net_base_stress.png`: Base vs Stress mean weekly net across the frozen 12-cell grid.
- `best_base_cumulative.png`: cumulative weekly net P&L for the least-negative Base cell.
- `surface_feature_panel.csv`: session-level surface and feature panel.
- `trades_base.csv` / `trades_stress.csv`: executed four-leg trade ledgers.
- `weekly_base.csv` / `weekly_stress.csv`: weekly net P&L.
- `null_trades_base.csv` / `null_trades_stress.csv`: randomized-control trade ledgers.
- `price_coverage.csv`: cell-level execution coverage.
- `bootstrap_summary_*.csv`: bootstrap uncertainty summaries.

---

## Appendix E — Phase decision

**Decision:** Close Phase 32.  
**Promotion:** None.  
**WFA/OOS:** Not authorized.  
**Post-result tuning:** Prohibited.  
**Next family:** Dealer/gamma or multi-expiry volatility-surface structure, as a new preregistered phase.
