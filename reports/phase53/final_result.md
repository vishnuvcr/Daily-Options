# Phase 53 — Same-Session 09:30 ATM-Adjacent IV Skew × Opening Direction Result

## Authoritative execution

- Workflow: **36548934744**
- Branch: phase-53-same-session-atm-skew-opening-v1
- Artifact: **11023921928**
- Artifact SHA-256: **847ed7c77a3998cab05873f51713850a8d90e2ca046ce4cb71686aea115e2be5**

## Data integrity

- Study sessions: **1,228**
- Post-warm-up sessions: **1,168**
- Feature-eligible sessions: **1,146 / 1,168 = 98.12%**
- 09:30 skew valid sessions: **1,154 / 1,168 = 98.80%**
- Feature-expiry mapping: **100%**
- Prior-information violations: **0**
- Exact-expiry option files: **267**
- Execution coverage: **98.79%–100%** across all 12 true cells
- Base/Stress accounting: reconciled

## True-cell results

| State | Mapping | Exit | Base mean/wk | Base median/wk | Base positive weeks | Stress mean/wk | Stress median/wk | Stress positive weeks |
|---|---|---|---:|---:|---:|---:|---:|---:|
| **LOW_SKEW** | **FADE** | **10:30** | **-₹198** | -₹249 | 43.9% | **-₹293** | -₹310 | 39.7% |
| HIGH_SKEW | FADE | 15:10 | -₹214 | -₹605 | 42.2% | -₹307 | -₹645 | 40.5% |
| MID_SKEW | FADE | 15:10 | -₹238 | -₹498 | 44.7% | -₹315 | -₹558 | 43.7% |
| MID_SKEW | FADE | 10:30 | -₹251 | -₹334 | 40.6% | -₹330 | -₹424 | 39.6% |
| HIGH_SKEW | CONTINUE | 10:30 | -₹253 | -₹283 | 41.6% | -₹347 | -₹370 | 38.7% |
| MID_SKEW | CONTINUE | 10:30 | -₹310 | -₹407 | 38.6% | -₹389 | -₹485 | 37.1% |
| LOW_SKEW | FADE | 15:10 | -₹341 | -₹873 | 38.6% | -₹433 | -₹993 | 37.6% |
| MID_SKEW | CONTINUE | 15:10 | -₹357 | -₹831 | 35.0% | -₹434 | -₹900 | 33.0% |
| LOW_SKEW | CONTINUE | 10:30 | -₹404 | -₹597 | 36.2% | -₹498 | -₹654 | 35.1% |
| HIGH_SKEW | FADE | 10:30 | -₹461 | -₹518 | 31.8% | -₹555 | -₹583 | 30.6% |
| LOW_SKEW | CONTINUE | 15:10 | -₹540 | -₹1,057 | 36.0% | -₹632 | -₹1,160 | 34.9% |
| HIGH_SKEW | CONTINUE | 15:10 | -₹607 | -₹574 | 39.3% | -₹700 | -₹663 | 38.7% |

**0/12** true cells cleared the promotion gate.

## Best-cell null comparison

Best true cell: **LOW_SKEW / FADE / 10:30**

- Base true mean weekly net: **-₹198**
- Five permutation-null means: -₹208, -₹146, -₹275, -₹181, -₹357
- Null mean: **-₹233**
- Stress true mean weekly net: **-₹293**
- Five permutation-null means: -₹291, -₹226, -₹356, -₹263, -₹444
- Null mean: **-₹316**

The true state modestly outperformed the matched null average, but both true and null economics remained negative. This is not a tradable after-cost edge.

## Decision

**CLOSED — NEGATIVE DISCOVERY.**

Same-session 09:30 adjacent-strike IV skew carries some weak information relative to permutation controls, but none of the 12 frozen combinations achieves the required weekly expectancy, median and consistency after Base and Stress friction.

No skew threshold, moneyness, lookback, direction mapping, entry/exit, spread width or cost-model retuning is authorized.

## Strengths

- 98.12% post-warm-up feature eligibility.
- 98.80% same-session skew coverage.
- 100% expiry mapping.
- Zero prior-information violations.
- 12 finite cells plus 5 permutation nulls per cell.
- Historical lot sizes and realistic Base/Stress costs.
- Execution coverage remained above 95% in every true cell.
