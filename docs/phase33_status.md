# Phase 33 Status

**Phase:** Dealer Gamma Exposure Proxies  
**Branch:** `phase-33-dealer-gamma-exposure-v1`  
**State:** PREREGISTERED — corrected rerun pending  
**Numerical P&L:** none accepted

## Completed
- Phase 32 closure verified.
- New Phase 33 branch created from main.
- Research question, aims, methodology, frozen grid, costs, data gates and stop rule written.
- Literature review completed and persisted.
- Primary methodological issue — GEX sign is an inventory assumption, not an intrinsic Greek property — explicitly frozen before numerical testing.

## Frozen experiment
3 features × 2 thresholds × 2 exits = 12 true cells.
Five null seeds per cell and Base/Stress friction are mandatory.
No WFA/OOS before the economic gate.

## Run 1
Run **36339719895** passed all six unit tests and restored the pinned cache, but stopped before feature construction on E0439 (DuckDB reserved alias). No numerical result exists.

## Current phase
Build and unit-test the prior-session option/OI gamma reconstruction. The next numerical step is the source/schema gate; only after it passes may Base/Stress discovery run.

## Key risk controls
- Prior-session OI only.
- Strict prior-information barrier.
- Fixed ±1,500-point chain window.
- Fixed conventional call-positive / put-negative dealer proxy.
- No post-result sign switching.
- Historical lot-size and cost model.
