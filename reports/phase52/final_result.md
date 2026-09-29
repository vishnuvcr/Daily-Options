# Phase 52 — Same-Session 09:30 ATM IV Level Regime × Opening-Gap Direction Result

## Authoritative execution

- Workflow: **36548607459**
- Branch: phase-52-same-session-atm-iv-gap-v1
- Artifact: **11023327699**
- Artifact SHA-256: **5c82311f78f1e952f6938527bfcc1b640cdba90e63ad079a65f8586c1f12cf74**

## Data integrity

- Study sessions: **1,228**
- Post-warm-up sessions: **1,168**
- Feature-eligible sessions: **1,148 / 1,168 = 98.29%**
- Same-session ATM-IV valid coverage: **1,156 / 1,168 = 98.97%**
- Expiry mapping: **100%**
- Prior-information violations: **0**
- Exact-expiry option files: **267**
- Execution coverage across all 12 true cells: **98.74%–100%**
- Base and Stress accounting: **reconciled**

Only 12 sessions lacked valid same-session ATM CE/PE quotes; the frozen 95% gate was comfortably cleared.

## True-cell results

| State | Mapping | Exit | Base mean/wk | Base median/wk | Base positive weeks | Stress mean/wk | Stress median/wk | Stress positive weeks |
|---|---|---|---:|---:|---:|---:|---:|---:|
| LOW_IV | CONTINUE | 10:30 | -₹420 | -₹388 | 35.3% | -₹514 | -₹472 | 32.6% |
| LOW_IV | CONTINUE | 15:10 | -₹275 | -₹389 | 39.7% | -₹370 | -₹435 | 39.1% |
| LOW_IV | FADE | 10:30 | -₹221 | -₹258 | 41.8% | -₹316 | -₹332 | 38.6% |
| LOW_IV | FADE | 15:10 | -₹421 | -₹405 | 39.7% | -₹515 | -₹485 | 36.4% |
| MID_IV | CONTINUE | 10:30 | -₹237 | -₹394 | 38.2% | -₹317 | -₹483 | 36.6% |
| MID_IV | CONTINUE | 15:10 | -₹402 | -₹430 | 40.8% | -₹481 | -₹470 | 38.2% |
| MID_IV | FADE | 10:30 | -₹214 | -₹170 | 41.9% | -₹294 | -₹260 | 39.3% |
| **MID_IV** | **FADE** | **15:10** | **₹47** | **-₹387** | **44.0%** | **-₹32** | **-₹432** | **42.9%** |
| HIGH_IV | CONTINUE | 10:30 | -₹298 | -₹558 | 36.0% | -₹383 | -₹588 | 35.0% |
| HIGH_IV | CONTINUE | 15:10 | -₹736 | -₹1,594 | 33.0% | -₹819 | -₹1,649 | 31.5% |
| HIGH_IV | FADE | 10:30 | -₹414 | -₹507 | 36.5% | -₹500 | -₹561 | 34.5% |
| HIGH_IV | FADE | 15:10 | -₹367 | -₹1,351 | 38.0% | -₹449 | -₹1,392 | 37.0% |

**0/12** true cells cleared the complete promotion gate.

The best Base cell, MID_IV / FADE / 15:10, was only **₹47/week mean** with a **negative median** and **44.0% positive weeks**. Under Stress it became **-₹32/week** with a negative median.

## Permutation-null comparison

For the best true cell:

Base true mean weekly net: **₹47**.

Five permutation-null means:
- seed 101: -₹74
- seed 202: -₹154
- seed 303: +₹69
- seed 404: -₹373
- seed 505: -₹241

Stress true mean weekly net: **-₹32**.

Five permutation-null means:
- seed 101: -₹151
- seed 202: -₹229
- seed 303: -₹5
- seed 404: -₹445
- seed 505: -₹316

The true state label is somewhat better than the average null in Base and Stress, but the absolute economics are nowhere near the weekly promotion threshold.

## Temporal stability

For the best cell, Base annual net was positive in 2021, 2024 and 2025 but negative in 2022, 2023 and 2026. Stress was negative in 2022, 2023, 2025 and 2026, with only 2021 and 2024 positive. The result therefore lacks robust cross-year after-cost stability.

## Decision

**CLOSED — NEGATIVE DISCOVERY.**

Same-session 09:30 ATM IV level provides no friction-robust weekly edge when crossed with opening-gap direction under the frozen one-lot debit-spread implementation.

No IV threshold, lookback, exit, direction mapping, expiry rule or cost-model retuning is authorized.

## Strengths

- 98.29% feature eligibility.
- 98.97% same-session ATM-IV quote coverage.
- 100% expiry mapping.
- Zero information-barrier violations.
- 12 finite true cells plus five fixed permutation nulls per cell.
- Base and doubled-slippage Stress with accounting reconciliation.

## Limitations

- The ATM IV state uses a simple CE/PE average and ignores skew and term-structure shape.
- The debit-spread execution still pays meaningful entry/exit friction.
- No WFA/OOS is justified because the discovery gate failed.
