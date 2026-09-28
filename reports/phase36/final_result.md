# Phase 36 — Final Result: Global Shock Breadth / Cross-Market Disagreement

## Decision
**CLOSED / RETIRED — discovery gate failed. No WFA/OOS.**

Authoritative successful workflow: **36378802491**.

## Data integrity
The corrected run passed the global data gate:
- raw NIFTY sessions: 1,228
- global-feature-eligible sessions: 1,164
- warm-up/global-unavailable sessions: 64
- prior-information violations: 0

Execution quote coverage passed in all four cells:
- BROAD_SHOCK × 10:30: 153/157 = 97.45%
- BROAD_SHOCK × 15:10: 153/157 = 97.45%
- SPLIT_SHOCK × 10:30: 4/4 = 100%
- SPLIT_SHOCK × 15:10: 4/4 = 100%

## True-cell results

| State | Exit | Trades | Weeks | Base total net | Base mean weekly | Base median weekly | Base positive-week rate | Stress total net | Stress mean weekly | Stress median weekly | Stress positive-week rate |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BROAD_SHOCK | 10:30 | 153 | 111 | -₹3,307.72 | -₹29.80 | -₹170.16 | 43.24% | -₹9,728.51 | -₹87.64 | -₹222.93 | 42.34% |
| BROAD_SHOCK | 15:10 | 153 | 111 | -₹5,704.05 | -₹51.39 | -₹508.52 | 40.54% | -₹12,125.00 | -₹109.23 | -₹548.50 | 40.54% |
| SPLIT_SHOCK | 10:30 | 4 | 4 | +₹2,047.28 | +₹511.82 | +₹369.09 | 50.00% | +₹1,867.37 | +₹466.84 | +₹319.11 | 50.00% |
| SPLIT_SHOCK | 15:10 | 4 | 4 | -₹6,204.07 | -₹1,551.02 | -₹1,730.94 | 25.00% | -₹6,383.98 | -₹1,596.00 | -₹1,780.92 | 25.00% |

No cell satisfies all frozen promotion conditions in both frictions: mean weekly net >= ₹5,000, median weekly net >= ₹5,000, and positive-week rate >=70%.

## Null controls
Five fixed block-permutation seeds were completed for Base and Stress. The null distributions did not provide evidence that the observed true-cell outcomes constituted a robust weekly trading edge. The sparse SPLIT_SHOCK cells are particularly low-power because only four true candidate days were available.

## Interpretation
The evidence does not support promoting global-shock breadth as a weekly NIFTY debit-spread strategy under the frozen rules. The main BROAD_SHOCK state loses money in both exit horizons and both frictions. The only positive true cell, SPLIT_SHOCK × 10:30, has only four trades/four weeks and fails the consistency thresholds materially.

## Accounting and implementation
The authoritative workflow passed unit tests, pinned-data acquisition, data gate, Base, Stress and accounting reconciliation. No post-result retuning was performed.

## Conclusion
Phase 36 is **retired without WFA/OOS promotion**. The family should not be expanded by changing breadth thresholds, exits, wings, indices or costs after observing the results.

## Next direction
The next distinct family should test an actual cross-market/local-price dislocation rather than another global-state partition. A preregistered opening-gap divergence test is the next candidate: compare the prior-session global shock direction with the NIFTY 09:30 opening-gap direction and test a frozen continuation/fade rule with the same defined-risk spread execution and weekly promotion gate.
