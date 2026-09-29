# Status — OTM1 / 2xOTM2 Four-Leg Intraday Ratio Backspread

As of: 2026-09-29

| Phase | Status | Result |
|---|---|---|
| A implementation/data gate | PASS with fixes | Branch created; tests pass; EOTM12-001/002/003 fixed and logged |
| B baseline Base/Stress | ACTIVE | Authoritative run 36527429892 executing Base/Stress; no P&L accepted yet |
| C losing-trade analysis | PENDING | Requires valid baseline output |
| D frozen holdout filter probe | PENDING | Only after C |
| E conclusion/manuscript | PENDING | Bounded endpoint |

Integrity rules:
- No P&L is accepted until source coverage, unit tests, leg completeness and cost accounting pass.
- No prospective loss-avoidance rule may use post-entry information.
- No parameter is tuned after seeing the full-sample result.
- Every implementation/workflow defect is logged on this branch.


### Latest execution checkpoint
- Run 36527429892 is active.
- Unit tests passed before data acquisition.
- Prior run 36527327192 passed the data coverage gate: 1,234 sessions and 267 expiry files, but failed pre-P&L on a DuckDB timezone cast; that defect is fixed.
- Current run is the first candidate to generate baseline P&L after the engine fix.
