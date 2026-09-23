# Research Status

Last updated: 2026-09-23

## Overall
Phase 1 — DATA FOUNDATION IN PROGRESS

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

### 2026-09-23 — Step 1.1 Data foundation scaffold
- Added source manifest.
- Added generic CSV/Parquet/XLSX audit utility.
- Added configurable Paytm/NSE option cost model.
- Added unit tests.
- Added manual GitHub Actions workflow.
- Detected and fixed E0005 before the first workflow run.

## Current blockers
- Historical bid/ask/depth data may require licensed or broker-authenticated sources.
- Some public datasets have close/market-price bars without executable quotes.

## Next action
Add source download adapters and immutable cache manifests, run the first manual data audit, then promote to the Phase 2 baseline tournament.
