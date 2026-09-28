# Phase 40 Status

## Current state
PREREGISTERED — ENGINEERING BUILD / NUMERICAL EXECUTION PENDING.

## Completed
- Phase 40 research question, information timing, 8-cell discovery grid, cost model and null controls are frozen.
- Dedicated branch: phase-40-overnight-gap-implied-move-v1.
- Source diagnostic and manual Actions workflow are present.
- Phase 39 is now confirmed CLOSED — NEGATIVE DISCOVERY; Phase 40 remains a distinct follow-on family.

## Engineering corrections before first economic run
- E0401: phase engine used a contiguous rolling z-score; corrected to the strictly prior 60 valid GAP_RATIO observations with no imputation.
- E0402: prior RV20 included the current signal day's close; corrected with a one-session shift.

## Pending
1. Clean unit tests.
2. Pinned source acquisition and data gate.
3. Base/Stress/nulls only if all gates pass.
4. Final manuscript and main-status synchronization.

No Phase 40 P&L has been accepted.
