# Phase 54 — Same-Session 09:30 Matched ATM IV Call-Put Spread × Opening Direction Result

## Authoritative execution

- Workflow: **36549550020**
- Branch: phase-54-same-session-atm-iv-spread-opening-v1
- Artifact: **11024192628**
- Artifact SHA-256: **5c982a5c14eb50962e9ef3eeceb2387ffbb652bd68677a88946790ebffe3629f**

## Data integrity

- Study sessions: **1,228**
- Post-warm-up sessions: **1,168**
- Feature-eligible sessions: **1,146 / 1,168 = 98.12%**
- Same-session matched ATM CE/PE IV valid coverage: **1,154 / 1,168 = 98.80%**
- Feature-expiry mapping: **100%**
- Prior-information violations: **0**
- Exact-expiry option files: **267**
- Execution coverage across all 12 true cells: **99.04%–100%**
- Base and Stress accounting: **reconciled**

## True-cell results

| State | Mapping | Exit | Base mean/wk | Base median/wk | Base positive weeks | Stress mean/wk | Stress median/wk | Stress positive weeks |
|---|---|---|---:|---:|---:|---:|---:|---:|
| LOW_SPREAD | CONTINUE | 10:30 | -₹282 | -₹314 | 40.2% | -₹376 | -₹418 | 37.4% |
| LOW_SPREAD | CONTINUE | 15:10 | -₹744 | -₹638 | 36.8% | -₹837 | -₹710 | 36.2% |
| LOW_SPREAD | FADE | 10:30 | -₹424 | -₹504 | 32.2% | -₹518 | -₹567 | 31.6% |
| **LOW_SPREAD** | **FADE** | **15:10** | **-₹49** | **-₹507** | **44.3%** | **-₹143** | **-₹547** | **43.7%** |
| MID_SPREAD | CONTINUE | 10:30 | -₹251 | -₹313 | 40.3% | -₹331 | -₹403 | 39.3% |
| MID_SPREAD | CONTINUE | 15:10 | -₹211 | -₹730 | 37.0% | -₹289 | -₹801 | 34.9% |
| MID_SPREAD | FADE | 10:30 | -₹292 | -₹348 | 40.6% | -₹371 | -₹419 | 38.5% |
| MID_SPREAD | FADE | 15:10 | -₹375 | -₹632 | 41.4% | -₹453 | -₹752 | 40.8% |
| HIGH_SPREAD | CONTINUE | 10:30 | -₹442 | -₹586 | 32.1% | -₹536 | -₹648 | 31.6% |
| HIGH_SPREAD | CONTINUE | 15:10 | -₹571 | -₹1,044 | 35.8% | -₹663 | -₹1,121 | 34.2% |
| HIGH_SPREAD | FADE | 10:30 | -₹195 | -₹289 | 42.6% | -₹290 | -₹365 | 38.9% |
| HIGH_SPREAD | FADE | 15:10 | -₹356 | -₹803 | 37.9% | -₹449 | -₹898 | 36.8% |

**0/12** true cells met the full promotion gate.

The best Base cell, LOW_SPREAD / FADE / 15:10, remained negative under Stress and had a strongly negative median and <45% positive weeks.

## Permutation-null comparison

For LOW_SPREAD / FADE / 15:10:

### Base
True mean weekly net: **-₹49**.

Five null means:
- seed 101: -₹484
- seed 202: -₹222
- seed 303: +₹42
- seed 404: -₹364
- seed 505: +₹65

Null average: **-₹192/week**.

### Stress
True mean weekly net: **-₹143**.

Five null means:
- seed 101: -₹561
- seed 202: -₹298
- seed 303: -₹35
- seed 404: -₹439
- seed 505: -₹12

Null average: **-₹269/week**.

The true state modestly outperformed the matched null average, but the absolute economics remained negative and far below the ₹5,000/week promotion gate.

## Temporal stability

For the best cell:
- Base annual net was positive in 2021, 2022, 2024 and 2026, but strongly negative in 2023 and 2025.
- Stress annual net was positive only in 2021 and 2026; it was negative in 2022–2025.

The result therefore lacks robust cross-year stability.

## Decision

**CLOSED — NEGATIVE DISCOVERY.**

Matched-strike same-session ATM IV put-call spread does not produce a friction-robust weekly edge when used to condition opening-gap continuation/reversal under the frozen one-lot debit-spread implementation.

No post-result changes to spread definition, 60-session history, percentile boundaries, expiry rule, gap mapping, execution times, spread width or cost model are authorized.

## Strengths

- 98.12% feature eligibility.
- 98.80% matched ATM CE/PE IV coverage.
- 100% feature-expiry mapping.
- Zero information-barrier violations.
- 12 finite true cells plus five permutation nulls per cell.
- Base and doubled-slippage Stress with accounting reconciliation.

## Limitations

- The feature captures only matched ATM IV asymmetry, not the full surface or term structure.
- The 09:31 debit-spread implementation remains friction-sensitive.
- No WFA/OOS is justified after discovery failure.
