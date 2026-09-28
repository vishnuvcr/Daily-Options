# Phase 37 — Final Result: Global Shock × NIFTY Opening Dislocation

## Decision
**CLOSED / RETIRED — discovery gate failed. No WFA/OOS.**

Authoritative successful workflow: **36379200435**.

## Data integrity and execution coverage
- Raw NIFTY sessions: 1,228
- Global-feature-eligible: 1,164
- Combined global + opening-gap feature coverage: 100%
- Prior-information violations: 0
- CONVERGENT × 10:30: 79/80 = 98.75%
- CONVERGENT × 15:10: 79/80 = 98.75%
- DIVERGENT × 10:30: 26/27 = 96.30%
- DIVERGENT × 15:10: 26/27 = 96.30%

All four cells passed the technical execution-coverage gate.

## True-cell results

| State | Exit | Trades | Weeks | Base mean/wk | Base median/wk | Base +weeks | Stress mean/wk | Stress median/wk | Stress +weeks |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| CONVERGENT | 10:30 | 79 | 65 | -₹144.09 | -₹123.51 | 41.54% | -₹193.48 | -₹163.49 | 41.54% |
| CONVERGENT | 15:10 | 79 | 65 | -₹532.10 | -₹843.66 | 40.00% | -₹581.49 | -₹883.64 | 40.00% |
| DIVERGENT | 10:30 | 26 | 26 | -₹525.70 | -₹557.64 | 30.77% | -₹570.14 | -₹587.63 | 30.77% |
| DIVERGENT | 15:10 | 26 | 26 | -₹612.27 | -₹1,081.70 | 34.62% | -₹656.71 | -₹1,121.68 | 30.77% |

All four cells fail the frozen mean-weekly >= ₹5,000, median-weekly >= ₹5,000 and >=70% positive-week promotion gate.

## Null controls
Five fixed global block-permutation seeds were completed under both Base and Stress. The true results do not show a stable advantage over the fixed null controls. Importantly, even without formal p-value interpretation, the true cells are far below the economic promotion threshold.

## Cost/accounting
Accounting reconciliation passed. The frozen cost model retained historical lot sizes, Paytm Money/NSE/statutory charges and Base/Stress slippage.

## Interpretation
The alignment or divergence between a large prior global shock and the NIFTY 09:30 opening gap, under the frozen thresholds, did not produce a monetizable short-horizon directional debit-spread strategy.

This phase does not justify changing the global threshold, gap threshold, direction mapping, spread width or exits.

## Conclusion
Phase 37 is **retired without WFA/OOS promotion**.

## Next research direction
A materially distinct, higher-density mechanism is required. The next phase will isolate the NIFTY opening-gap effect itself using a preregistered continuation-versus-reversal finite grid, independent of the failed global-conditioning layer.
