# Phase 50 — Opening Location Relative to Prior Range × Gap Direction Result

## Authoritative execution

- Workflow: **36539948879**
- Branch: phase-50-opening-location-range-gap-v1
- Artifact: **11019976395**
- Artifact SHA-256: **4fb748002689619723a9a38a653ce40360314256d97f584edccffbbe4c56e3cf**

## Data integrity

- Study sessions: **1,228**
- Feature-eligible sessions: **1,219 / 1,228 = 99.267%**
- Prior-range validity: **100%** among eligible sessions
- Expiry mapping: **100%**
- Prior-information violations: **0**
- Execution coverage: **98.6%–100%** across all 12 true cells
- Base/Stress accounting: reconciled

## True-cell results

| State | Mapping | Exit | Base mean/wk | Base median/wk | Base positive weeks | Stress mean/wk | Stress median/wk | Stress positive weeks |
|---|---|---|---:|---:|---:|---:|---:|---:|
| INSIDE_RANGE | CONTINUE | 10:30 | -₹413 | -₹423 | 33.3% | -₹461 | -₹463 | 33.3% |
| INSIDE_RANGE | CONTINUE | 15:10 | -₹683 | -₹988 | 33.3% | -₹730 | -₹1,028 | 31.3% |
| INSIDE_RANGE | FADE | 10:30 | -₹43 | -₹153 | 41.7% | -₹91 | -₹190 | 39.6% |
| **INSIDE_RANGE** | **FADE** | **15:10** | **+₹163** | **-₹0** | **50.0%** | **+₹116** | **-₹30** | **50.0%** |
| ABOVE_RANGE | CONTINUE | 10:30 | -₹438 | -₹444 | 33.9% | -₹564 | -₹567 | 32.7% |
| ABOVE_RANGE | CONTINUE | 15:10 | -₹550 | -₹1,183 | 36.1% | -₹674 | -₹1,257 | 36.1% |
| ABOVE_RANGE | FADE | 10:30 | -₹378 | -₹443 | 35.7% | -₹504 | -₹513 | 33.0% |
| ABOVE_RANGE | FADE | 15:10 | -₹391 | -₹913 | 41.3% | -₹515 | -₹1,033 | 40.1% |
| BELOW_RANGE | CONTINUE | 10:30 | -₹278 | -₹456 | 37.7% | -₹359 | -₹486 | 36.8% |
| BELOW_RANGE | CONTINUE | 15:10 | -₹378 | -₹1,029 | 36.3% | -₹458 | -₹1,064 | 34.9% |
| BELOW_RANGE | FADE | 10:30 | -₹353 | -₹208 | 43.4% | -₹435 | -₹298 | 41.0% |
| BELOW_RANGE | FADE | 15:10 | -₹362 | -₹337 | 44.3% | -₹443 | -₹391 | 42.9% |

The best cell was **INSIDE_RANGE / FADE / 15:10**:
- Base: **+₹163.39/week**, median **-₹0.09**, 50.0% positive weeks.
- Stress: **+₹116.07/week**, median **-₹30.08**, 50.0% positive weeks.

This is far below the ₹5,000/week promotion requirement and fails the median/positive-week consistency requirements.

## Null comparison

For INSIDE_RANGE / FADE / 15:10:

Base matched permutation-null means were approximately -₹191, -₹380, -₹45, +₹118 and -₹999; the null average was about **-₹300/week**.

Stress matched null means were approximately -₹236, -₹424, -₹89, +₹71 and -₹1,048; the null average was about **-₹345/week**.

The true cell outperformed the matched-null average, but the absolute economics were negligible.

## Decision

**CLOSED — NEGATIVE DISCOVERY.**

Opening location relative to the prior session's range does not provide a sufficiently strong after-cost weekly edge in the frozen NIFTY debit-spread implementation.

No post-result changes to the state definitions, gap mapping, exits, spread width, expiry rule or cost model are authorized.

No WFA/OOS is authorized.
