# Research Status

Last updated: 2026-09-23

## Overall
Phase 0 — BOOTSTRAPPED

## Step log

### 2026-09-23 — Step 0.1 Repository audit
- Target: vishnuvcr/Daily-Options
- Result: public repository, default branch main, repository size 0.
- Finding: no prior code, commits, strategy implementation, data or research report.
- Correction: initialized the repository as the authoritative research log and codebase.

### 2026-09-23 — Step 0.2 Current cost/regulatory baseline
- NSE current STT page shows option-sale STT at 0.15% effective 2026-04-01.
- NSE publishes permitted lot sizes through its contract-information page.
- Paytm Money announced flat Rs 20 brokerage across segments effective 2025-01-15.
- Correction: cost model defaults to Rs 20/order, 0.15% option-sale STT, and configurable exchange/statutory rates.

### 2026-09-23 — Step 0.3 Data-source reconnaissance
Candidate sources:
- NSE option chain and F&O reports.
- Zenodo NIFTY spot/futures/options 1-minute data, 2017-2020.
- Hugging Face NIFTY option dataset, about 34M rows, 2020-2025.
- Open-source NIFTY options data engines/backtesters.
- GitHub-based 1-minute collectors using broker APIs for future authenticated collection.

Status: candidate sources only; independent validation pending Phase 1.

## Current blockers
- Repository started empty.
- High-quality historical bid/ask/depth may require licensed or broker-authenticated sources.
- Some public datasets have close/market-price bars without bid/ask and cannot be treated as perfect executable prices.

## Next action
Create phase-1-data-foundation with data manifests, download adapters, schema validation, cached sample datasets and automated quality checks.


## Continuation checkpoint — 2026-09-24

### Execution findings
- Phase 8 v2 run 35937700542: tests/data acquisition passed, base computation failed on missing `open` in the executable-entry result. Current branch commit 7f1ed0b adds an explicit guard and preserves the intended option-open entry-price model.
- Phase 9 run 35937112092: attempt 3 is currently running the base numerical stage after an infrastructure cancellation of the prior attempt.
- Phase 10 run 35937773719: tests/data acquisition passed, base computation failed on pandas Series attribute access (`meta.leader`). Current branch commit 7558c90 replaces this with key-based access.

### Research integrity
No P&L from these failed runs is accepted. No parameter set was promoted or retuned from test-period results.

## Latest engineering checkpoint — 2026-09-24

- Phase 10 additional defect E0074 corrected in commit 5adf689; no result accepted.
- Phase 11 additional defect E0075 isolated and corrected on dedicated v2 branch; PR #12 is open.
- Phase 9 remains result-pending after repeated runner cancellation; CI was hardened before further interpretation.

## 2026-09-24 exact-ref execution checkpoint

Fresh corrected workflows:
- Phase 8 v3 run 35972809477: tests and data acquisition passed; base friction running.
- Phase 9 v2 run 35972822793: tests and data acquisition passed; base friction running.
- Phase 10 v2 run 35972869077: tests and data acquisition passed; base friction running.
- Phase 11 v3 run 35972926200: queued after PR-triggered workflow creation.

No P&L has been accepted from these runs yet. Exact-parent Git-data commits are now used for execution refs.

## 2026-09-24 execution frontier

- Phase 8 v3 run 35972809477: unit tests and data acquisition passed; base friction completed successfully; stress friction remains in progress.
- Phase 9 v4 retry run 35973446515: unit tests and data acquisition passed; base computation again cancelled by runner shutdown. No P&L accepted.
- Phase 10 v4 run 35973884459: corrected premium propagation; currently in progress after dependency installation. No P&L accepted.
- Phase 11 v3 run 35972926200 remains queued.

No strategy has cleared the Rs 1,000/lot/day promotion gate.

## Phase 8 result — 2026-09-24

Phase 8 v3 exact-ref run 35972809477 completed cleanly through unit tests, cached data acquisition, base friction and doubled-slippage stress.

- 96 preregistered variants.
- 107,460 executable trades.
- Best base mean all-day net: -₹6.13/lot/day.
- Best doubled-slippage mean all-day net: -₹36.13/lot/day.
- Target-qualified variants: 0/96.
- Best base profit factor: 0.988.
- Best base max drawdown: approximately -₹67,939 for the best-ranked variant.

Decision: Phase 8 is retired at the preliminary gate. No walk-forward promotion is warranted because no variant is even positive at the preliminary cost-aware gate, and no parameter will be retuned around this negative result.
## Phase 10 result — 2026-09-24

Phase 10 v4 run 35973884459 completed cleanly through base, doubled-slippage stress and its embedded walk-forward evaluation.

- 128 preregistered variants.
- 10,752 executable trades.
- Best base mean active-day net: -₹113.62/lot/day.
- Best stress mean active-day net: -₹136.48/lot/day.
- 0 preliminary target-qualified variants.
- 3 WFA windows, 0 positive test windows, 0 target windows.

Decision: Phase 10 is retired. No parameter retuning is permitted.
