# Phase 52 — Same-Session 09:30 ATM IV Level Regime × Opening Direction Result

## Authoritative execution
- Workflow: **36548301179**
- Branch: phase-52-current-atm-iv-regime-opening-v1
- Artifact: **11023562027**
- Artifact SHA-256: **a3207be3c9883c11248c422de622c3202c81a340998ed530bfcc6193ce3ca406**

## Data integrity
- Study sessions: **1,228**
- Post-warm-up sessions: **1,168**
- Feature-eligible sessions: **1,146 / 1,168 = 98.12%**
- 09:30 ATM IV valid: **1,154 / 1,168 = 98.80%**
- Feature-expiry mapping: **100%**
- Prior-information violations: **0**
- Exact-expiry files: **267**
- Execution coverage: **98.80%–100%** across the 12 cells
- Base/Stress accounting: **reconciled**

## True-cell discovery

All 12 frozen cells were negative under both friction regimes.

The strongest Base cell was **MID_IV / FADE / 15:10**:
- Base mean weekly net: **-₹100.61**
- Base median weekly net: **-₹498.78**
- Base positive-week rate: **46.59%**
- Base total net: **-₹17,707**
- Base max drawdown: **-₹36,508**

Stress for the same cell:
- Stress mean weekly net: **-₹182.60**
- Stress median weekly net: **-₹568.74**
- Stress positive-week rate: **45.45%**
- Stress total net: **-₹32,137**
- Stress max drawdown: **-₹40,673**

Best Base cell remained negative in 5 of 6 calendar years; 2024 was positive while 2021–2023 and 2025 were negative. Stress was negative in every calendar year except 2024.

Other notable Base cells:
- LOW_IV / FADE / 10:30: -₹142/week
- MID_IV / FADE / 10:30: -₹305/week
- HIGH_IV / FADE / 15:10: -₹375/week
- HIGH_IV / CONTINUE / 10:30: -₹377/week
- HIGH_IV / FADE / 10:30: -₹566/week

No cell met the ₹5,000 mean + median + 70% positive-week gate in either friction regime.

## Decision

**CLOSED — NEGATIVE DISCOVERY.**

The absolute 09:30 ATM IV level did not produce a viable after-cost directional regime when crossed with opening-direction FOLLOW/FADE.

The negative result is stronger than the Phase 51 data-limited result because same-session ATM IV coverage is 98.80%, comfortably above the frozen 95% gate, and the full Base/Stress discovery completed cleanly.

No WFA/OOS is authorized. No IV threshold, percentile boundary, mapping, exit, spread width or cost-model tuning is authorized.

## Statistical interpretation

The best cell modestly outperformed some random permutation-null configurations, but its absolute expectancy was still economically negative. The null comparison does not rescue the strategy because the preregistered economic promotion gate is the controlling criterion.

## Strengths
- Same-session 09:30 IV is available before the 09:31 entry.
- 98.80% IV coverage and 98.12% final feature eligibility.
- Zero information-barrier violations.
- Historical expiry/lot handling and realistic Base/Stress costs.
- 12 fixed cells and 5 fixed permutation nulls per cell.
- Full artifact/accounting validation passed.

## Limitations
- ATM IV uses only the nearest current expiry and simple CE/PE averaging.
- IV skew, term structure and smile information are intentionally excluded here and belong to separate hypotheses.
- No WFA/OOS follows a failed discovery gate.
