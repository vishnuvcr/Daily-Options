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

### 2026-09-23 — Step 2.1 Baseline tournament CI run
- CI downloaded the 18 MB one-year NIFTY 1-minute sample successfully.
- Unit tests passed (4/4).
- Backtest stage stopped on E0006 before numerical results were produced.
- Correction committed so the next push reruns the tournament.

### 2026-09-23 — Step 2.2 Phase 2 baseline result
- Dataset: public one-year NIFTY 1-minute sample, 244 trading days.
- Variants tested: 12 directional option-buying configurations.
- Best variant: EMA family without VWAP/volume filters.
- Trades: 242.
- Win rate: 43.39%.
- Mean net on active trade days: Rs -307.42 per lot.
- Mean net across all trading days: Rs -304.90 per lot/day.
- Profit factor: 0.690.
- Total net: Rs -74,396.28 across the sample.
- Promotion gate: FAIL.
- Inference: simple single-leg directional option buying is rejected as the lead family under this cost/execution model; Phase 3 will test defined-risk option structures and regime-conditioned volatility signals.


### 2026-09-23 — Step 3.1 Phase 3 structure tournament
- Vertical-spread preliminary test: 21 multi-strike days were testable; the two tested widths did not meet the promotion gate. Best width-2 result: 9 trades, 33.33% win rate, mean active-day net Rs -155.82, mean all-day net Rs -5.75, profit factor 0.305, total net Rs -1,402.35.
- VRP-filtered directional option-buying test: 5 thresholds. Best recorded threshold 0.00: 168 trades, 44.05% win rate, mean active-day net Rs -185.32, mean all-day net Rs -127.60, profit factor 0.793, total net Rs -31,133.95. Gate FAIL_PRELIMINARY.
- Unfiltered intraday ATM short-straddle test: 3 variants. Best recorded configuration used a 2.0x premium stop, 50% premium-decay target and 180-minute maximum hold: 240 trades, 62.5% win rate, mean active-day net Rs 237.81, mean all-day net Rs 233.91, profit factor 1.351, total net Rs 57,074.53. Gate FAIL_PRELIMINARY but this is the strongest current hypothesis family.
- Added literature/data review covering NIFTY order flow/VRP studies, realistic-friction VRP research, and candidate multi-year option datasets.

### 2026-09-23 — Step 3.2 Next experiment
- Added a VRP-filtered short-volatility experiment using an IV-minus-realized-volatility threshold at the 09:30 entry window.
- Phase 3 CI was changed to manual-only so documentation commits do not cancel benchmark runs.
- Result: pending the next manual Phase 3 execution; the existing completed short-straddle result remains the current quantitative lead.


### 2026-09-23 — Step 3.3 Focused straddle grid result
- Optimized grid reused precomputed trade outcomes across 420 base configurations and 1,200 filter variants.
- Zero configurations reached the Rs 1,000/day target.
- Best filtered configuration: entry at 10:15, 1.8x premium stop, 45% decay target, 180-minute hold, gap <=0.5%, first-15-minute range <=0.5%, VRP >=0.
- Result: 153 trades, 62.7% calendar-day coverage, mean net Rs 233.06/day, median daily P&L Rs 0, 10th-percentile daily P&L Rs -1,513.44, positive-day rate 42.5%, max drawdown Rs -19,407.76/lot, profit factor 1.60.
- Decision: retire naked intraday straddle as lead family. It does not meet the target and its calendar-day hit rate/drawdown profile is not aligned with the user's consistency objective.

### 2026-09-23 — Cost/accounting correction
- Verified current NSE contract information is updated 2026-09-10 and NSE's Oct 3, 2025 circular revised NIFTY from 75 to 65; earlier 2025-2026 backtests that used a fixed 65 lot are therefore provisional until rerun with the date-aware contract resolver. citeturn328174search13turn328174search0
- Verified Paytm Money's current F&O FAQ states Rs 10 brokerage per unique executed F&O order; the research default remains a conservative Rs 20/order until the user's exact account tariff is known. citeturn809296search0

## Current blockers
- Historical bid/ask/depth data may require licensed or broker-authenticated sources.
- Some public datasets have close/market-price bars without executable quotes.

## Next action
Add source download adapters and immutable cache manifests, run the first manual data audit, then promote to the Phase 2 baseline tournament.
