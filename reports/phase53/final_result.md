# Phase 53 — Same-Session 09:30 Near-ATM IV Skew × Opening Direction Result

## Authoritative execution

- Workflow: **36549121608**
- Branch: phase-53-near-atm-iv-skew-gap-v1
- Artifact: **11023737870**
- Artifact SHA-256: **758c8e96b6b73ac9930a83f07cd8127678ca3f499110cefc3573b552f4e56fc3**

## Data integrity

- Study sessions: **1,228**
- Post-warm-up sessions: **1,168**
- Feature-eligible sessions: **1,148 / 1,168 = 98.29%**
- Same-session near-ATM skew valid coverage: **1,156 / 1,168 = 98.97%**
- Expiry mapping: **100%**
- Prior-information violations: **0**
- Exact-expiry option files: **267**
- Execution coverage across all 12 true cells: **98.79%–100%**
- Base and Stress accounting: **reconciled**
- All five permutation-null blocks completed for each true cell.

## True-cell results

| State | Mapping | Exit | Base mean/wk | Base median/wk | Base positive weeks | Stress mean/wk | Stress median/wk | Stress positive weeks |
|---|---|---|---:|---:|---:|---:|---:|---:|
| LOW_SKEW | CONTINUE | 10:30 | -₹456 | -₹555 | 31.0% | -₹553 | -₹620 | 28.8% |
| LOW_SKEW | CONTINUE | 15:10 | -₹622 | -₹642 | 41.6% | -₹718 | -₹728 | 41.1% |
| **LOW_SKEW** | **FADE** | **10:30** | **-₹138** | **-₹196** | **44.9%** | **-₹235** | **-₹258** | **42.7%** |
| LOW_SKEW | FADE | 15:10 | -₹257 | -₹695 | 37.8% | -₹354 | -₹735 | 37.3% |
| MID_SKEW | CONTINUE | 10:30 | -₹216 | -₹327 | 39.4% | -₹292 | -₹414 | 37.9% |
| MID_SKEW | CONTINUE | 15:10 | -₹342 | -₹645 | 36.4% | -₹418 | -₹720 | 35.9% |
| MID_SKEW | FADE | 10:30 | -₹371 | -₹379 | 37.4% | -₹447 | -₹427 | 34.3% |
| MID_SKEW | FADE | 15:10 | -₹169 | -₹216 | 46.0% | -₹245 | -₹256 | 44.9% |
| HIGH_SKEW | CONTINUE | 10:30 | -₹307 | -₹321 | 41.1% | -₹399 | -₹393 | 38.9% |
| HIGH_SKEW | CONTINUE | 15:10 | -₹505 | -₹1,166 | 38.9% | -₹594 | -₹1,201 | 38.9% |
| HIGH_SKEW | FADE | 10:30 | -₹362 | -₹543 | 33.3% | -₹454 | -₹618 | 31.7% |
| HIGH_SKEW | FADE | 15:10 | -₹340 | -₹1,176 | 37.2% | -₹429 | -₹1,312 | 36.1% |

**0/12** true cells met the full promotion gate.

The best Base cell, LOW_SKEW / FADE / 10:30, remained negative in Stress and had a negative median and <45% positive weeks.

## Permutation-null comparison

For LOW_SKEW / FADE / 10:30:

### Base
True mean weekly net: **-₹138**.

Five null means:
- seed 101: -₹174
- seed 202: -₹249
- seed 303: -₹239
- seed 404: -₹114
- seed 505: -₹265

Null mean: **-₹208/week**.

### Stress
True mean weekly net: **-₹235**.

Five null means:
- seed 101: -₹255
- seed 202: -₹332
- seed 303: -₹319
- seed 404: -₹199
- seed 505: -₹348

Null mean: **-₹291/week**.

The true state modestly outperformed the matched null average, but the absolute economics remained clearly negative and far below the ₹5,000/week gate.

## Temporal stability

For the best cell:
- Base annual net was negative in 2021, 2022, 2023, 2024 and 2026; only 2025 was positive.
- Stress annual net was negative in 2021, 2022, 2023, 2024 and 2026; only 2025 was positive.

This rules out treating the small null-relative improvement as a robust cross-year trading edge.

## Decision

**CLOSED — NEGATIVE DISCOVERY.**

Same-session near-ATM IV skew, in this frozen form, does not produce a friction-robust weekly edge when used to condition opening-gap continuation versus reversal.

No post-result changes to skew definition, strike offsets, 60-session lookback, percentile boundaries, exit times, gap mapping, expiry rule or cost model are authorized.

## Strengths

- 98.29% feature eligibility.
- 98.97% near-ATM skew coverage.
- 100% expiry mapping.
- Zero information-barrier violations.
- 12 finite true cells plus five permutation nulls per cell.
- Base and doubled-slippage Stress with full accounting reconciliation.

## Limitations

- The skew measure uses only one near-ATM put and one near-ATM call rather than the full smile.
- The 09:31 debit-spread implementation remains friction-sensitive.
- No WFA/OOS is justified after discovery failure.
