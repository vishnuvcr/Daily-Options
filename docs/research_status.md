# Research Status

Last updated: 2026-09-24

## Overall
Phase 3G — COMPLETE; FAIL_PRELIMINARY; RETIRED.

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

### 2026-09-24 — Cost/accounting correction
- Verified current NSE contract information is updated 2026-09-10 and NIFTY lot size changes must be handled by date-aware contract resolution.
- Verified current Paytm Money F&O FAQ states Rs 10 brokerage per unique executed F&O order; the research default remains a conservative Rs 20/order until the user's exact account tariff is known.
- Date-aware lot-size handling remains mandatory.

### 2026-09-24 — Step 3E.3 Corrected VWAP/RSI momentum tournament
- Diagnostic established that the cached NIFTY spot-index Volume field is zero for all 91,185 spot rows.
- Implementation was corrected to use traded-option session VWAP and traded-option volume ratio, while keeping spot RSI/EMA as underlying filters.
- Corrected workflow evaluated 1,296 variants across 244 calendar days with 11,178 signal/contract-path bases.
- No configuration reached the Rs 1,000/day target.
- Best configuration: 10:00 entry, 4-of-4 conditions, RSI 60/40, option volume ratio >=1.5, 15% stop, 30% target, 90-minute hold.
- Best result: 204 trades, 83.61% calendar-day coverage, mean all-day net Rs -558.10/day, mean active-trade-day net Rs -667.54, median daily net Rs -1,050.65, 10th-percentile daily net Rs -2,402.94, positive-day rate 21.31%, trade win rate 25.49%, profit factor 0.457, max drawdown about Rs -137,294/lot.
- Decision: Phase 3E retired as a lead family.

### 2026-09-24 — Step 3F.1 Phase 3F initiated
- Created branch phase-3f-option-microstructure.
- New hypothesis: use option-chain IV/OI/volume structure and volatility regime, rather than another RSI/VWAP/EMA variation.
- Added an auditable data-schema gate and manual-only workflow.
- Primary external dataset candidate: artist-23/nifty-options-data, reported as 33.96M rows from 2020-12-29 to 2025-12-26 with IV, OI, volume, spot, strike and expiry metadata.
- Current phase status: data audit pending.

### 2026-09-24 — Step 3F.2 Source-tree and schema hardening
- Inspected the pinned Hugging Face source tree.
- Correction: original audit selected only the first parquet file; replaced with a full-partition PyArrow scan.
- Dataset revision pinned to 45e0a04 in data/manifests/phase3f_artist23.json.
- Public viewer reported a negative minimum for volume; volume features quarantined pending reconciliation.
- Added unit tests for multi-file scanning and negative-volume quarantine.

### 2026-09-24 — Step 3F.3 Automated audit trigger
- Workflow retains manual workflow_dispatch plus path-filtered push trigger for code/data-audit changes.
- Raw source is cached on the runner.
- Current status: audit run triggered; strategy optimization blocked until data-quality gate is resolved.

### 2026-09-24 — Step 3F.4 CI correction
- First path-filtered data-audit run executed unit tests successfully but stopped in dataset acquisition because the YAML shell heredoc delimiter was indented incorrectly.
- No market-data audit was executed in that failed run.
- Correction: dataset acquisition now uses a single-line Python invocation pinned to revision 45e0a04.

### 2026-09-24 — Step 3F.5 Microstructure tournament launch correction
- First Phase 3F tournament attempt failed before execution because the workflow ran the script directly and Python could not import the research package.
- No strategy statistic from that run was accepted.
- Correction: workflow now invokes python -m research.phase3f_microstructure_tournament.
- Complete-data audit: 84 parquet files, 33,963,731 rows, 1,228 dates, IV/OI/spot non-null, 16 negative-volume rows quarantined, 485 IV>300 observations flagged.

### 2026-09-24 — Step 3F.6 Directional microstructure result
- Complete multi-year IV/OI/volume directional screen completed successfully in GitHub Actions run 35906761397.
- 7,303 feature rows and 972 variants were evaluated using one-trade-per-day-per-parameter logic, next-bar entry, defined-risk debit spreads, project cost model and 0.20-point slippage.
- Zero variants reached the Rs 1,000/day target.
- Best configuration: MONTH expiry, 2-strike debit spread, 30-minute hold, OI imbalance >=0.20, volume imbalance >=0.20, 15-minute spot-return threshold 0.10%, IV/RV >=1.25.
- Best result: 92 trades, mean active-day net Rs -234.26, mean all-day net Rs -17.62, win rate 16.30%, positive-day rate 1.23%, profit factor 0.148, max drawdown Rs -21,379.94.
- Decision: retire the directional IV/OI/volume imbalance family.

### 2026-09-24 — Step 3F.9 IV-skew screen launch
- Initial IV-skew workflow run 35908956508 passed unit tests and data acquisition, but the first shock grid produced zero signals.
- Correction: widened preliminary shock grid and absolute-skew filters while keeping fixed strikes, next-minute entry and defined-risk four-leg structure.

### 2026-09-24 — Step 3F.10 IV-skew shock/reversion result
- Corrected IV-skew screen completed in GitHub Actions run 35909289272.
- 7,245 feature rows and 162 expiry/parameter variants were evaluated.
- Zero variants had positive all-calendar-day expectancy; zero reached the Rs 1,000/day target.
- Best configuration: MONTH expiry, 10:15 IST entry, skew shock >=1.0 IV point, absolute skew >=2.0 IV points, 90-minute hold; 12 trades; mean active-day net -Rs 306.43; mean all-day net about -Rs 3.02; win rate 8.33%; PF 0.014; total net -Rs 3,677.20.
- Decision: retire IV-skew shock/reversion.
- Prior defined-risk iron-fly and fixed-strike OI-break branches were also retired without a positive cost-aware result.

### 2026-09-24 — Step 4.1 Phase 4 initialized
- Four Phase 3F microstructure hypotheses were tested and retired without a positive cost-aware result.
- Phase 4 activated as a validation phase for the only prior near-miss family with positive historical expectancy: the intraday ATM short straddle.
- Added nested expanding-window train -> validation -> embargo -> untouched-test evaluation on the multi-year IV/OI dataset.

### 2026-09-24 — Step 4.2 Phase 4 execution hardening
- Initial valid dataset run produced no tradable ATM straddle observations.
- Root cause: call and put quotes can occur at different timestamps inside the entry window.
- Correction: choose the common strike nearest spot using available call/put quotes within the 2-minute entry window; use the later quote timestamp as the signal/entry anchor and hold that absolute strike through the path.

### 2026-09-24 — Step 4.3 Phase 4 entry-clock bug fixed
- Diagnostics from run 35911325373 showed PHASE4_OBSERVATIONS=0.
- Root cause: configured entry offsets were added to midnight rather than the 09:15 IST market open.
- Correction: entry timestamp is now explicitly 09:15 IST plus the configured post-open offset.

### 2026-09-24 — Step 4.4 Phase 4 nested walk-forward result
- GitHub Actions run: 35912159508; commit: 05c2ce40d4bafbb07baa64298c46eb64439e5058.
- Unit tests passed and the complete multi-year data cache was acquired/reused successfully.
- Observations: 7,331; core trade rows: 131,958; expanded trade rows: 852,750.
- Core variants: 54; regime-filter variants: 8; total parameter variants: 432.
- Walk-forward windows: 14; selected test windows: 22; positive test windows: 8; target-qualified test windows: 0.
- Mean selected test-window net: Rs -64.23/lot; median: Rs -43.69/lot.
- Mean test positive-day rate: 47.65%.
- No selected-test bootstrap 95% lower bound was positive across the run.
- Gate: FAIL_PRELIMINARY.
- Decision: retire the intraday ATM short-straddle family as a lead candidate. Do not run another unconstrained straddle sweep.
- Next bounded hypothesis: dynamic intraday price-structure breaks as the primary event, with option OI repositioning used only as post-break confirmation and a defined-risk debit spread as the implementation.

### 2026-09-24 — Step 4.5 Repository audit / environment correction
- Direct local git clone was attempted for source-tree inspection but failed because DNS/network resolution to github.com was unavailable in the execution container.
- No research result depended on that clone; GitHub connector access remained authoritative.
- Logged as E0035 and closed.

### 2026-09-24 — Step 3G.1 Bounded implementation prepared
- Created branch phase-3g-oi-confirmed-breakout from the completed Phase 4 validation branch.
- Pre-registered 128 parameter variants: 15/30-minute structure lookback, 3/5-minute OI confirmation, 0.01/0.02 normalized OI threshold, WEEK/MONTH expiry, 1/2-strike debit spread, 60/90-minute hold, and optional IV/RV <=1.25 filter.
- OI is used only after the price-structure break; the strategy does not use OI as a standalone predictor.
- Added base-cost and 2x-slippage runs, date-aware NIFTY lot sizes, and a temporary CI bridge because the dedicated Phase 3G workflow was not being scheduled by the repository Actions connection.
- Implementation code and bounded hypothesis documentation are committed; numerical results are not yet accepted until CI produces the trade/leaderboard artifacts.

### 2026-09-24 — Step 3G.0 CI diagnostic and specification correction
- Run 35914357367 passed all 12 unit tests and fetched all 84 pinned parquet partitions.
- Research execution failed because trade_id was dropped before path simulation; no strategy statistic was accepted.
- Initial OI confirmation also used backward-looking OI change at the break timestamp; this did not satisfy the declared information barrier and is rejected.
- Correction: preserve trade_id, use forward 3/5-minute OI change, delay entry until the window has elapsed, and cache the pinned dataset.

### 2026-09-24 — Step 3G.2 Corrected Phase 3G result and retirement
- Corrected GitHub Actions run 35916973751 completed successfully after the WFA date-normalization fix.
- Base slippage (0.20 points/leg): all 128 variants had negative mean all-calendar-day net; best mean was Rs -61.11/lot/day.
- Stress slippage (0.40 points/leg): all 128 variants remained negative; best mean was Rs -79.55/lot/day.
- Corrected WFA: 13 test windows; base 1 positive / 13 and mean test-window net Rs -192.79; stress 0 positive / 13 and mean Rs -252.79.
- Bootstrap 95% intervals for mean test-window net remained fully below zero in both friction settings.
- Decision: Phase 3G is retired. No grid expansion is permitted.
- Next bounded hypothesis: derivative price-discovery / option-lead-lag using short-horizon ATM option price changes as the information source and defined-risk spreads as the execution vehicle.

## Current blockers
- Historical bid/ask/depth data may require licensed or broker-authenticated sources.
- Some public datasets have close/market-price bars without executable quotes.

## Current phase
Phase 3H — COMPLETE; FAIL_PRELIMINARY; RETIRED.

### 2026-09-24 — Step 3H.6 Accepted result and retirement
- Corrected indexed-engine run 35918302989 completed successfully on commit 64abd09e74e5a209b461f86efef4d41a91478681; artifact 10775828210 is retained as the canonical execution output.
- 108 pre-registered variants, 438,043 feature rows, 132,072 executable trades.
- Base slippage 0.20: all variants negative; best mean all-calendar-day net Rs -181.83/lot/day.
- Stress slippage 0.40: all variants negative; best mean all-calendar-day net Rs -241.83/lot/day.
- Nested walk-forward: 16/16 test windows negative at both frictions. Base mean test-window net Rs -191.39; stress mean Rs -251.39.
- Bootstrap 95% percentile intervals for the mean test-window net exclude zero at both frictions.
- Decision: retire Phase 3H. No threshold expansion, sign reversal, extra filter or additional option-microstructure sweep is permitted within this family.
- Next bounded experiment: Phase 3I, a cross-market/underlying price-discovery hypothesis based on NIFTY futures-versus-spot information, subject first to a historical futures data-quality gate.

### 2026-09-24 — Step 3H.1 Phase 3H initialized
- Created branch phase-3h-option-lead-lag from the finalized Phase 3G branch.
- Pre-registered 108 variants testing ATM option-pressure lead-lag: 1/3/5-minute lookback, 1%/2%/3% pressure threshold, WEEK/MONTH expiry, 1/2-strike spread width, 5/10/15-minute hold.
- Added a leakage-safe forward-return diagnostic and defined-risk debit-spread execution engine.
- Added manual GitHub Actions workflow with cached pinned dataset and base/stress slippage runs.
- Current status: awaiting CI numerical result.

### 2026-09-24 — Step 3H.2 Pre-result engine correction
- Unit tests passed in the initial Phase 3H CI attempt, but code review identified a path-simulation bookkeeping defect before any strategy statistic was accepted: identical setups were deduplicated without remapping the simulated path to every matching variant.
- Correction: simulate each unique setup once, then merge path outcomes back to all matching variants; constrain "next executable" entry lookup to a two-minute execution budget.
- No numerical Phase 3H result from the pre-correction run is eligible for acceptance.

### 2026-09-24 — Step 3H.3 Cache reuse correction
- Phase 3H initially used a phase-specific cache key.
- Correction: switched to the pinned-data cache key shared across phases, with the Phase 3G cache as a restore source.
- No strategy statistic was accepted from the pre-correction CI attempt.

### 2026-09-24 — Step 3H.4 Execution-speed correction
- The initial Phase 3H numerical engine remained in one long CI step without progress reporting after the pinned dataset was acquired.
- No numerical statistic from that slow run is accepted.
- Replaced the nested per-signal/per-path DataFrame scans with indexed per-session price maps and one-time setup simulation, then reattaching each simulated path to all matching variants.
- CI will now rerun automatically on the corrected branch commit.

### 2026-09-24 — Step 3H.5 Corrected CI rerun
- New indexed-engine workflow run 35918302989 is in progress.
- Checkout and environment setup completed successfully.
- At last inspection, dependency installation was in progress; numerical backtest had not started yet.
- No Phase 3H strategy statistics are accepted at this point.


### 2026-09-24 — Step 3H.4 Phase 3H final result and retirement
- Corrected optimized run 35918302989 completed successfully on commit 64abd09e74e5a209b461f86efef4d41a91478681; artifact 10775828210.
- 108 pre-registered option-lead-lag variants were evaluated over 438,043 feature rows and 132,072 executable trades.
- Base slippage 0.20: every variant had negative mean calendar-day net; best was Rs -181.83/lot/day.
- Stress slippage 0.40: every variant remained negative; best was Rs -241.83/lot/day.
- Base WFA: 16/16 test windows negative; mean test-window net Rs -191.39; bootstrap 95% interval approximately [-214.70,-169.35].
- Stress WFA: 16/16 test windows negative; mean Rs -251.39; bootstrap 95% interval approximately [-274.70,-229.35].
- Forward spot diagnostics showed no stable directional hit-rate edge; observed 1-minute hit rates ranged about 46.8%–56.1%.
- Decision: retire Phase 3H. No parameter expansion is permitted.
- Next bounded direction: regime-conditioned underlying-price behavior (intraday dislocation/mean-reversion or opening-range regime) expressed through defined-risk spreads.

### 2026-09-24 — Step 3I.1 Phase 3I implementation and data-gate launch
- Created branch `phase-3i-futures-spot-lead-lag` from the accepted Phase 3H record.
- Added a pre-registered 72-variant futures/spot predictive diagnostic using futures return, futures-minus-spot lead gap, and basis-change features over 1/3/5-minute lookbacks with 0/2/5/10-bps thresholds and continuation/contrarian modes.
- Added a Stage-1 data gate against the pinned Zenodo spot/futures archive and a manual GitHub Actions workflow with cache reuse and artifact upload.
- First execution revealed that the Zenodo master archive contains nested yearly ZIP files. This is logged as E0047 and corrected by recursively extracting those yearly archives.
- Current corrected workflow run: 35919545224, based on commit 39b68958683b02883706e9c39e017de0b96b64fe.
- No Phase 3I numerical result is accepted until the corrected run produces the source audit and predictive diagnostic.

### 2026-09-24 — Step 3I.2 Data gate pass; first predictive screen provisional
- Canonical run 35919907675 (artifact 10776373001) successfully loaded all four years from the pinned Zenodo archive.
- Data audit: 372,055 spot rows, 371,783 futures rows, 991 common trading dates, 99.733% timestamp overlap and 99.193% common-day session completeness at the >=350-minute threshold. Date range: 2017-01-02 through 2020-12-31.
- The first 72-variant predictive screen produced a small cluster of overall-threshold positives and was provisionally marked PASS by the initial implementation.
- Step 3I.3 review found that the implementation had not enforced the pre-registered requirement of two forward horizons plus same-sign performance in both sample halves. That screen is not accepted for promotion.
- A corrected strict predictive-gate implementation is now running; only its output can determine whether Phase 3I advances to option implementation.

### 2026-09-24 — Step 3I.4 Option-source compatibility correction
- The first Phase 3I option execution did not have overlapping historical coverage with the futures/spot signal sample, so its result is rejected as invalid.
- The option stage is being rerun from the matching 2017-2020 Zenodo NIFTY archive with lazy strike-file indexing.
