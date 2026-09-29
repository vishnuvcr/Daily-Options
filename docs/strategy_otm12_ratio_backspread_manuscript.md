# Research Manuscript — NIFTY Intraday OTM1 / 2xOTM2 Four-Leg Ratio Backspread

## Abstract

This study backtested a fixed one-lot intraday NIFTY options structure: sell 1 OTM1 put, buy 2 OTM2 puts, sell 1 OTM1 call, and buy 2 OTM2 calls. The strategy used a 09:30 IST reference, entered using the 09:31 IST option-bar open, selected the nearest listed expiry on or after the trade date, and exited at the 15:15 IST bar open, with a documented 15:14 fallback only when the 15:15 leg quote was unavailable. The analysis used a pinned 1-minute NIFTY/options dataset and included brokerage, transaction charges, statutory charges, GST, STT/stamp-duty conventions and two slippage assumptions.

Across 1,227 eligible sessions, 1,209 complete four-leg trades were executable, giving 98.53% execution coverage. The clean Base run (₹0.20/option-point/side slippage) produced gross P&L of -₹272,009.75, total costs of ₹445,912.12 and net P&L of -₹717,921.87. The Stress run (₹0.40 slippage) produced the same gross P&L but total costs of ₹602,848.12 and net P&L of -₹874,857.87. The strategy therefore lost money before any attempt at loss avoidance, and transaction costs were a major component of the negative net result.

The losing-trade analysis found no robust single pre-entry predictor among the frozen feature family. A shallow chronological loss tree had Base cross-validated AUC of approximately 0.506, effectively indistinguishable from chance. Two adverse circumstances were reasonably persistent in discovery-to-holdout replication: very large prior-day ranges and expiry-day entries. A deliberately frozen holdout probe then tested only those filters. The combined rule reduced the magnitude of losses, but the untouched holdout remained negative: -₹111,294 under Base and -₹151,338 under Stress, with 66.38% of holdout trades retained. No tested filter produced positive holdout expectancy.

The principal inference is that this fixed structure can profit when one option wing experiences a sufficiently large expansion in the farther OTM longs to overwhelm the opposite wing's loss, time decay and transaction costs. The study did not identify a sufficiently reliable pre-entry condition that makes the fixed baseline economically attractive after costs.

## 1. Research question

Under a fixed one-lot implementation of the NIFTY four-leg structure

- Sell 1 OTM1 PUT
- Buy 2 OTM2 PUT
- Sell 1 OTM1 CALL
- Buy 2 OTM2 CALL

what pre-entry market circumstances are associated with losing trades, what circumstances are associated with profitable trades, and can a small set of pre-specified no-trade conditions improve out-of-sample net performance?

### Secondary questions

1. How often does the strategy execute completely using the pinned 1-minute option data?
2. How large is the effect of realistic trading frictions?
3. Are loser characteristics stable between the discovery period and an untouched chronological holdout?
4. Does a shallow, interpretable loss model provide useful pre-entry discrimination?
5. Can a small number of discovery-derived filters produce positive holdout expectancy without tuning on the holdout?

## 2. Aims

### Primary aim

Quantify the economic performance and losing-trade circumstances of the fixed NIFTY intraday OTM1/2xOTM2 four-leg ratio backspread.

### Secondary aims

- Measure execution coverage and data completeness.
- Decompose gross P&L and transaction-cost drag.
- Compare winners and losers using only information available by 09:30 IST.
- Determine whether loser patterns replicate out of sample.
- Test a tightly bounded set of frozen no-trade rules.

## 3. Objectives

1. Implement the frozen strategy exactly once without post-result parameter tuning.
2. Validate timestamp handling, expiry selection, strike selection and four-leg completeness.
3. Run Base and Stress friction models.
4. Quantify win rate, mean/median P&L, profit factor, drawdown and calendar/expiry effects.
5. Compare winner and loser distributions using non-parametric tests.
6. Examine five fixed discovery quantile bins for the main candidate features and replicate those bins unchanged on holdout.
7. Fit a shallow loss tree as a diagnostic rather than as an optimizer.
8. Test only the frozen Phase C filter candidates on the 2025+ holdout.
9. Produce a bounded conclusion rather than open-ended optimization.

## 4. Frozen strategy specification

### Entry

- Underlying: NIFTY index.
- Position size: 1 lot.
- Entry reference: 09:30 IST NIFTY close.
- Executable option entry: 09:31 IST option-bar open.
- Expiry: nearest listed NIFTY expiry on or after the trade date.
- OTM1 call: first listed strike strictly above the 09:30 NIFTY reference.
- OTM2 call: second listed strike above OTM1 call.
- OTM1 put: first listed strike strictly below the reference.
- OTM2 put: second listed strike below OTM1 put.
- Positions: OTM1 PE -1, OTM2 PE +2, OTM1 CE -1, OTM2 CE +2.

### Exit

Primary exit: 15:15 IST option-bar open for all four legs.

Fallback: 15:14 IST option close was used only where the corresponding 15:15 open was unavailable; all four legs had to use the same exit mark time. The fallback was added solely as a data-execution robustness rule and was not tuned against P&L.

### Lot-size and friction handling

The research reused the repository's historical NIFTY lot-size regimes and established Paytm Money/NSE/statutory cost convention, including brokerage, exchange charge, SEBI fee, STT, stamp duty, GST and explicit option-price slippage.

Base slippage: ₹0.20 per option price point per side.

Stress slippage: ₹0.40 per option price point per side.

No separate broker margin requirement is claimed in this manuscript; P&L is not presented as a return on margin/capital.

## 5. Data and data-quality methodology

The research used a pinned revision of the 1-minute NIFTY/index-options dataset already used by the repository. The data gate identified 1,227 sessions with usable index morning features and mapped expiries in the actual strategy eligibility pipeline. Exact expiry files were used; the broader cache contained 267 expiry files, while 257 expiry files were actually touched by the eligible-session backtest.

A dedicated timestamp probe demonstrated that the option timestamps were available at the intended 09:31 and 15:15 IST bars. The principal implementation defect encountered during development was instead a Python-date versus datetime-like trade-date mismatch in the session/quote join. This caused the first zero-trade runs and was corrected with explicit `dt.date` normalization plus a regression test.

The clean backtest then passed unit tests, coverage checks, trade completeness checks and final feature-analysis reporting.

## 6. Chronological research design

The discovery/holdout split was fixed before performance interpretation:

- Discovery: 2021-07-01 through 2024-12-31.
- Holdout: 2025-01-01 through 2026-08-04.

No holdout observation was used to choose a new threshold. Discovery quantile boundaries were transported unchanged to the holdout.

## 7. Candidate pre-entry feature family

The prospective feature family was frozen to:

- overnight gap and absolute gap
- first-15-minute return
- first-15-minute absolute return
- first-15-minute range
- prior-day range and return
- prior-20-session median range
- day-of-week
- expiry proximity and expiry-day flag
- NIFTY entry level
- four-leg entry premiums
- short-premium sum
- far-premium sum
- net entry credit/debit
- long-to-short premium ratio

Post-entry information was excluded from any prospective filter.

## 8. Statistical analysis

### Winner-versus-loser comparison

Winner and loser feature distributions in the discovery sample were compared with two-sided Mann–Whitney U tests. The test was used as a screening statistic, not as a multiple-testing claim of discovery.

### Quantile replication

For selected features, discovery quintile boundaries were frozen. Mean P&L and win rate were calculated within those bins and then replicated without change on the holdout.

### Loss-tree diagnostic

A shallow decision tree with maximum depth 3 and minimum leaf size 50 was fit to classify loss versus non-loss. Chronological cross-validation was used to assess discrimination. This tree was explicitly diagnostic and was not used to optimize thresholds.

### Performance measures

The research reported:

- trade count
- execution coverage
- gross P&L
- total costs
- net P&L
- win rate
- mean/median P&L
- mean win and mean loss
- profit factor
- maximum drawdown
- maximum gain/loss
- friction sensitivity
- discovery/holdout performance

## 9. Phase B results — validated baseline

### 9.1 Clean Base friction

| Metric | Base |
|---|---:|
| Eligible sessions | 1,227 |
| Executed trades | 1,209 |
| Execution coverage | 98.53% |
| Wins | 312 |
| Losses | 897 |
| Win rate | 25.81% |
| Gross P&L | -₹272,009.75 |
| Total costs | ₹445,912.12 |
| Net P&L | -₹717,921.87 |
| Mean net P&L/trade | -₹593.81 |
| Median net P&L/trade | -₹915.50 |
| Mean winning trade | ₹2,459.89 |
| Mean losing trade | -₹1,655.97 |
| Profit factor | 0.517 |
| Maximum drawdown | -₹716,320.49 |
| Maximum gain | ₹28,487.08 |
| Maximum loss | -₹14,059.65 |

### 9.2 Stress friction

| Metric | Stress |
|---|---:|
| Eligible sessions | 1,227 |
| Executed trades | 1,209 |
| Execution coverage | 98.53% |
| Wins | 289 |
| Losses | 920 |
| Win rate | 23.90% |
| Gross P&L | -₹272,009.75 |
| Total costs | ₹602,848.12 |
| Net P&L | -₹874,857.87 |
| Mean net P&L/trade | -₹723.62 |
| Median net P&L/trade | -₹1,032.73 |
| Mean winning trade | ₹2,521.14 |
| Mean losing trade | -₹1,742.90 |
| Profit factor | 0.454 |
| Maximum drawdown | -₹873,136.49 |
| Maximum gain | ₹28,307.08 |
| Maximum loss | -₹14,239.65 |

### Baseline interpretation

Gross performance was already negative before transaction costs. Costs then deepened the loss substantially. The strategy therefore does not merely suffer from a small execution-friction problem; its fixed payoff structure was unfavorable over the studied period.

## 10. Phase C results — what distinguishes losers?

### 10.1 Statistical separation was weak

For all 15 frozen pre-entry features, the discovery winner-versus-loser Mann–Whitney p-values were above 0.15. The smallest was for entry NIFTY level (p≈0.150), followed by first-15-minute absolute return (p≈0.180). No feature met a conventional p<0.05 threshold.

The clean Base shallow loss tree produced a 5-fold chronological CV AUC of approximately 0.506. This is effectively chance-level discrimination.

### 10.2 Persistent adverse bins

Two conditions recurred sufficiently to justify a tightly bounded holdout probe:

1. Very large prior-day range. The discovery top quintile was above approximately 1.352% prior-day range. Its mean P&L was -₹944 per trade in discovery and -₹1,952 per trade in holdout.
2. Expiry-day entry. Holdout expiry-day trades had mean P&L of approximately -₹1,373 and an 18.1% win rate.

Other apparent patterns were unstable. For example, first-15-minute absolute return showed materially different bin behavior between discovery and holdout, so it was not promoted to the frozen filter set.

## 11. Why profitable trades occur

The leg-level decomposition gives the clearest economic explanation.

A profitable trade usually needs one side of the structure to generate a substantial positive contribution from the two farther OTM long options. In the full sample, only about 6.4% of winners had both the call-side and put-side wing contributions positive; the common situation was one profitable wing offsetting one losing wing.

Among all winners:

- 57.7% had positive call-wing gross P&L.
- 48.7% had positive put-wing gross P&L.
- 93.6% had exactly one or otherwise at least one positive wing while the other was non-positive.
- 0% had both wings negative.

Among losers:

- 44.7% had both call and put wings negative.
- Positive wing contributions were often too small to offset the opposite-side loss and friction.

The holdout preserved this same broad mechanism: profitable trades had at least one positive wing in every observed case, while approximately 46.0% of holdout losers had both wings negative.

This is consistent with the economic shape of the fixed structure: it is not a generic premium-selling trade. It needs sufficiently large directional/volatility expansion in one tail for the 2x farther OTM long option position to overcome the loss on the nearer short option, the opposite wing's deterioration and trading costs.

## 12. Phase D — frozen holdout filter probe

The discovery top-quintile threshold for prior-day range was frozen at approximately 1.352%.

Only three filters were tested:

1. Exclude expiry-day entries.
2. Exclude days with prior-day range above the discovery 80th percentile.
3. Require both exclusions simultaneously.

### Base holdout

| Rule | Holdout trades | Retention | Holdout net P&L | Mean P&L | Win rate | Profit factor |
|---|---:|---:|---:|---:|---:|---:|
| Baseline | 348 | 100.0% | -₹282,985.19 | -₹813.18 | 27.59% | 0.541 |
| Exclude expiry day | 276 | 79.31% | -₹184,105.15 | -₹667.05 | 30.07% | 0.562 |
| Exclude top 20% prior-day range | 293 | 84.20% | -₹175,650.58 | -₹599.49 | 28.67% | 0.636 |
| Require both exclusions | 231 | 66.38% | -₹111,294.06 | -₹481.79 | 32.03% | 0.658 |

### Stress holdout

| Rule | Holdout trades | Retention | Holdout net P&L | Mean P&L | Win rate | Profit factor |
|---|---:|---:|---:|---:|---:|---:|
| Baseline | 348 | 100.0% | -₹343,081.19 | -₹985.87 | 26.72% | — |
| Exclude expiry day | 276 | 79.31% | -₹231,721.15 | -₹839.57 | 28.99% | — |
| Exclude top 20% prior-day range | 293 | 84.20% | -₹226,542.58 | -₹773.18 | 27.99% | — |
| Require both exclusions | 231 | 66.38% | -₹151,338.06 | -₹655.14 | 31.17% | 0.572 |

The combined filter reduced the magnitude of the loss but did not produce positive holdout expectancy. The same qualitative conclusion held under the higher-slippage Stress model.

## 13. Results synthesis

### What is common among losing trades?

The strongest recurring loser circumstances are:

- the underlying recently experienced an unusually large prior-day range, particularly above about 1.35% in this dataset;
- entry occurs on expiry day;
- the first 15 minutes and premium geometry do not provide a stable enough signal by themselves;
- at the payoff level, both wings can deteriorate together, or the positive wing can be too small to overcome the other wing and costs.

### In what circumstances does the structure tend to profit?

The reproducible mechanism is not a particular static NIFTY level or a simple gap threshold. Profits arise when one tail moves far enough, quickly enough, or with enough option repricing that the two farther OTM long contracts on that side generate a large positive P&L contribution.

That is a post-entry economic explanation rather than a proven pre-entry predictor. The study did not identify an entry-time rule that forecasts this expansion reliably enough to make the fixed structure profitable after costs.

## 14. Discussion

The strategy has a convex payoff architecture, but convexity alone is not sufficient for positive expectancy. The backtest shows that the cost of repeatedly buying two farther OTM options on both sides is material, while the nearer OTM short options do not generate enough premium income to offset this cost over the tested horizon.

The most important practical finding is therefore not that the strategy never wins. It does win, including occasional large winners. The issue is that large winners are too infrequent and/or too small relative to the collection of losing trades and trading costs.

The loser analysis also illustrates why naive filtering is dangerous. Some discovery features display plausible relationships, but several reverse or weaken in the holdout. The clean loss-tree AUC near 0.5 reinforces the interpretation that the pre-entry feature set, by itself, contains limited stable predictive information about whether the day will generate enough tail expansion.

The frozen holdout probe provides a useful negative result. Excluding the most obviously adverse regimes improves average P&L and win rate, but not enough to cross zero. This is evidence that the recurring loser conditions are real enough to matter but insufficient to rescue the fixed strategy.

## 15. Strengths

- Chronological discovery/holdout design prevented holdout tuning.
- Explicit Base and Stress friction scenarios were used.
- Historical lot-size changes were handled.
- Four-leg completeness was enforced.
- The timestamp and trade-date defects were isolated and corrected before accepting P&L.
- The final baseline and filter probe were rerun cleanly after implementation fixes.
- Post-entry information was excluded from prospective filtering.
- The filter phase was bounded rather than open-ended.
- The payoff was decomposed into call and put wing contributions to connect statistical results with strategy mechanics.

## 16. Limitations

- The underlying option dataset has partial coverage for illiquid or far strikes; execution coverage was high but not 100%.
- The 15:14 fallback is a data-execution convention that should be stress-tested further against a strict 15:15-only specification in future work.
- The analysis uses 1-minute OHLC bars rather than tick-by-tick bid/ask microstructure, so actual executable spread and queue effects may differ.
- Broker margin requirements and capital utilization were not estimated as an ROI denominator.
- The current feature family does not include a full volatility-surface state, India VIX term structure, implied-volatility skew, open-interest flow, FII/DII positioning, realized-volatility regime labels or cross-asset overnight signals.
- The tested structure is fixed; a different selection rule for OTM distance may behave differently.
- Statistical screening across multiple features creates a multiple-comparisons issue; therefore feature p-values were used descriptively and were not treated as proof of causality.

## 17. Conclusion

For the exact fixed one-lot NIFTY structure tested here, the baseline is economically unfavorable after realistic costs.

The clean Base result was -₹717,921.87 net across 1,209 trades, and the Stress result was -₹874,857.87. The strategy's profitable trades are driven by sufficiently strong one-sided tail expansion, but the research did not find a stable pre-entry signal that forecasts that expansion well enough.

The recurring loser circumstances are useful clues rather than a validated rescue strategy. Very large prior-day ranges and expiry-day entries are associated with worse outcomes and remain adverse in the holdout, but filtering them does not turn the strategy profitable.

Therefore this study closes with a negative but usable conclusion:

**Do not treat the fixed baseline as an economically validated intraday trading strategy. The evidence supports further research into volatility/movement regime selection rather than continued optimization of the same simple pre-entry filters.**

## 18. Future research directions

1. Model expected tail expansion directly using realized-volatility regime, India VIX level/term structure, option-implied volatility skew and term structure.
2. Add pre-open and opening-session cross-market signals, including global index futures, USDINR, crude and gold, while preserving strict information-time boundaries.
3. Study distance-based rather than first-two-listed-strikes OTM selection, with parameters preregistered before new holdout periods.
4. Incorporate option-chain open interest, volume, bid/ask spread and IV changes where data quality permits.
5. Replace the fixed 15:15 exit with a separately preregistered time-horizon study, such as 30-minute, 60-minute and end-of-day exits, without mixing the results.
6. Estimate capital/margin requirements and return on capital using broker-specific margin rules.
7. Test whether the structure works as part of a conditional volatility breakout framework rather than as a daily unconditional trade.
8. Run a fresh future holdout after all design choices are preregistered and locked.

## Appendix A — Clean implementation defects encountered and corrected

| ID | Problem | Resolution |
|---|---|---|
| EOTM12-001 | Workflow friction expression issue | Corrected workflow |
| EOTM12-002 | Missing huggingface_hub dependency | Added dependency |
| EOTM12-003 | DuckDB timezone casting issue | Explicit IST normalization |
| EOTM12-004 | Direct timezone-to-TIME option cast rejected | Timestamp normalization before filtering |
| EOTM12-005 | No stage diagnostics after zero-trade result | Added persisted selection diagnostics |
| EOTM12-006 | Option/session trade_date dtype mismatch | Explicit date normalization + regression test |
| EOTM12-007 | Read-only pandas quantile array | Writable copy before bin-boundary assignment |

## Appendix B — Authoritative runs

- Clean baseline: GitHub Actions run 36532252218.
- Phase C analysis: run 36533168599.
- Phase D frozen holdout probe: run 36533292973.
- Dataset cache revision: 51ca58c.
- Strategy branch: `strategy/otm1-2x-otm2-ratio-backspread-v1`.

## Appendix C — Key repository documents

- Strategy research plan: `docs/strategy_otm12_ratio_backspread_plan.md`
- Strategy status: `docs/strategy_otm12_ratio_backspread_status.md`
- Error log: `docs/error_log_strategy_otm12_ratio_backspread.md`
- Phase C analysis: `docs/strategy_otm12_phase_c_loss_patterns.md`
- Phase D analysis: `docs/strategy_otm12_phase_d_holdout_filter.md`
