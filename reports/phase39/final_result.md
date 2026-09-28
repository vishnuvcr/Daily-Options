# Phase 39 — NIFTY Option-Implied vs Realized Opening-Move Dislocation
## Final Research Manuscript — DATA-LIMITED

### Abstract
Phase 39 tested a preregistered opening dislocation hypothesis comparing the NIFTY first-15-minute realized move with a 09:30 ATM option-implied 15-minute move. The clean authoritative workflow passed unit tests, source diagnostics and the corrected execution mapping, but failed the frozen data-quality gate. Of 1,234 raw sessions, 1,174 were post-warm-up; only 838 (71.38%) had a complete prior-only feature, below the required 95%. Direct IV input coverage was 98.64%, expiry mapping was 100%, prior-information violations were zero, and corrected minimum execution quote coverage was 96.99%.

The failure was driven by 16 post-warm-up sessions without a usable MOVE_RATIO; requiring 60 prior completed observations propagated those gaps into 320 downstream sessions without a valid z-score. No Base/Stress or null economics were accepted, and no WFA/OOS was authorized.

### Research question
Can an unusually large or small NIFTY first-15-minute move relative to the contemporaneous option-implied 15-minute move generate a reproducible cost-aware short-horizon directional option edge?

### Methodology
The study fixed the signal at 09:30, used nearest-₹50 ATM, strict next-expiry selection, CE/PE implied volatility, annualized-volatility scaling by sqrt(15/390), a strictly prior 60-session standardized MOVE_RATIO, CONTINUE/FADE mappings and 09:31/10:30/15:10 defined-risk debit-spread execution. Costs and doubled slippage were frozen before numerical execution.

### Data-quality results
| Gate | Result | Required |
|---|---:|---:|
| Post-warm-up feature eligibility | 71.38% (838/1,174) | ≥95% |
| Direct IV input coverage | 98.64% | ≥95% |
| Expiry mapping | 100% | ≥95% |
| Prior-information violations | 0 | 0 |
| Minimum execution coverage | 96.99% | ≥95% |

### Missingness diagnosis
Sixteen sessions had missing raw MOVE_RATIO values. Because the standardized feature was defined over the prior 60 completed sessions without imputation, missing observations created 320 additional sessions without a valid prior-only z-score. This is a source-observability limitation under the frozen method, not evidence of profitability or unprofitability.

### Economic analysis
No economic result was accepted. Base, Stress and five-seed null P&L were not run because the data gate failed.

### Strengths
- Strict no-lookahead information barrier.
- Direct option-source diagnostics confirmed real 09:30 IV quotes.
- Execution-source diagnostic confirmed representative 09:31/10:30/15:10 quotes.
- Corrected execution coverage exceeded the required threshold.
- The closure criterion was frozen before observing the final coverage outcome.

### Limitations
- 16 missing source observations materially reduced strict 60-session feature-history coverage.
- No economic conclusion can be drawn.
- The family may still contain information under a materially different missing-data methodology, but changing that methodology here would be post-result redesign and is not authorized.

### Conclusion
Phase 39 is **DATA-LIMITED and retired**. It does not supply a trading strategy result. The next family should use a distinct prior-day option-implied volatility state that does not require the same-day 09:30/first-15-minute ratio history.

### Future direction
Phase 40 will test prior-day ATM NIFTY implied volatility relative to prior realized volatility as a state for normalizing the next-session opening gap, using a fresh branch, independent null controls, the same realistic cost model, and the same ₹5,000/week gate.

### Reproducibility appendix
- Authoritative integrity rerun: workflow 36410759707, attempt 2.
- reports/phase39/gate/data_gate.json
- reports/phase39/gate/price_coverage.csv
- reports/phase39/diagnostics/source_snapshot_diagnostic.json
- reports/phase39/diagnostics/execution_quote_diagnostic.json
- research/phase39_implied_realized_opening_dislocation.py
- docs/phase39_plan.md