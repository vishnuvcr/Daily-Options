# Phase 15 v1 — VRP + Jump-Brake Short Volatility Final Result

Authoritative clean rerun: 36019644002
Commit: 73fb5570882f4b1b5a03174520faee7dfe4ce331
Source: artist-23/nifty-options-data revision 45e0a04

## Critical invalidation before acceptance

The earlier Phase 15 shard result was quarantined because the execution-window join matched legs by strike but omitted the CALL/PUT side. The resulting pivot could assign the wrong side to a leg, and Base/Stress then produced different exit reasons even though only slippage changed. This was logged as E0145. All earlier Phase 15 P&L artifacts are invalid.

## Clean rerun

288 fixed cells: 3 entry times × 3 VRP thresholds × 2 jump brakes × 2 structures × 2 expiry types × 2 holds × 2 stop ratios.

### WEEK shard
- 144 cells.
- Base best: 09:30 | VRP>=4 | jump<=0.40% | STRADDLE | 60m | stop 1.30x.
- Base mean active-day net: ₹30.82.
- Stress mean active-day net: -₹9.23.
- Base target-qualified cells: 0.
- Stress target-qualified cells: 0.
- Base walk-forward: 35 windows, 17 positive, 0 target; mean test-window net -₹8.85.
- Stress walk-forward: 35 windows, 14 positive, 0 target; mean test-window net -₹50.44.

### MONTH shard
- 144 cells.
- Base best: 09:30 | VRP>=4 | jump<=0.40% | STRADDLE | 60m | stop 1.30x.
- Base mean active-day net: -₹90.53.
- Stress mean active-day net: -₹128.53.
- Base target-qualified cells: 0.
- Stress target-qualified cells: 0.
- Base walk-forward: 34 windows, 4 positive, 0 target; mean test-window net -₹147.37.
- Stress walk-forward: 34 windows, 4 positive, 0 target; mean test-window net -₹189.31.

### Combined nested walk-forward
- Base: 34 windows, 16 positive, 0 target; mean test-window net -₹9.85/lot/day.
- Stress: 34 windows, 13 positive, 0 target; mean test-window net -₹29.28/lot/day.

## Decision

Phase 15 is RETIRED. The VRP + jump-brake short-volatility family does not meet the ₹1,000/lot/day target, does not survive doubled slippage at the family level, and does not produce a qualifying walk-forward window.

No parameter retuning or post-hoc narrowing will be performed.

Next research family: intraday IV-skew / downside-tail repricing expressed through defined-risk option structures, with the same cost model and nested walk-forward gates.