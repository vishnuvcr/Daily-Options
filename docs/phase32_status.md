# Phase 32 Status

Branch: phase-32-options-skew-smile-dislocation-v1

Current state: corrected rerun pending/starting after E0428 and E0429.

Preregistered family: NIFTY option-skew / smile-surface dislocation.

Finite grid: 2 features × 2 thresholds × 3 exits = 12 true cells.

Null controls: seeds 101, 202, 303, 404, 505 for each feature/cell and friction.

Costs: Paytm Money/NSE/statutory model; Base ₹0.20 and Stress ₹0.40 premium-point slippage per order; historical NIFTY lot sizes.

Promotion gate: Base and Stress must both clear mean weekly net ≥₹5,000, median ≥₹5,000, ≥70% positive weeks and ≥80% execution coverage before WFA/OOS.

Run 1: 36338180973 — unit-test failure only; no acquisition/P&L. E0428/E0429 corrected.

Next checkpoint: corrected authoritative workflow run; no post-result tuning.
