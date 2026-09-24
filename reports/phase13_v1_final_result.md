# Phase 13 v1 — Late-Day Volatility Acceleration Result

Authoritative workflow: 35994608170
Branch: phase-13-late-day-volatility-acceleration-v1
Head: 42b5020ed4f5cef8f0f0e6195603b1096bdc6427
Artifact SHA-256: 43723f9a2657679fc7e5543db6deb2501b5197d9a5e5fd3f40d5350ef575cee6

## Validity

The run passed unit tests, data extraction, base friction, doubled-slippage stress, decision summary and artifact upload. Earlier Phase 13 artifacts were rejected for preregistration arithmetic, cost-model and NaN-path defects and are audit-only.

## Full-sample result

- 384 fixed simulation cells.
- 40,384 signal entries.
- 79,456 executed trade records across the risk/hold cells.
- Base slippage: 0.20 premium points/leg.
- Stress slippage: 0.40 premium points/leg.

Best base cell: w10|z1.5|vp80|14:45:00|LONG|MONTH|h10|r0
- 306 trades / 153 active days
- Mean active-day net: ₹285.45/lot/day
- Median active-day net: -₹13.07
- Win rate: 49.67%
- Profit factor: 1.597
- Max drawdown: -₹17,464
- Total net: ₹43,674
- Preliminary target-qualified cells: 0

Stress for the same cell:
- Mean active-day net: ₹225.45/lot/day
- Median active-day net: -₹73.07
- Win rate: 47.06%
- Profit factor: 1.443
- Max drawdown: -₹18,784
- Total net: ₹34,494

## Nested walk-forward

- 5 test windows.
- Base: 4/5 positive test windows; 1/5 test windows above ₹1,000/lot/day; mean test-window net ₹243.65.
- Stress: 4/5 positive test windows; 0/5 above ₹1,000/lot/day; mean test-window net ₹183.65.

## Interpretation

The family is materially better behaved than Phases 8–12, but it does not meet the research target on the frozen full-sample leaderboard, and its average OOS result remains far below ₹1,000/lot/day. The isolated >₹1,000 test window is not enough to promote the family.

## Decision

Phase 13 is classified as a near-miss and frozen. No parameter retuning or post-result expansion is permitted. The exact leading rule will be subjected to independent later-period validation before any new optimization is considered.