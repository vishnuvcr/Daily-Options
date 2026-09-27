# Phase 31.10 — Institutional Futures Positioning × NIFTY Opening-Gap Translation — Final Manuscript

## Abstract
Phase 31.10 tested whether prior-session participant-wise NIFTY index-futures positioning contains enough information to generate a cost-aware same-day NIFTY option-spread strategy. The frozen experiment used three prior-only standardized positioning features, two signal thresholds and two exits, producing 12 true cells. The study used official NSE participant-wise F&O open-interest archives from 2021-07-01 through 2026-08-31, a pinned NIFTY/options dataset, historical lot sizes, explicit transaction costs and Base/Stress slippage, plus five full-panel null permutations per cell and friction regime.

The data gate passed with 1,164/1,164 feature-eligible sessions complete, zero prior-positioning barrier violations, and 1,234/1,234 participant-OI source files. Execution-price coverage exceeded 97.4% for every true cell in both friction regimes. Nevertheless, 0/12 true cells passed the preregistered ₹5,000/week promotion gate in Base and 0/12 in Stress. No true cell had positive total net P&L.

## Research question
Does prior-session participant-wise NIFTY index-futures positioning improve defined-risk option-spread expectancy sufficiently to meet the project's ₹5,000 net/week requirement after realistic costs and Base/Stress slippage?

## Methodology
The primary predictors were:
1. FII index-futures net-ratio 60-observation prior-only z-score.
2. DII index-futures net-ratio 60-observation prior-only z-score.
3. FII-minus-DII index-futures net-ratio 60-observation prior-only z-score.

Thresholds were |z| ≥ 0.50 and |z| ≥ 1.00. Positive values mapped to a call debit spread and negative values to a put debit spread. Entry was 09:31, with 10:30 and 15:10 exits. The nearest eligible NIFTY expiry, ₹50 ATM strike and 200-point one-lot debit spread were used with historical lot sizes.

Base slippage was ₹0.20 per option-price unit per order; Stress was ₹0.40. Brokerage, statutory and exchange costs followed the frozen project charge model. The economic gate required mean weekly net ≥₹5,000, median weekly net ≥₹5,000, positive weeks ≥70%, and adequate execution coverage in both friction regimes.

## Data integrity
- NIFTY feature-eligible sessions: **1,164**
- Complete feature sessions: **1,164 (100%)**
- Prior-positioning barrier violations: **0**
- Participant-OI source files: **1,234 / 1,234**
- Execution coverage: **≥97.409%** for all true cells in Base and Stress
- Null seeds: **101, 202, 303, 404, 505**
- True cells: **12**
- Null summaries: **60 per friction regime**

## Results
### Base
Best mean weekly net: **-₹929.82/week**, corresponding to FII index-net z-score, |z|≥1.00, 10:30 exit.

### Stress
Best mean weekly net: **-₹1,077.44/week**, for the same cell.

The full frozen grid produced:
- **0/12** promotion passes in Base.
- **0/12** promotion passes in Stress.
- **0/12** cells with positive total net P&L.

The best observed Base mean was **₹5,929.82/week below** the project's ₹5,000 target. The best Stress mean was **₹6,077.44/week below** the target.

## Null controls
The five complete-panel permutations per cell were evaluated without changing the feature distribution. Null results are diagnostic only. Because the true cells were already economically negative, any relative separation from nulls cannot qualify the family for promotion.

## Interpretation
The experiment provides negative discovery evidence for this particular institutional-positioning construction. The conclusion is limited to the frozen features, thresholds, horizons, option structure, execution assumptions and study period. It does not establish that all institutional positioning measures are uninformative.

The opening-gap cross-tab is retained as a descriptive diagnostic and was not used to post-select trades.

## Strengths
- Official NSE participant-OI source.
- Full source manifest and hashes.
- Prior-information barrier.
- Finite preregistered grid.
- Null controls.
- Base/Stress friction testing.
- Historical lot-size handling.
- Execution-coverage validation.
- Explicit cost reconciliation.
- No result-driven parameter expansion.

## Limitations
- Participant OI is end-of-day aggregate positioning, not intraday order flow.
- Index-futures positioning does not fully describe participants' options, stock-futures or OTC exposures.
- The 60-observation z-score is only one representation of positioning persistence.
- Option execution uses observed historical prices rather than reconstructed full order-book queue dynamics.
- The study is discovery evidence rather than untouched OOS evidence.

## Conclusion
Phase 31.10 is **closed as negative discovery evidence**. No WFA/OOS promotion is authorized.

## Future research
A subsequent family must be materially distinct. Candidate research directions include option-skew/smile dislocations, dealer/gamma proxies, volatility-surface shape, or carefully time-aligned combinations of independent market-state variables. Any such family must be separately preregistered with a finite grid and explicit null controls.

## Reproducibility
Authoritative run: **36337462383**.

Final report path: `reports/phase31_10_final_result.md`.

No live-trading recommendation is implied by this research result.
