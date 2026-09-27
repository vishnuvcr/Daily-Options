# Phase 33 Status

**Phase:** Dealer Gamma Exposure Proxies  
**Branch:** `phase-33-dealer-gamma-exposure-v1`  
**State:** **CLOSED — DATA-LIMITED; no economic P&L accepted**

## Authoritative data-gate run

**36340721257**

- Expected prior-session observations: **1,233**
- Gamma snapshots: **1,228**
- Snapshot coverage: **99.59%**
- Prior-information barrier violations: **0**
- GEX_Z coverage: **100.00%**
- FLIP_DISTANCE_Z coverage: **26.54%**
- ATM_GEX_SHARE_Z coverage: **100.00%**
- Feature-gate requirement per registered feature: **95%**

Because FLIP_DISTANCE_Z is only 26.54% complete after warm-up, the preregistered feature gate fails. Base/Stress discovery is not authorized.

## Quarantined runs

Runs **36339719895**, **36339811180**, **36340037859**, **36340212329**, and **36340369225** are not economic evidence. The first four contain implementation failures; run 36340369225 predates the final audited cost/sign/timestamp corrections and is explicitly quarantined.

## Decision

Phase 33 is closed as DATA-LIMITED. No strategy, P&L, null economics, WFA or OOS result is promoted.

Final manuscript: `reports/phase33/final_result.md`.

## Next family

Phase 34: **multi-expiry volatility term structure**.
