# Phase 12 v2 Data-Gate Checkpoint — 2026-09-24

Active branch: phase-12-derivative-lead-options-v2-data-gate

The Phase 11 family has been retired after a clean negative preliminary screen. Phase 12 is the new research frontier.

The v1 Phase 12 preflight is retained as audit history and is not executable evidence because it wrote a placeholder futures expiry identity.

The v2 branch adds:
- exact monthly NIFTY expiry dates derived from the pinned NIFTY option dataset;
- contract-by-contract NIFTY futures acquisition through OpenChart;
- common UTC-naive timestamp normalization for futures and spot;
- deterministic nearest-to-expiry selection;
- a hard gate of at least 300 trading days and at least 90 percent timestamp overlap;
- isolated v2b workflow concurrency with cancellation disabled.

No Phase 12 strategy P&L has been accepted. The next scientific gate is data integrity only; the 144 preregistered strategy variants remain untouched until the data gate passes.
