# Phase 53 — Same-Session 09:30 Near-ATM IV Skew × Opening Direction Result

## Authoritative execution

- Workflow: **36548991737**
- Branch: phase-53-near-atm-iv-skew-opening-v1
- Artifact: **11024002184**
- Artifact SHA-256: **88f6fe5cc5a53f3fac7ed103f466f16388dc84cd59edbf59fbebdf3b0ab36431**

## Data integrity

- Study sessions: **1,228**
- Post-warm-up sessions: **1,168**
- Feature-eligible sessions: **1,144 / 1,168 = 97.95%**
- 09:30 skew-valid sessions: **1,152 / 1,168 = 98.63%**
- Feature-expiry mapping: **100%**
- Prior-information violations: **0**
- Exact-expiry files: **267**
- Execution coverage across true cells: **99.26%–100%**
- Base and Stress accounting: **reconciled**

The 16 missing OTM-put/call 09:30 quote pairs were excluded; the frozen 95% gate passed.

## Frozen true-cell results

| Skew state | Mapping | Exit | Base mean/wk | Base median/wk | Base positive weeks | Stress mean/wk | Stress median/wk | Stress positive weeks |
|---|---|---|---:|---:|---:|---:|---:|---:|
| LOW_SKEW | CONTINUE | 10:30 | -₹393 | -₹567 | 34.6% | -₹486 | -₹616 | 33.5% |
| LOW_SKEW | CONTINUE | 15:10 | -₹487 | -₹1,174 | 33.5% | -₹578 | -₹1,199 | 33.0% |
| LOW_SKEW | FADE | 10:30 | -₹203 | -₹243 | 45.0% | -₹297 | -₹294 | 40.8% |
| LOW_SKEW | FADE | 15:10 | -₹353 | -₹851 | 39.8% | -₹445 | -₹926 | 38.7% |
| MID_SKEW | CONTINUE | 10:30 | -₹297 | -₹318 | 38.6% | -₹374 | -₹362 | 36.5% |
| MID_SKEW | CONTINUE | 15:10 | -₹524 | -₹848 | 34.5% | -₹599 | -₹911 | 33.0% |
| MID_SKEW | FADE | 10:30 | -₹254 | -₹371 | 38.6% | -₹330 | -₹424 | 37.6% |
| **MID_SKEW** | **FADE** | **15:10** | **-₹177** | **-₹758** | **39.1%** | **-₹253** | **-₹848** | **39.1%** |
| HIGH_SKEW | CONTINUE | 10:30 | -₹260 | -₹281 | 41.8% | -₹352 | -₹366 | 39.6% |
| HIGH_SKEW | CONTINUE | 15:10 | -₹452 | -₹475 | 42.9% | -₹542 | -₹541 | 42.3% |
| HIGH_SKEW | FADE | 10:30 | -₹429 | -₹399 | 33.0% | -₹521 | -₹450 | 31.9% |
| HIGH_SKEW | FADE | 15:10 | -₹250 | -₹660 | 40.1% | -₹341 | -₹711 | 39.0% |

**0/12** cells met the complete promotion gate.

## Best-cell permutation-null comparison

For **MID_SKEW / FADE / 15:10**:

Base null mean weekly P&L:
- Seed 101: -₹272
- Seed 202: -₹253
- Seed 303: -₹82
- Seed 404: -₹2
- Seed 505: -₹335
- Null mean: **-₹189**

Stress null mean weekly P&L:
- Seed 101: -₹347
- Seed 202: -₹330
- Seed 303: -₹160
- Seed 404: -₹78
- Seed 505: -₹413
- Null mean: **-₹266**

The true cell is only modestly better than the matched null average and remains substantially negative after realistic friction. The result therefore does not support an economically exploitable skew edge.

## Decision

**CLOSED — NEGATIVE DISCOVERY.**

Near-ATM same-session IV skew does not generate a robust after-cost opening-direction strategy under the frozen execution model.

No post-result change to the ±₹100 skew legs, 60-session history, tercile boundaries, feature expiry, execution expiry, direction mapping, entry, exits, spread width or cost model is authorized.

## Strengths

- 97.95% feature eligibility after warm-up.
- 98.63% same-session skew quote/IV coverage.
- 100% feature-expiry mapping.
- Zero prior-information violations.
- 12 frozen cells plus 5 permutation nulls per cell.
- Base and doubled-slippage Stress.
- Historical lot sizes and established transaction-cost model.
- Full accounting reconciliation.

## Limitations

- Skew is defined using only one OTM put and one OTM call at fixed ±₹100 moneyness.
- It does not capture the broader smile or term structure.
- Option quote quality can affect IV inversion.
- No WFA/OOS is justified because the frozen discovery gate failed.
