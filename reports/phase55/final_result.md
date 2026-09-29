# Phase 55 — Same-Session 09:30 IV Smile Curvature / Wing Richness × Opening Direction Result

## Authoritative execution

- Workflow: **36550214228**
- Branch: phase-55-iv-curvature-opening-v1
- Artifact: **11023369823**
- Artifact SHA-256: **01de8b9eab36ea8969dba577146c1502b3a23b3ea3083ba4acbd34451128b036**

## Data integrity

- Study sessions: **1,228**
- Post-warm-up sessions: **1,168**
- Feature-eligible sessions: **1,144 / 1,168 = 97.95%**
- 09:30 curvature-valid sessions: **1,152 / 1,168 = 98.63%**
- Feature-expiry mapping: **100%**
- Prior-information violations: **0**
- Exact-expiry files: **267**
- Execution coverage across true cells: **99.73%–100%**
- Base and Stress accounting: **reconciled**

## Frozen true-cell results

The best cell under both frictions was **HIGH_CURVATURE / FADE / 15:10**:

- Base mean weekly net: **-₹105.32**
- Base median weekly net: **-₹602.85**
- Base positive-week rate: **41.50%**
- Base total net: **-₹21,064**
- Base max drawdown: **-₹82,278**
- Base raw gross P&L: **+₹34,922**
- Base slippage: **₹16,044**
- Base transaction costs: **₹39,942**

Stress:
- Mean weekly net: **-₹185.35**
- Median weekly net: **-₹632.83**
- Positive-week rate: **41.00%**
- Total net: **-₹37,070**
- Max drawdown: **-₹88,485**
- Raw gross P&L: **+₹34,922**
- Slippage: **₹32,058**
- Transaction costs: **₹39,934**

No cell cleared the complete dual-friction promotion gate.

## Best-cell permutation-null comparison

For HIGH_CURVATURE / FADE / 15:10:

Base null mean weekly P&L:
- Seed 101: -₹439
- Seed 202: -₹363
- Seed 303: +₹88
- Seed 404: -₹549
- Seed 505: -₹446
- Null average: **-₹342**

Stress null mean weekly P&L:
- Seed 101: -₹516
- Seed 202: -₹439
- Seed 303: +₹12
- Seed 404: -₹627
- Seed 505: -₹523
- Null average: **-₹419**

The true cell is modestly better than the mean permutation-null result, but its absolute after-cost expectancy remains negative and its median/positive-week gates fail.

## Calendar stability

Best-cell Base mean weekly P&L:
- 2021: +₹163
- 2022: +₹313
- 2023: +₹107
- 2024: -₹97
- 2025: -₹1,253
- 2026 available: +₹1,033

Stress:
- 2021: +₹116
- 2022: +₹240
- 2023: +₹36
- 2024: -₹155
- 2025: -₹1,365
- 2026 available: +₹906

The positive effect is not stable across regimes; the 2025 loss more than offsets the earlier positive years.

## Decision

**CLOSED — NEGATIVE DISCOVERY.**

Local IV-smile curvature/wing richness does not create a robust after-cost opening-direction strategy under the frozen execution model.

No post-result changes to the ±₹100 wings, 60-session history, terciles, IV inversion, expiry, direction mapping, entry, exits, spread width, or cost model are authorized.

## Strengths

- 97.95% feature eligibility.
- 98.63% same-session ATM/wing IV coverage.
- 100% feature-expiry mapping.
- Zero prior-information violations.
- 12 true cells plus 5 permutation nulls per cell.
- Historical lots, Base/Stress slippage, full transaction-cost model.
- Accounting reconciliation.

## Limitations

- Curvature uses only three moneyness points: ATM and two fixed ±₹100 wings.
- It does not capture the full volatility surface.
- The same 09:30 option-surface information is not enough to overcome execution costs for the tested debit-spread implementation.
- No WFA/OOS is justified because no discovery cell cleared the promotion gate.
