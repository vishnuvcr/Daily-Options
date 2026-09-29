# Phase 57 — 09:15–09:30 Opening-Range Volatility Regime × Opening-Gap Direction Result

## Authoritative execution

- Workflow: **36551911099**
- Branch: phase-57-opening-range-vol-gap-v1
- Artifact: **11025372329**
- Artifact SHA-256: **c0714aa3f31d39ade17fb2ec5e2f6a55aaa4c826c9679739ac39b8a3b249f9b4**

## Data integrity

- Study sessions: **1,228**
- Post-warm-up sessions: **1,168**
- Feature-eligible sessions: **1,159 / 1,168 = 99.229%**
- Prior-range coverage among eligible sessions: **100%**
- Complete 09:15–09:29 opening-range coverage: **100%**
- Regime coverage: **100%**
- Expiry mapping: **100%**
- Prior-information violations: **0**
- Exact-expiry files: **267**
- Execution coverage: **97.82%–99.72%**
- Base and Stress accounting: **reconciled**

## Frozen true-cell results

| Opening-range state | Mapping | Exit | Base mean/wk | Base median/wk | Base positive weeks | Stress mean/wk | Stress median/wk | Stress positive weeks |
|---|---|---|---:|---:|---:|---:|---:|---:|
| LOW_OPEN_RANGE | CONTINUE | 10:30 | -₹372 | -₹436 | 37.7% | -₹457 | -₹495 | 35.3% |
| LOW_OPEN_RANGE | CONTINUE | 15:10 | -₹761 | -₹860 | 34.8% | -₹844 | -₹912 | 34.3% |
| LOW_OPEN_RANGE | **FADE** | 10:30 | -₹231 | -₹232 | 42.2% | -₹316 | -₹289 | 40.2% |
| **LOW_OPEN_RANGE** | **FADE** | **15:10** | **-₹88** | **-₹464** | **41.7%** | **-₹172** | **-₹521** | **41.2%** |
| MID_OPEN_RANGE | CONTINUE | 10:30 | -₹243 | -₹302 | 36.4% | -₹319 | -₹382 | 34.0% |
| MID_OPEN_RANGE | CONTINUE | 15:10 | -₹251 | -₹624 | 40.8% | -₹325 | -₹706 | 39.3% |
| MID_OPEN_RANGE | FADE | 10:30 | -₹224 | -₹222 | 39.8% | -₹300 | -₹285 | 37.9% |
| MID_OPEN_RANGE | FADE | 15:10 | -₹368 | -₹691 | 42.2% | -₹443 | -₹755 | 41.3% |
| HIGH_OPEN_RANGE | CONTINUE | 10:30 | -₹282 | -₹418 | 36.7% | -₹365 | -₹521 | 34.7% |
| HIGH_OPEN_RANGE | CONTINUE | 15:10 | -₹331 | -₹1,011 | 37.0% | -₹413 | -₹1,078 | 37.0% |
| HIGH_OPEN_RANGE | FADE | 10:30 | -₹354 | -₹298 | 42.5% | -₹437 | -₹376 | 40.0% |
| HIGH_OPEN_RANGE | FADE | 15:10 | -₹245 | -₹501 | 45.7% | -₹328 | -₹616 | 44.7% |

**0/12** cells passed the complete dual-friction promotion gate.

## Best-cell economics

For **LOW_OPEN_RANGE / FADE / 15:10**:

### Base
- Total net: **-₹18,045**
- Mean weekly net: **-₹88.46**
- Median weekly net: **-₹463.71**
- Positive-week rate: **41.67%**
- Max drawdown: **-₹55,604**
- Worst trade: **-₹5,752**
- Raw gross P&L: **+₹43,528**
- Slippage cost: **₹17,284**
- Transaction costs: **₹44,289**

### Stress
- Total net: **-₹35,162**
- Mean weekly net: **-₹172.36**
- Median weekly net: **-₹520.70**
- Positive-week rate: **41.18%**
- Max drawdown: **-₹64,824**
- Worst trade: **-₹5,812**
- Raw gross P&L: **+₹43,528**
- Slippage cost: **₹34,410**
- Transaction costs: **₹44,281**

The opening-range state produced positive gross P&L in the best cell, but realistic friction converted it to a net loss.

## Best-cell permutation-null comparison

For LOW_OPEN_RANGE / FADE / 15:10:

### Base
Null mean weekly net:
- 101: -₹108
- 202: -₹261
- 303: -₹185
- 404: -₹223
- 505: -₹287
- Null average: **-₹213**

True cell: **-₹88/week**.

### Stress
Null mean weekly net:
- 101: -₹192
- 202: -₹345
- 303: -₹265
- 404: -₹306
- 505: -₹369
- Null average: **-₹295**

True cell: **-₹172/week**.

The true cell outperformed the average permutation-null result, but absolute after-cost expectancy remained negative and the median/positive-week gates failed.

## Calendar stability

Best-cell mean weekly net by year:

| Year | Base | Stress |
|---|---:|---:|
| 2021 | +₹110 | +₹34 |
| 2022 | +₹465 | +₹384 |
| 2023 | -₹174 | -₹249 |
| 2024 | +₹226 | +₹160 |
| 2025 | -₹484 | -₹594 |
| 2026 available | -₹1,118 | -₹1,213 |

Positive early years do not persist into 2025–2026.

## Decision

**CLOSED — NEGATIVE DISCOVERY.**

The 09:15–09:29 opening-range volatility regime does not produce a robust after-cost opening-gap strategy under the frozen execution model.

No post-result change to the opening-range window, normalization ratio, 60-session history, tercile boundaries, gap mapping, entry, exits, expiry, spread width, or cost model is authorized.

## Strengths

- 99.229% feature eligibility.
- 100% opening-range and prior-range coverage.
- Zero prior-information violations.
- 12 frozen cells plus 5 permutation nulls per cell.
- Historical lots, Base/Stress slippage, full transaction-cost model.
- Accounting reconciliation.

## Limitations

- The opening-range state is a simple volatility-context variable; it does not capture direction within the range.
- The 09:15–09:29 range is still correlated with the broader opening-gap/early-volatility family already tested.
- No WFA/OOS is justified because no discovery cell cleared the promotion gate.
