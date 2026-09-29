# Phase 55 — Same-Session 09:30 IV Smile Curvature × Opening Direction Result

## Authoritative execution

- Workflow: **36550200125**
- Branch: phase-55-same-session-smile-curvature-opening-v1
- Artifact: **11023749886**
- Artifact SHA-256: **c0c54fc133755a6d95c3fe4221913bb42dea12d054971a8fbeac58c41ba628ea**

## Data integrity

- Study sessions: **1,228**
- Post-warm-up sessions: **1,168**
- Feature-eligible sessions: **1,144 / 1,168 = 97.95%**
- 09:30 smile-curvature valid sessions: **1,152 / 1,168 = 98.63%**
- Feature-expiry mapping: **100%**
- Prior-information violations: **0**
- Exact-expiry option files: **267**
- Execution coverage: **99.26%–100%** across all 12 true cells
- Base/Stress accounting: **reconciled**

## True-cell results

All 12 frozen cells were negative under both Base and Stress.

Best cell across both frictions: **HIGH_CURVATURE / FADE / 15:10**

### Base
- Mean weekly net: **-₹59.85**
- Median weekly net: **-₹563.60**
- Positive-week rate: **42.08%**
- Total net P&L: **-₹12,090**
- Max drawdown: **-₹68,083**

### Stress
- Mean weekly net: **-₹141.33**
- Median weekly net: **-₹603.58**
- Positive-week rate: **42.08%**
- Total net P&L: **-₹28,548**
- Max drawdown: **-₹74,826**

## Best-cell permutation-null comparison

Base null mean weekly nets: -₹502.18, -₹518.79, -₹446.35, -₹322.71, -₹340.93. Null average: **-₹426.19/week**.

Stress null mean weekly nets: -₹581.32, -₹593.17, -₹525.83, -₹401.95, -₹421.36. Null average: **-₹504.73/week**.

The true curvature state materially outperforms the matched permutation-null average, but the absolute after-cost result remains negative. This is not a tradable edge.

## Decision

**CLOSED — NEGATIVE DISCOVERY.**

No post-result changes to smile definition, moneyness, lookback, percentile thresholds, expiry selection, direction mapping, entry/exit, spread width or cost model are authorized.

## Strengths

- 97.95% post-warm-up feature eligibility.
- 98.63% same-session smile-input coverage.
- Zero prior-information violations.
- 100% feature-expiry mapping.
- 12 finite cells plus 5 permutation nulls per cell.
- Historical lot sizes and realistic Base/Stress friction.
- Every true cell above the 95% execution-coverage floor.
- Full accounting reconciliation.

## Limitation

The feature measures only local three-strike smile curvature. It does not measure the full volatility surface or term structure.
