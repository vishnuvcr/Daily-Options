# Phase 48 — Prior-Session Return Direction × Opening-Gap Direction Result

## Authoritative execution

- Workflow: **36538835468**
- Branch: phase-48-prior-return-gap-direction-v1
- Artifact: **11019348113**
- Artifact SHA-256: **ff5e86f91a18a85b803531bb555415093a9147d1b76e3f5dc34bb2da5327e93f**

## Data integrity

- Study sessions: **1,228**
- Feature-eligible sessions: **1,214 / 1,228 = 98.86%**
- Prior-return coverage among eligible sessions: **100%**
- Expiry mapping: **100%**
- Prior-information violations: **0**
- 267 exact-expiry option files
- Execution coverage: **98.58%–99.23%** across all 8 true cells
- Base/Stress accounting: reconciled

## True-cell results

| State | Mapping | Exit | Base mean/wk | Base median/wk | Base positive weeks | Stress mean/wk | Stress median/wk | Stress positive weeks |
|---|---|---|---:|---:|---:|---:|---:|---:|
| PRIOR_UP | CONTINUE | 10:30 | -₹425 | -₹595 | 32.8% | -₹538 | -₹673 | 29.5% |
| PRIOR_UP | CONTINUE | 15:10 | -₹519 | -₹1,209 | 32.8% | -₹630 | -₹1,285 | 31.6% |
| PRIOR_UP | FADE | 10:30 | -₹395 | -₹424 | 35.7% | -₹508 | -₹531 | 33.2% |
| PRIOR_UP | FADE | 15:10 | -₹355 | -₹622 | 41.0% | -₹466 | -₹702 | 38.5% |
| PRIOR_DOWN | CONTINUE | 10:30 | -₹371 | -₹279 | 39.8% | -₹476 | -₹359 | 39.0% |
| PRIOR_DOWN | CONTINUE | 15:10 | -₹536 | -₹665 | 38.5% | -₹639 | -₹821 | 36.8% |
| **PRIOR_DOWN** | **FADE** | **10:30** | **-₹336** | **-₹433** | **37.7%** | **-₹441** | **-₹513** | **37.2%** |
| PRIOR_DOWN | FADE | 15:10 | -₹348 | -₹822 | 37.7% | -₹452 | -₹862 | 37.2% |

**0/8** cells met the promotion gate in Base or Stress.

## Best-cell null comparison

For PRIOR_DOWN / FADE / 10:30:

- Base true mean weekly net: **-₹336**
- Five permutation-null means: approximately **-₹204, -₹385, -₹322, -₹482, -₹394**
- Null average: **-₹357**
- Stress true mean weekly net: **-₹441**
- Five permutation-null means: approximately **-₹305, -₹485, -₹421, -₹581, -₹493**
- Null average: **-₹457**

The true cell was slightly better than the matched null average, but remained economically negative and far below the ₹5,000/week gate.

## Temporal stability

The best cell, PRIOR_DOWN / FADE / 10:30, was negative in 2021, 2023, 2024, 2025 and 2026 in Base, with only 2022 positive. Stress was negative in every year. The interaction therefore does not provide a stable after-cost edge.

## Decision

**CLOSED — NEGATIVE DISCOVERY.**

Prior-session return direction does not rescue the opening-gap strategy under the frozen one-lot debit-spread execution and realistic friction model.

No threshold, state, mapping, exit, or execution retuning is authorized.

## Strengths

- 98.86% feature eligibility and 100% prior-return/expiry coverage.
- Zero prior-information violations.
- 8 finite true cells and 5 permutation nulls per cell.
- Historical lot sizes and realistic Base/Stress costs.
- Execution coverage above 95% in every true cell.

## Limitations

- The feature uses only the sign, not magnitude, of the prior-session return.
- The 09:31 debit-spread implementation can remain cost-dominated when directional movement is insufficient.
- No WFA/OOS is justified after failure of the frozen discovery gate.
