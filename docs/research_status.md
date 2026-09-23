# Research Status

Last updated: 2026-09-23

## Overall
Phase 3F — OPTION MICROSTRUCTURE DATA AUDIT IN PROGRESS

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


### 2026-09-23 — Step 3E.3 Corrected VWAP/RSI momentum tournament
- The diagnostic established that the cached NIFTY spot-index Volume field is zero for all 91,185 spot rows, so spot-index volume cannot be a valid volume filter on this dataset.
- The implementation was corrected to use traded-option session VWAP and traded-option volume ratio, while keeping spot RSI/EMA as underlying filters.
- The corrected workflow passed CI and evaluated 1,296 variants across 244 calendar days with 11,178 signal/contract-path bases.
- No configuration reached the Rs 1,000/day target.
- Best configuration: 10:00 entry, 4-of-4 conditions, RSI 60/40, option volume ratio >=1.5, 15% stop, 30% target, 90-minute hold.
- Best result: 204 trades, 83.61% calendar-day coverage, mean all-day net Rs -558.10/day, mean active-trade-day net Rs -667.54, median daily net Rs -1,050.65, 10th-percentile daily net Rs -2,402.94, positive-day rate 21.31%, trade win rate 25.49%, profit factor 0.457, max drawdown about Rs -137,294/lot.
- Decision: Phase 3E is retired as a lead family. The failure is now attributable to the corrected signal specification rather than missing signal data.
- Next research branch should move to a materially different hypothesis instead of further tuning this family.


### 2026-09-24 — Step 3F.1 Phase 3F initiated
- Created branch `phase-3f-option-microstructure` from the completed Phase 3E branch.
- New hypothesis: use option-chain IV/OI/volume structure and volatility regime, rather than another RSI/VWAP/EMA variation.
- Added an auditable data-schema gate and manual-only GitHub Actions workflow.
- Primary external dataset candidate: artist-23/nifty-options-data, reported as 33.96M rows from 2020-12-29 to 2025-12-26 with IV, OI, volume, spot, strike and expiry metadata. This is a candidate source and must pass independent audit before strategy results are trusted.
- Current phase status: DATA AUDIT PENDING.


### 2026-09-24 — Step 3F.2 Source-tree and schema hardening
- Inspected the pinned Hugging Face source tree. The NIFTY dataset is partitioned into both `NIFTY/MONTH` and `NIFTY/WEEK`; each contains multiple strike/option parquet files.
- Correction: the original Phase 3F audit selected only the first parquet file. It has been replaced with a full-partition PyArrow scan so the audit covers all available parquet files.
- The dataset revision is pinned to Hugging Face revision `45e0a04` in `data/manifests/phase3f_artist23.json`.
- The public dataset viewer currently reports a negative minimum for `volume` while also reporting a very large positive maximum. This is a data-quality warning, not a strategy result. Volume features are quarantined until CI measures the affected rows and an independent reconciliation is completed.
- Added unit tests for multi-file scanning and negative-volume quarantine.

### 2026-09-24 — Step 3F.3 Automated audit trigger
- Changed the Phase 3F workflow to retain a manual `workflow_dispatch` button while also allowing a path-filtered push trigger for code/data-audit changes only.
- This avoids the earlier E0008 failure mode where documentation-only commits repeatedly relaunched long-running research jobs.
- Workflow now pins the external dataset revision, caches the raw source on the runner, runs unit tests first, then audits the complete `NIFTY` tree and uploads the report.
- Current status: audit run triggered by the research-code update; strategy optimization remains blocked until the data-quality gate is resolved.


### 2026-09-24 — Step 3F.4 CI correction
- The first path-filtered Phase 3F run executed all unit tests successfully (9/9) but stopped in the dataset acquisition step because the YAML shell heredoc delimiter was indented incorrectly.
- No market-data audit was executed in that failed run, so no data result was accepted.
- Correction applied: dataset acquisition now uses a single-line Python invocation pinned to revision `45e0a04`.
- A new path-filtered run should execute automatically from the correction commit.


### 2026-09-24 — Step 3F.5 Microstructure tournament launch correction
- The first Phase 3F tournament attempt reached the strategy step only after the full data audit passed, then failed before execution because the workflow ran the script directly and Python could not import the repository `research` package.
- No strategy statistic from that run is accepted.
- Correction: workflow now invokes `python -m research.phase3f_microstructure_tournament`, matching the known-good package execution pattern from Phase 2.
- The complete-data audit remains valid: 84 parquet files, 33,963,731 rows, 1,228 dates, IV/OI/spot non-null, 16 negative-volume rows quarantined, 485 IV>300 observations flagged.


### 2026-09-24 — Step 3F.6 Directional microstructure result
- The complete multi-year IV/OI/volume directional screen completed successfully in GitHub Actions run `35906761397`.
- 7,303 feature rows and 972 variants were evaluated using one-trade-per-day-per-parameter logic, next-bar entry, defined-risk debit spreads, the project cost model and 0.20-point slippage.
- Zero variants reached the Rs 1,000/day target.
- Best recorded configuration: MONTH expiry, 2-strike debit spread, 30-minute hold, OI imbalance >=0.20, volume imbalance >=0.20, 15-minute spot-return threshold 0.10%, IV/RV >=1.25.
- Best result: 92 trades, mean active-day net Rs -234.26, mean all-day net Rs -17.62, win rate 16.30%, positive-day rate 1.23%, profit factor 0.148, max drawdown Rs -21,379.94.
- Decision: retire the directional IV/OI/volume imbalance family as a Phase 3F lead. Do not spend additional tuning budget on this family.
- Next: test a defined-risk short-volatility/iron-fly regime screen using the same audited dataset.


### 2026-09-24 — Step 3F.9 IV-skew screen launch
- Initial IV-skew workflow run `35908956508` passed unit tests and data acquisition, but the first shock grid (2/4/6 IV points) produced zero signals. No P&L result was produced and no strategy conclusion was drawn.
- Interpretation: the initial event thresholds were too coarse for the observed intraday skew-change scale.
- Correction: widen the preliminary shock grid to 0.25/0.50/1.00 IV points and absolute-skew filters to 0/1/2 points, while keeping the same fixed strikes, next-minute entry and defined-risk four-leg structure.
- The workflow remains manual-capable and push-triggered only; the overlapping PR trigger was removed after concurrency cancellation noise.


### 2026-09-24 — Step 3F.10 IV-skew shock/reversion result
- Corrected IV-skew screen completed in GitHub Actions run `35909289272`.
- 7,245 feature rows and 162 expiry/parameter variants were evaluated.
- Zero variants had positive all-calendar-day expectancy; zero reached the ₹1,000/day target.
- Best configuration: MONTH expiry, 10:15 IST entry, skew shock >=1.0 IV point, absolute skew >=2.0 IV points, 90-minute hold; 12 trades; mean active-day net -₹306.43; mean all-day net -₹3.02; win rate 8.33%; PF 0.014; total net -₹3,677.20.
- Decision: retire IV-skew shock/reversion. Four economically distinct Phase 3F families have now failed preliminary promotion: directional IV/OI imbalance, defined-risk iron fly, fixed-strike OI-break, and IV-skew reversion.
- Next phase: Phase 4 nested walk-forward on the strongest near-miss candidate family from Phase 3 (intraday ATM short straddle) using the multi-year IV/OI dataset. This is a validation phase, not permission to promote the strategy.


### 2026-09-24 — Step 4.1 Phase 4 initialized
- Four Phase 3F microstructure hypotheses were tested and retired without a positive cost-aware result: directional IV/OI imbalance, iron-fly volatility regime, fixed-strike OI repositioning around breaks, and IV-skew shock/reversion.
- Phase 4 is now activated as a validation phase for the only prior near-miss family with positive in-sample expectancy: the intraday ATM short straddle.
- Added nested expanding-window train -> validation -> embargo -> untouched-test evaluation on the multi-year IV/OI dataset.
- The Phase 4 workflow is manual-capable and path-filtered; raw source is reused from the pinned Actions cache.


### 2026-09-24 — Step 4.2 Phase 4 execution hardening
- Phase 4 successfully completed its workflow setup and WFA engine execution path, but the first valid dataset run still produced no tradable ATM straddle observations.
- Root cause: call and put quotes in the public data can occur at different timestamps inside the allowed entry window, so requiring an exact common timestamp was too restrictive.
- Correction applied: choose the common strike nearest spot using the available call/put quotes within the 2-minute entry window; use the later quote timestamp as the signal/entry anchor, then hold that absolute strike through the path.
- A rerun is now executing with this correction. No Phase 4 numerical conclusion is accepted until it produces an actual observation/trade table.
