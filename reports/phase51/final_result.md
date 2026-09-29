# Phase 51 — Prior-Session ATM IV Level Regime × Opening-Gap Direction Result

## Authoritative execution

- Workflow: **36540501382**
- Branch: phase-51-prior-atm-iv-regime-gap-v1
- Artifact: **11020206536**
- Artifact SHA-256: **c2ecc67b4173d8152f1c528250d67920ccf6bbbcf8b0ddad5258d6b87bfd569c**

## Data gate

The preregistered 95% coverage gate **did not pass**.

- Raw 09:30 NIFTY sessions: **1,228**
- Post-warm-up sessions: **1,168**
- Prior-session ATM IV valid: **1,098 / 1,168 = 94.01%**
- Final feature-eligible sessions: **1,093 / 1,168 = 93.58%**
- Expiry mapping: **100%**
- Prior-information violations: **0**
- Required coverage: **95%**

Observed IV-data failures among post-warm-up sessions:
- Missing ATM CE/PE: **33**
- IV inversion failures: **33**
- Other/empty failure reason: **4**

The feature gate therefore failed before Base/Stress numerical discovery.

## Decision

**CLOSED — DATA-LIMITED.**

No trading P&L, promotion cell, null comparison or WFA/OOS result is accepted from Phase 51.

The 95% threshold is not being lowered and the IV definition is not being broadened after seeing the coverage outcome.

## Interpretation

The pinned public option dataset does not provide sufficient, clean prior-session ATM CE/PE information for this specific feature at the required 95% completeness threshold. This is a data limitation, not evidence that the IV-level hypothesis is profitable or unprofitable.

## Strengths

- Strict next-expiry feature timing.
- Black-Scholes inversion from observed ATM CE and PE prices.
- 60 valid-observation regime history.
- Zero prior-information violations.
- Explicit missing-data and inversion-failure accounting.

## Limitation

The available option dataset has insufficient prior-session ATM quote completeness for this state variable under the frozen gate.

## Phase boundary

No post-result data-rule relaxation is authorized. A later phase may use a different, more source-complete volatility observable, but it must be separately preregistered.
