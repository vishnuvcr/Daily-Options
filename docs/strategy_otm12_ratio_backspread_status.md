# Status — OTM1 / 2xOTM2 Four-Leg Intraday Ratio Backspread

As of: 2026-09-29

| Phase | Status | Result |
|---|---|---|
| A implementation/data gate | ACTIVE | Timestamp probe passed: option bars at 09:31 and 15:15 exist. Root cause EOTM12-006 fixed: option/session trade_date type mismatch. Regression test added. |
| B baseline Base/Stress | RUNNING | New baseline automatically triggered by commit 352ca6684443ebb97f72421809ee1147c1139bc9. |
| C losing-trade/common-circumstance analysis | PENDING | Requires valid baseline trades. |
| D frozen holdout filter probe | PENDING | Only after C. |
| E conclusion/manuscript | PENDING | Bounded endpoint. |

## Latest authoritative activity
- Root-cause probe workflow: 36531281661 — successful.
- Probe finding: raw option parquet timestamps are IST-aware and selected option bars include 09:31 and 15:15. The zero-trade defect was the trade_date equality join, not timestamp availability.
- Fix commit: 352ca6684443ebb97f72421809ee1147c1139bc9.
- Strategy branch: strategy/otm1-2x-otm2-ratio-backspread-v1.
- No P&L has been accepted from any earlier failed run.

## Provisional baseline evidence
- Workflow 36531435058 produced 1,209 complete trades in both Base and Stress before the reporting exception EOTM12-007.
- Base: gross P&L -₹272,009.75; costs ₹445,912.12; net P&L -₹717,921.87; win rate 25.81%; profit factor 0.517.
- Stress: gross P&L -₹272,009.75; costs ₹602,848.12; net P&L -₹874,857.87; win rate 23.90%; profit factor 0.454.
- These are provisional because the clean post-fix rerun 36532252218 is still the authoritative confirmation run.
- Preliminary discovery/holdout analysis: no single pre-entry feature produced a robust profitable regime. A discovery-defined exclusion of the middle 40–80% of first-15-minute absolute return improved holdout mean P&L versus the unfiltered holdout but remained negative; it is not promoted as a trading filter.

## Integrity rules
- No P&L is accepted until source coverage, unit tests, leg completeness and cost accounting pass.
- No prospective loss-avoidance rule may use post-entry information.
- No parameter is tuned after seeing the full-sample result.
- Every implementation/workflow defect is logged on this branch.
