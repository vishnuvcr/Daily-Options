# Phase 56 — Prior-Session Candle Conviction Regime × Opening-Gap Direction Result

## Authoritative execution

- Workflow: **36551083186**
- Branch: phase-56-candle-conviction-gap-v1
- Artifact: **11025430232**
- Artifact SHA-256: **e1ad412e2fea255f45c13b440c0717b3aecae9846ab2d3f17c18a1673d17b1ac**

## Data integrity

- Raw sessions: **1,228**
- Post-warm-up sessions: **1,168**
- Feature-eligible sessions: **1,160 / 1,168 = 99.315%**
- Prior-body-ratio validity: **100%**
- Expiry mapping: **100%**
- Prior-information violations: **0**
- Execution coverage: **98.47%–99.10%** across all 12 cells
- Base/Stress accounting: **reconciled**

## True-cell results

The best true cell under both frictions was:

**LOW_CONVICTION / FADE / 15:10**

### Base
- Mean weekly net: **-₹125.86**
- Median weekly net: **-₹495.34**
- Positive-week rate: **43.18%**
- Total net: **-₹27,689**
- Max drawdown: **-₹74,518**

### Stress
- Mean weekly net: **-₹201.79**
- Median weekly net: **-₹546.51**
- Positive-week rate: **40.45%**
- Total net: **-₹44,393**
- Max drawdown: **-₹81,552**

All 12 true cells were negative under both Base and Stress.

## Null-control comparison

For the best true cell, the five permutation-null mean weekly nets were:

### Base
- seed 101: -₹381
- seed 202: -₹200
- seed 303: -₹380
- seed 404: -₹345
- seed 505: -₹16
- null average: approximately **-₹265/week**

### Stress
- seed 101: -₹460
- seed 202: -₹274
- seed 303: -₹461
- seed 404: -₹421
- seed 505: -₹92
- null average: approximately **-₹342/week**

The true cell outperformed the average randomized-label benchmark, but its absolute expectancy remained negative and far below the ₹5,000/week promotion threshold.

## Decision

**CLOSED — NEGATIVE DISCOVERY.**

The prior-session candle-body conviction regime does not produce a viable after-cost opening-gap strategy under the frozen execution and friction model.

No WFA/OOS is authorized. No body-ratio threshold, tercile definition, direction mapping, exit, expiry, spread width or cost retuning is permitted.

## Strengths

- 99.315% feature eligibility after warm-up.
- 100% prior-range validity and expiry mapping.
- Zero information-barrier violations.
- 12 fixed cells plus 5 permutation nulls per cell.
- Historical lots and full Base/Stress costs.
- Execution coverage above the frozen 95% threshold in every true cell.

## Limitations

- Candle conviction uses only body/range geometry and excludes volume, order flow and news.
- The best state still suffers from small directional expectancy relative to fixed option transaction costs.
- No WFA/OOS follows a failed discovery gate.
