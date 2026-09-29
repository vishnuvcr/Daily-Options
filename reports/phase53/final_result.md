# Phase 53 — Same-Session 09:30 ATM IV Skew Regime × Opening Direction Result

## Authoritative execution
- Workflow: **36548853266**
- Branch: phase-53-atm-iv-skew-opening-v1
- Artifact: **11023447986**
- Artifact SHA-256: **eee53f79b1db9c4a193c36df1d93b9f65c7dd7003793a698e539af368aab0eaa**

## Data integrity
- Study sessions: **1,228**
- Post-warm-up sessions: **1,168**
- Feature-eligible sessions: **1,146 / 1,168 = 98.12%**
- Same-session ATM skew valid: **1,154 / 1,168 = 98.80%**
- Feature-expiry mapping: **100%**
- Prior-information violations: **0**
- Execution coverage: **99.04%–100%** across all 12 cells
- Base/Stress accounting: reconciled

## Discovery result

All 12 frozen cells were negative under both Base and Stress.

Best Base cell:
**HIGH_SKEW / FADE / 15:10**
- Base mean weekly net: **-₹49.18**
- Base median weekly net: **-₹506.69**
- Base positive-week rate: **44.25%**
- Base total net: **-₹8,558**
- Base max drawdown: **-₹55,375**

Stress for the same cell:
- Stress mean weekly net: **-₹142.70**
- Stress median weekly net: **-₹546.67**
- Stress positive-week rate: **43.68%**
- Stress total net: **-₹24,830**
- Stress max drawdown: **-₹61,591**

Matched permutation-null means for this cell were approximately:
- Base: -₹192/week average across the five fixed nulls.
- Stress: -₹269/week average across the five fixed nulls.

The real skew state therefore outperformed its null average, but the absolute expectancy was still negative and far below the ₹5,000/week promotion gate.

## Decision

**CLOSED — NEGATIVE DISCOVERY.**

Same-session ATM put-minus-call IV skew contains some descriptive information relative to randomized labels, but not enough to overcome option execution costs or meet the economic target.

No WFA/OOS is authorized. No post-result skew threshold, percentile, mapping, exit, spread or cost tuning is permitted.

## Strengths
- 98.80% same-session skew coverage.
- 98.12% final feature eligibility.
- Zero information-barrier violations.
- 12 fixed cells plus 5 permutation nulls per cell.
- Historical expiries/lots and Base/Stress friction.
- Full artifact validation and accounting reconciliation.

## Limitations
- Skew is an ATM CE-vs-PE IV difference rather than a full volatility-surface risk-neutral skew measure.
- The exact predictive relationship described in much of the literature is longer-horizon than this intraday test.
- No WFA/OOS follows a failed discovery gate.
