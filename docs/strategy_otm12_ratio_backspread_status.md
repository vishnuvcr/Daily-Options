# Status — OTM1 / 2xOTM2 Four-Leg Intraday Ratio Backspread

As of: 2026-09-29

| Phase | Status | Result |
|---|---|---|
| A implementation/data gate | ACTIVE | Unit tests passed on prior correction; source coverage passed (1,234 sessions / 267 expiry files). Latest failed baseline exposed the need for stage-level quote-selection diagnostics. |
| B baseline Base/Stress | BLOCKED | Run 36529669783 failed in both frictions with 0 complete four-leg trades; diagnostic rerun 36530427013 is active. |
| C losing-trade/common-circumstance analysis | PENDING | Requires valid baseline trades. |
| D frozen holdout filter probe | PENDING | Only after C. |
| E conclusion/manuscript | PENDING | Bounded endpoint. |

## Latest authoritative activity
- Diagnostic commit: `ebefee1e4a586d8ae428a2877218d0d776ef8343`
- Workflow: `36530427013`
- Branch: `strategy/otm1-2x-otm2-ratio-backspread-v1`
- Base and Stress are rerunning the frozen strategy with per-session stage diagnostics.
- The prior zero-trade result is explicitly **not** a trading result.

## Integrity rules
- No P&L is accepted until source coverage, unit tests, leg completeness and cost accounting pass.
- No prospective loss-avoidance rule may use post-entry information.
- No parameter is tuned after seeing the full-sample result.
- Every implementation/workflow defect is logged on this branch.
