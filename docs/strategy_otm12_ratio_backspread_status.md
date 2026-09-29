# Status — OTM1 / 2xOTM2 Four-Leg Intraday Ratio Backspread

As of: 2026-09-29

| Phase | Status | Result |
|---|---|---|
| A implementation/data gate | CLOSED | Timestamp semantics, trade-date join, leg completeness and cost plumbing validated. |
| B baseline Base/Stress | CLOSED | Clean workflow 36532252218 PASS: 1,209 completed trades, 98.53% execution coverage. |
| C losing-trade/common-circumstance analysis | CLOSED | Workflow 36533478456 PASS. High prior-day range + near-expiry identified as a repeatable loss-concentration regime. |
| D frozen holdout filter probe | CLOSED | Workflow 36533719671 PASS. Frozen filter replicated on 2025+ holdout and improved negative P&L without making the retained strategy profitable. |
| E conclusion/manuscript | CLOSED | Workflow 36534074291 PASS. Final manuscript, supplement, tables and figures validated. |

## Clean baseline conclusion

Base:
- 1,209 trades; 312 wins / 897 losses
- Win rate 25.81%
- Gross P&L -₹272,009.75
- Costs ₹445,912.12
- Net P&L -₹717,921.87
- Profit factor 0.517
- Max drawdown -₹716,320.49

Stress:
- 1,209 trades; 289 wins / 920 losses
- Win rate 23.90%
- Gross P&L -₹272,009.75
- Costs ₹602,848.12
- Net P&L -₹874,857.87
- Profit factor 0.454
- Max drawdown -₹873,136.49

## Main research finding

The strongest repeatable loser regime is prior-day NIFTY range > 1.314516% together with days to expiry <= 1.5 calendar days.

On the untouched 2025+ holdout this regime contained 24 of 348 trades (6.90%) and had mean net P&L about -₹2.83k Base / -₹3.00k Stress.

Excluding those trades improved holdout net P&L by ₹67,879 Base and ₹71,911 Stress, but the retained strategy remained negative at -₹663.91/trade Base and -₹836.94/trade Stress.

## Profit mechanism

Profitable trades are primarily one-sided convex outcomes: in 100% of winners, at least one of the combined call-side or put-side contributions was positive. The complete win generally comes from a sufficiently large move through one wing rather than simultaneous movement on both sides.

## Final interpretation

This branch does not establish a profitable standalone trading strategy. It establishes a reproducible loss-concentration regime that can be used as a research clue for future, separately validated entry filters or strategy redesign.

## Final manuscript

- Branch: research/otm12-phase-e-manuscript-v1
- Final validation workflow: 36534074291

