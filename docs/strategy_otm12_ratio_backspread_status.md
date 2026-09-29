# Status — OTM1 / 2xOTM2 Four-Leg Intraday Ratio Backspread

As of: 2026-09-29

| Phase | Status | Result |
|---|---|---|
| A implementation/data gate | ACTIVE | Unit tests PASS; source coverage PASS (1,234 sessions / 267 expiry files); quote-time normalization fixed and rerun active |
| B baseline Base/Stress | RUNNING | Latest authoritative workflow run 36529669783 |
| C losing-trade/common-circumstance analysis | PENDING | Requires valid baseline trades |
| D frozen holdout filter probe | PENDING | Only after C |
| E conclusion/manuscript | PENDING | Bounded endpoint |

## Latest run
- Workflow: 36529669783
- Branch: `strategy/otm1-2x-otm2-ratio-backspread-v1`
- Base and Stress are executing the frozen strategy.
- Earlier runs produced **no accepted P&L** because the quote-selection layer rejected all four-leg trades; this is classified as an implementation/data-selection defect, not a trading result.
- The latest code normalizes the IST timestamps and applies the 09:31 / 15:15 selection after timestamp normalization.

## Integrity rules
- No P&L is accepted until source coverage, unit tests, leg completeness and cost accounting pass.
- No prospective loss-avoidance rule may use post-entry information.
- No parameter is tuned after seeing the full-sample result.
- Every implementation/workflow defect is logged on this branch.
