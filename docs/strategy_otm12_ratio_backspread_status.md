# Status — OTM1 / 2xOTM2 Four-Leg Intraday Ratio Backspread

As of: 2026-09-29

| Phase | Status | Result |
|---|---|---|
| A implementation/data gate | ACTIVE | Branch created; strategy frozen |
| B baseline Base/Stress | PENDING | Workflow will run on branch update |
| C losing-trade analysis | PENDING | Requires valid baseline output |
| D frozen holdout filter probe | PENDING | Only after C |
| E conclusion/manuscript | PENDING | Bounded endpoint |

Integrity rules:
- No P&L is accepted until source coverage, unit tests, leg completeness and cost accounting pass.
- No prospective loss-avoidance rule may use post-entry information.
- No parameter is tuned after seeing the full-sample result.
- Every implementation/workflow defect is logged on this branch.
