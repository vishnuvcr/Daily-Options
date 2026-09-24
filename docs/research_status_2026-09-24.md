# Research Status Checkpoint — 2026-09-24

Phase 11 v5e completed successfully on workflow run 35978104824.

Phase 11 result: 64 preregistered variants; 2,220 signals; 2,020 trades; 0 target-qualified variants. Best base mean active-day net was -122.28 INR per lot per active day. Stress at doubled slippage was -138.10 INR. Exit counts were 1,036 STOP, 978 TIME, and 6 TARGET. Decision: retire the family without result-driven retuning.

Phase 12 is now the active frontier. The original Phase 12 v1 data preflight is not accepted because it assigned a placeholder futures expiry. A v2 data-gate branch preserves the original as audit history and adds exact monthly expiry derivation, contract-by-contract NIFTY futures acquisition, and common UTC timestamp normalization before the coverage gate.

No Phase 12 strategy P&L has been computed or accepted yet.


## Phase 12 v3 final closure — 2026-09-24

Workflow 35992405332 completed successfully. The corrected Phase 12 futures/spot lead-lag pilot produced 52,476 signal entries and 51,760 executable trades across the 288 preregistered simulation cells. Base best mean active-day net was -₹151.50/lot/day; stress was -₹211.50. All 4 walk-forward test windows were negative in both friction settings. Phase 12 is retired without result-driven retuning.

### Next frontier: Phase 13
Phase 13 moves to a materially different modern-data mechanism: volatility regime + price structure + defined-risk NIFTY option execution with an explicit no-trade filter. Candidate modern data sources include thetrademarkk/india-index-options-1m (~2021–2026) and rissin/nse-options-intraday (Oct 2024–2026), with exact expiry and timestamp integrity gates. The phase will not inherit Phase 12's futures-lead parameter family.
