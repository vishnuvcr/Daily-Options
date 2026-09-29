# Phase 54 — Same-Session 09:30 Matched ATM IV Call-Put Spread × Opening Direction Result

## Authoritative execution
- Workflow: **36549521888**
- Branch: phase-54-matched-atm-iv-call-put-opening-v1
- Artifact: **11023594728**
- Artifact SHA-256: **7ac1405b75489160e23bcad760dcec81557a23fd5438c53834ef63206927307f**

## Data integrity
- Study sessions: **1,228**
- Post-warm-up sessions: **1,168**
- Feature-eligible sessions: **1,146 / 1,168 = 98.12%**
- Matched 09:30 ATM CE/PE IV coverage: **1,154 / 1,168 = 98.80%**
- Feature-expiry mapping: **100%**
- Prior-information violations: **0**
- Execution coverage: **99.04%–100%** across all 12 cells
- Base/Stress accounting: reconciled

## True-cell results

| State | Mapping | Exit | Base mean/wk | Base median/wk | Base positive weeks | Stress mean/wk | Stress median/wk | Stress positive weeks |
|---|---|---|---:|---:|---:|---:|---:|---:|
| HIGH_SPREAD | FADE | 15:10 | **-₹49** | -₹507 | 44.3% | **-₹143** | -₹547 | 43.7% |
| LOW_SPREAD | FADE | 10:30 | -₹195 | -₹289 | 42.6% | -₹290 | -₹365 | 38.9% |
| MID_SPREAD | CONTINUE | 15:10 | -₹211 | -₹730 | 37.0% | -₹289 | -₹801 | 34.9% |
| MID_SPREAD | CONTINUE | 10:30 | -₹251 | -₹313 | 40.3% | -₹331 | -₹403 | 39.3% |
| HIGH_SPREAD | CONTINUE | 10:30 | -₹282 | -₹314 | 40.2% | -₹376 | -₹418 | 37.4% |
| MID_SPREAD | FADE | 10:30 | -₹292 | -₹348 | 40.6% | -₹371 | -₹419 | 38.5% |
| LOW_SPREAD | FADE | 15:10 | -₹356 | -₹803 | 37.9% | -₹449 | -₹898 | 36.8% |
| MID_SPREAD | FADE | 15:10 | -₹375 | -₹632 | 41.4% | -₹453 | -₹752 | 40.8% |
| HIGH_SPREAD | FADE | 10:30 | -₹424 | -₹504 | 32.2% | -₹518 | -₹567 | 31.6% |
| LOW_SPREAD | CONTINUE | 10:30 | -₹442 | -₹586 | 32.1% | -₹536 | -₹648 | 31.6% |
| LOW_SPREAD | CONTINUE | 15:10 | -₹571 | -₹1,044 | 35.8% | -₹663 | -₹1,121 | 34.2% |
| HIGH_SPREAD | CONTINUE | 15:10 | -₹744 | -₹638 | 36.8% | -₹837 | -₹710 | 36.2% |

**0/12** cells cleared the promotion gate.

## Best-cell permutation null

For HIGH_SPREAD / FADE / 15:10:

Base true mean: **-₹49/week**. Five null means: -₹484, -₹222, +₹42, -₹364, +₹65. Null average: **-₹192/week**.

Stress true mean: **-₹143/week**. Five null means: -₹561, -₹298, -₹35, -₹439, -₹12. Null average: **-₹269/week**.

The true state modestly outperformed the average randomized-label benchmark, but both true and null economics remained negative.

## Decision

**CLOSED — NEGATIVE DISCOVERY.**

Matched-strike ATM put-versus-call IV asymmetry does not produce a viable after-cost opening-direction strategy under the frozen 09:31/10:30/15:10 debit-spread execution.

No WFA/OOS is authorized. No post-result skew/spread threshold, mapping, timing, moneyness, spread width or cost-model tuning is permitted.

## Strengths
- 98.12% feature eligibility and 98.80% matched ATM IV coverage.
- Zero prior-information violations.
- Exact expiry/lot handling.
- 12 fixed cells plus 5 state-permutation nulls per cell.
- Base/Stress friction and full accounting reconciliation.

## Limitations
- The spread is a simple matched-strike IV difference rather than a full volatility-surface skew measure.
- The phase intentionally does not condition on IV term structure, smile slope or option-flow variables.
- No WFA/OOS follows a failed discovery gate.
