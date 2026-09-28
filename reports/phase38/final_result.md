# Phase 38 — NIFTY Opening Volatility / Price-Structure
## Final Research Manuscript

Status: CLOSED — NEGATIVE DISCOVERY  
Authoritative workflow: 36408210374  
Branch: phase-38-opening-volatility-structure-v1

## Abstract
Phase 38 tested whether a strictly prior 60-session NIFTY opening-range volatility state, conditioned on the first 15-minute directional move, could identify a cost-aware short-horizon directional debit-spread edge. The frozen design used HIGH_VOL/LOW_VOL states at ±0.75 z-score, CONTINUE/FADE mappings, 09:31 entry, 10:30/15:10 exits, a one-lot 200-point debit spread, historical lot sizes, Paytm Money/NSE/statutory charges, and Base/Stress slippage of ₹0.20/₹0.40 per option-price unit/order.

The authoritative run passed all integrity gates. Of 1,228 raw NIFTY sessions, 1,168 post-warm-up sessions were all feature-eligible, with 100% feature coverage, 100% expiry mapping and zero prior-information violations. Base and Stress execution coverage exceeded 95% for every true cell and all accounting reconciliations passed.

Economically, 0/8 Base and 0/8 Stress cells passed the frozen ₹5,000 mean-weekly, ₹5,000 median-weekly and ≥70% positive-week gate. The best true cell, HIGH_VOL × FADE × 15:10, earned only ₹73.75 mean weekly in Base and ₹1.59 in Stress, with positive-week rates below 55%. No WFA/OOS was authorized and no result-driven tuning is permitted.

## 1. Research question
Can a NIFTY-specific early-session volatility regime, measured from the first 15 minutes and conditioned on opening direction, produce a reproducible short-horizon option-spread edge after realistic trading costs?

## 2. Methodology
The first 15 minutes were fixed at 09:15–09:29. Opening-range percentage was standardized against a strictly prior 60-session mean and sample standard deviation. A valid session required the 09:30 NIFTY reference for ATM construction. Signals were mapped to continuation or fade and monetized through a one-lot 200-point defined-risk debit spread.

No stops, targets, leverage changes, discretionary filters, or post-result parameter selection were permitted.

## 3. Results
| Cell | Base mean/week | Base median/week | Base positive weeks | Stress mean/week | Stress median/week | Stress positive weeks |
|---|---:|---:|---:|---:|---:|---:|
| HIGH_VOL × CONTINUE × 10:30 | -572.15 | -501.15 | 35.66% | -644.88 | -543.81 | 32.56% |
| HIGH_VOL × CONTINUE × 15:10 | -749.60 | -867.65 | 36.43% | -821.24 | -908.05 | 36.43% |
| HIGH_VOL × FADE × 10:30 | -127.42 | -144.21 | 47.29% | -200.16 | -184.19 | 44.19% |
| HIGH_VOL × FADE × 15:10 | +73.75 | +171.05 | 54.26% | +1.59 | +111.08 | 51.94% |
| LOW_VOL × CONTINUE × 10:30 | -248.10 | -299.54 | 38.89% | -330.12 | -367.72 | 36.11% |
| LOW_VOL × CONTINUE × 15:10 | -175.44 | -559.07 | 37.50% | -255.22 | -657.28 | 36.81% |
| LOW_VOL × FADE × 10:30 | -289.08 | -307.96 | 38.89% | -370.73 | -399.90 | 35.42% |
| LOW_VOL × FADE × 15:10 | -423.70 | -705.00 | 38.19% | -504.77 | -767.46 | 37.50% |

All 8 Base and 8 Stress promotion flags were false.

## 4. Null controls
Five fixed permutation nulls were run for each friction regime. Only HIGH_VOL × FADE × 15:10 exceeded all five null mean-weekly results. Its economic result was still far below the promotion threshold, so the null comparison does not justify WFA/OOS or promotion.

## 5. Cost/accounting assessment
All true-cell accounting reconciliations passed. The final result therefore reflects the frozen cost model rather than an uncosted gross-return screen.

## 6. Discussion
The family did not produce the required weekly edge. The result is stronger negative evidence because the feature and execution coverage gates passed cleanly and the negative conclusion survives doubled slippage. There is no basis to retune the ±0.75 state thresholds, opening interval, exit times, spread width or direction mapping after observing the results.

## 7. Strengths
- Complete study-period session coverage after warm-up.
- Strict prior-information barrier.
- Fixed finite grid and placebo controls.
- Historical lot sizes and explicit execution costs.
- Independent Base/Stress accounting reconciliation.

## 8. Limitations
- The hypothesis is specific to a 15-minute opening-range representation.
- Option-chain microstructure beyond the selected executable prices is not modeled.
- Only two fixed exits and one spread width were preregistered.
- The discovery gate deliberately stops before WFA/OOS after failure.

## 9. Conclusion
Phase 38 is retired as negative discovery. The frozen opening-volatility/price-structure family did not achieve the ₹5,000/week consistency objective after realistic costs.

## 10. Future research
The next distinct family will test an option-implied-versus-realized opening-move dislocation hypothesis using a new preregistered Phase 39 branch. No Phase 38 parameter will be reused by retuning.

## Appendix
Primary reproducibility files:
- docs/phase38_plan.md
- docs/phase38_literature_review.md
- docs/phase38_status.md
- docs/phase38_error_log.md
- research/phase38_opening_volatility_structure.py
- tests/test_phase38_opening_volatility_structure.py
- .github/workflows/phase-38-main-launcher.yml
- reports/phase38/