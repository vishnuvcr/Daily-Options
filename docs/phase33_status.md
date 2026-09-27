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

## Run 2 / hardening
Run **36339811180** was still in the data-gate stage when the performance/methodology audit was performed. Its checked-out commit predates the vectorized hardening. No P&L is accepted from that run. The live branch now contains E0440's vectorized engine, frozen block-null permutation, and corrected regression.

Run 3 is the next authoritative attempt from the hardened branch head.

## Run 4 closure
Run **36340212329** completed unit tests, restored the cache, and generated the gamma feature panel plus signal panel, then failed in the execution-price query on the same unquoted `close` alias. No P&L was accepted. E0443 is logged; the exact query projection is now corrected.

Run 5 is the next authoritative attempt.

## Economic-accounting audit / run 5 quarantine
The live run **36340369225** predates the E0444/E0445 corrections. Its eventual numerical output, if any, is **quarantined and cannot be used** for promotion because that checkout omitted audited transaction/statutory costs, had the wrong put-debit-spread sign handling, and did not explicitly cap prior-session option snapshots at the index-session information cutoff.

Run **36340369225** is therefore not an authoritative P&L run. Run 6 is the first run eligible for economic interpretation.
