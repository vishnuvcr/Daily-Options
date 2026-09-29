# Phase 55 — Same-Session 09:30 Front-vs-Next-Expiry ATM IV Term Structure Result

## Authoritative execution

- Workflow: **36550678482**
- Branch: phase-55-front-next-expiry-atm-iv-term-structure-v1
- Gate artifact: **11023669935**
- Gate artifact SHA-256: **8282c1d32749ed238d699f5fedc2395092f83b5a4e89dec10fed954ca3ec841a**

## Data-gate result

- Raw sessions: **1,228**
- Post-warm-up sessions: **1,228**
- Current-session front/back ATM-IV valid sessions: **898 / 1,228 = 73.13%**
- Final feature-eligible sessions: **894 / 1,228 = 72.80%**
- Feature-expiry mapping: **100%**
- Prior-information violations: **0**
- Exact-expiry files: **267**
- Dominant failure reason: **330 sessions missing front or back ATM IV**

The frozen minimum coverage requirement is **95%**. The observed 73.13% term-structure coverage is therefore far below the acceptance threshold.

## Decision

**CLOSED — DATA-LIMITED.**

No Base or Stress P&L was accepted. The discovery matrix was intentionally skipped because the mandatory feature/data gate failed.

The failure is a data-availability limitation in the pinned one-minute option archive: the exact front/back same-strike 09:30 ATM quote pair is not sufficiently complete across the study window.

## Integrity

- Unit tests: passed.
- Pinned dataset acquisition/cache: passed.
- Feature timing barrier: passed with zero violations.
- Expiry mapping: passed.
- No numerical strategy result was accepted.

## Stop rule

No post-result threshold, expiry, slope-sign, execution, or cost retuning is authorized in this phase. A future retry would require a new, separately preregistered data source or a materially different coverage design; it must not silently lower the 95% gate.
