# Research Status

Last updated: 2026-09-25

## Overall
**Phase 30.2 — Equity Income / Falcon Spread weekly independent replication**

## Current research objective — 2026-09-25
The active YouTube/Equity Income program has replaced the former ₹1,000/active-lot/day intraday stopping rule with a **₹5,000 NET per completed trading week** objective at a fixed declared reference strategy position size.

The active consistency gate is:
- mean weekly net ≥ ₹5,000 on untouched OOS weeks;
- median weekly net ≥ ₹5,000;
- ≥70% of eligible OOS weeks net-positive;
- ≥80% of eligible OOS weeks executed unless a source-frozen no-trade rule applies;
- Base and doubled-slippage Stress both disclosed;
- weekly drawdown/worst week/expected shortfall/CVaR/profit factor and concentration reported.

The old ₹1,000/day threshold remains historical for Phases 0–25 and must not be used for Phase 29.5/30 decisions.

## Current blocker
Phase 29.4/29.5 source-fidelity and contract readiness must finish before any weekly P&L is accepted. The Iron Dome formalization branch already contains the bounded 12-cell matrix; Phase 30 remains blocked until its contract/lot and execution-cost gates pass.

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

## Current blocker / next action
The sole active numerical frontier is Falcon Spread. Run 36160873596 has passed tests and exact Rissin acquisition and is executing Base/Stress friction. No P&L is accepted until both jobs finish and their persisted artifacts are independently audited. If 0/270 cells pass the frozen weekly gate, retire Falcon and move to the next distinct source-faithful Equity Income candidate; no result-driven tuning.


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

## Phase 10 final decision — 2026-09-24

Phase 10 (cross-index relative-strength debit spreads) is **RETIRED** after a complete base + doubled-slippage stress run.

- 128 variants preregistered; 64 produced trades.
- Best base mean active-day net: ₹-113.62/lot/day.
- Best stress mean active-day net: ₹-136.48/lot/day.
- Base WFA: 0/3 positive, 0/3 target; mean test-window net ₹-122.39.
- Stress WFA: 0/3 positive, 0/3 target; mean test-window net ₹-138.27.
- No result-based retuning was performed.

Phase 10 result archive: `reports/phase10/` on `phase-10-cross-index-1m-v4-exec`.

## Phase 12 preregistration — 2026-09-24

A new data-gated family is preregistered in branch `phase-12-derivative-lead-options-v1` / PR #20.

Mechanism: measure derivative-versus-spot standardized return dislocation on NIFTY futures, then express a qualifying directional signal through a defined-risk option debit spread.

The phase is intentionally parked until:
- at least 300 futures trading days;
- >=90% futures/spot minute overlap;
- deterministic nearest-contract selection;
- exact contract-expiry metadata available before promotion;
- sufficient option entry coverage.

No Phase 12 P&L result exists yet.

## Phase 9 final result — 2026-09-24

Corrected Phase 9 v6 computation completed all four shards successfully. Independent aggregation of the four completed shard trade files produced the global result:

- 96 preregistered variants.
- 106,152 trades.
- Best base mean active-day net: **-₹168.79/lot/day**.
- Best doubled-slippage stress mean active-day net: **-₹228.79/lot/day**.
- 0/96 variants positive on mean active-day net.
- Base profit factor: **0.340**.
- Stress profit factor: **0.253**.
- Global nested walk-forward: 16 windows, **0 positive**, 0 target windows; mean test-window net **-₹231.14** base and **-₹252.34** stress.

Decision: Phase 9 is retired. The defined-risk regime credit-spread family is frozen; no further parameter tuning is permitted.

## 2026-09-24 — Phase 11 v5e authoritative execution checkpoint

- Authoritative branch: `phase-11-breakout-pullback-oi-v5e-authoritative`.
- Workflow run: `35978104824`; research job: `107563265459`.
- Unit tests: passed.
- Cached research data acquisition: passed.
- Base friction: in progress.
- Stress friction and report generation: pending.
- Accepted P&L: none.

The isolated v5e concurrency group uses `cancel-in-progress: false`, so the earlier v5/v6 cancellation pattern is not being repeated. Phase 8, Phase 9 and Phase 10 remain frozen negative; Phase 12 remains parked.

## 2026-09-24 — Phase 11 v5e authoritative execution checkpoint

- Authoritative branch: phase-11-breakout-pullback-oi-v5e-authoritative.
- Workflow run: 35978104824; research job: 107563265459.
- Unit tests: passed.
- Cached research data acquisition: passed.
- Base friction: in progress.
- Stress friction and report generation: pending.
- Accepted P&L: none.

The isolated v5e concurrency group uses cancel-in-progress=false, so the earlier v5/v6 cancellation pattern is not being repeated. Phase 8, Phase 9 and Phase 10 remain frozen negative; Phase 12 remains parked.


## 2026-09-24 — Phase 13 final result

Phase 13 late-day volatility acceleration completed cleanly in workflow run 35994608170. The 384-cell preregistered family generated 40,384 signal entries and 79,456 trade records. Best base mean active-day net was ₹285.45/lot/day; doubled-slippage stress was ₹225.45. No cell reached ₹1,000/lot/day. Nested walk-forward produced 5 windows: 4 positive and 1 negative at both friction levels. One base test window exceeded ₹1,000, but the corresponding stress window remained below target, so the family is classified as a near-miss and frozen without retuning.

Next active frontier: a global-cross-market opening-gap / India-open regime family, using only information known before the Indian session and a separate option execution layer.


## 2026-09-24 — Phase 14 preliminary result

Phase 14 global-cross-market opening-gap completed successfully in run 35996090009. The 768-cell frozen grid produced 15,464 entries and 30,256 trades. The raw leaderboard contained 32 cells above ₹1,000/lot/day at both base and stress, but these were concentrated in very small active-day samples. The freeze-safe walk-forward had only one available test window because the 2019–2020 data span yielded 212 distinct signal days; the selected rule (`GLOBAL3|gz0.5|gap0.0075|FADE|09:30:00|LONG|MONTH|h20|r0`) lost ₹1,232.12/lot/day base and ₹1,292.12 stress in that test. Phase 14 is therefore PROMISING/UNVALIDATED rather than promoted.

Next step: independent later-period validation of that exact frozen rule on the pinned 2020–2025 `artist-23/nifty-options-data` dataset, with no parameter search.


## 2026-09-24 — Phase 14 later-OOS closure and Phase 15 live execution

Phase 14 later-OOS validation of the frozen global-cross-market opening-gap rule is now closed. On the independent Rissin 1-minute NIFTY option source (run 36000863530), the exact frozen rule produced 12 executable trades across 17 signal days. Base mean active-day net was ₹352.05/lot; doubled-slippage stress was ₹322.05/lot. Only 2025 contributed trades, so the result did not satisfy the multi-year/100-trade promotion gate. Phase 14 is frozen and retired; no parameter retuning is authorized.

Phase 15 VRP + jump-brake short-volatility is the active frontier. Authoritative run 36005428946 on branch phase-15-vrp-jump-brake-short-vol-v1 has passed tests, pinned data acquisition and the lightweight timestamp/quote alignment probe; Base friction remains in progress. No Phase 15 P&L is accepted until Base, stress, walk-forward and independent later-source validation are complete.


## 2026-09-24 — Phase 15 final result

Phase 15 clean rerun 36019644002 invalidated the earlier spectacular short-volatility result after fixing E0145 (CALL/PUT leg contamination). Clean WEEK base best was ₹30.82/lot/day and stress -₹9.23; MONTH base -₹90.53 and stress -₹128.53. No target-qualified cell or walk-forward test window reached ₹1,000/lot/day. Combined nested WFA mean test-window net was approximately -₹9.85 base and -₹29.28 stress. Phase 15 is retired without retuning.

Next active frontier: intraday IV-skew / downside-tail repricing using defined-risk structures and the same fixed-cost/walk-forward framework.


## 2026-09-24 — Phase 15 critical invalidation and Phase 16 launch

Phase 15 clean rerun 36019644002 is the only accepted Phase 15 calculation. The earlier positive short-volatility shards were invalidated by E0145 because CALL/PUT sides were not included in the execution-leg join. The clean WEEK/MONTH rerun failed the target gate: WEEK best ₹30.82 base / -₹9.23 stress per active day; MONTH best -₹90.53 / -₹128.53; no ₹1,000-qualified cell. Phase 15 is retired.

Phase 16 is now the active frontier: intraday IV-skew tail credit verticals, 288 fixed cells per expiry shard, using the same cost model and doubled-slippage stress. Latest run 36021088602 is executing unit tests/data setup; no Phase 16 P&L accepted.


### 2026-09-24 — Phase 16 continuation checkpoint
- Phase 15 is retired. Corrected execution-leg validation did not clear the target: WEEK best was ₹30.82 base / -₹9.23 stress; MONTH best was approximately ₹-90.53 base / ₹-128.53 stress. Earlier positive Phase 15 artifacts remain invalidated by E0145.
- Phase 16 initial artifacts were invalid because the feature query filtered before the 15-minute lag and later produced zero trades from unnormalized execution joins. These were treated as implementation failures, not strategy evidence.
- Phase 16 corrected feature run produced 3,626 WEEK / 3,517 MONTH feature rows, 4,861 / 4,863 executable setups and ~480k execution-window rows, proving data coverage. The zero-trade output was then traced to DATE/TIMESTAMP join normalization (E0156).
- Phase 16 now caches execution outcomes by signal/side/width/hold/stop before mapping the 288 preregistered cells (E0157). Unit tests are required before numerical acceptance.
- Authoritative latest Phase 16 run: 36030055443, commit 7eefb6034014353c84e26e077c14655bb1eb5028. It is currently queued for a GitHub runner; no numerical result from this corrected run is accepted yet.


## 2026-09-25 — Phase 19 authoritative execution checkpoint

The corrected Phase 19 run `36042015205` on `phase-19-nifty-short-strangle-regime-v1` (head `2ed269eb2bc875671c818f5cde2707e0a97e4499`) is active. Both Base and Stress jobs passed unit tests and exact-expiry data acquisition and are currently executing the friction calculation. The run remains non-evidentiary until both jobs complete and the frozen 144-cell leaderboard, trade count, active-day net P&L, stress result and later-period validation gates are reviewed.

No parameter retuning has been performed after E0195.

## 2026-09-25 — Phase 19 v2 runtime supersession

The original Phase 19 corrected run `36042015205` is non-evidentiary after remaining in the friction step without artifacts. A static audit found E0197: the simulator still used the dataset `trading_day` field even after E0195 had established timestamp-derived IST `trade_date` as the authoritative key. Phase 19 v2 on `phase-19-nifty-short-strangle-regime-v2-runtime` preserves the frozen 144-cell grid and cost model, fixes the execution-date join, vectorizes exit-event calculation and performs exact cost-equivalence testing. Latest v2 run: `36043078139`; Stress has started cached-data acquisition and Base is queued. No P&L is accepted.


## 2026-09-25 — Phase 19 v3 authoritative execution

A clean Phase 19 v3 branch `phase-19-nifty-short-strangle-regime-v3-authoritative` was created to eliminate stale-run contention and report contamination. The frozen 144-cell short-strangle rule, exact-expiry dataset revision, cost model, Base slippage ₹0.20 and Stress slippage ₹0.40 are unchanged. The workflow cleans its output directory, runs unit tests, then Base and Stress sequentially and uploads only fresh Phase 19 evidence. Latest run: `36043694480`; tests and cached-data acquisition passed and Base friction is currently executing. No P&L has been accepted.


## 2026-09-25 — Phase 13 deduplication audit

Retrospective audit of the authoritative Phase 13 artifact found exact two-for-one duplication in every Base and Stress trade row. The simulator looped over both risk profiles even though `risk_id` was already part of the unique setup key. Exact-deduplication correction gives best full-sample mean active-day net ₹142.72 base / ₹112.72 stress, 0 target-qualified cells, and corrected nested-WFA mean test-window net ₹121.82 base / ₹91.82 stress. The published Phase 13 ₹285.45/₹225.45 result is invalidated and no retuning is permitted.


## 2026-09-25 — Phase 20 closure / Phase 21 active

Authoritative Phase 20 run 36045068043 completed Base and Stress for the frozen 384-cell global-gated Phase 13 interaction. It produced 3,872 trades; best mean active-day net was Rs 481.73 base and Rs 451.73 stress, with 0 target-qualified cells and 0 walk-forward windows. Phase 20 is retired without retuning. Phase 21 is now the active distinct hypothesis: fixed regime-switching long-gamma on expansion regimes and short-vega on calm regimes, with 60 frozen cells.

## Phase 24 — Falcon Spread numerical validation started — 2026-09-25

The user supplied a detailed transcript-derived rule set for Equity Income's Falcon Spread:
- Friday 5:3 near-week/far-week ratio-diagonal strangle around the 25-point premium zone;
- Monday purchase of five near-week outer wings on each side, one strike beyond the original shorts;
- hard stop required;
- full structure closed by Wednesday.

Phase 24 is preregistered on branch phase-24-falcon-spread-backtest-v1 with 270 frozen cells covering only unspecified timing/stop/strike-interpretation sensitivities. The source-primary cell is 25-point premium, diagonal far-week strike selection, and fixed Friday/Monday execution conventions.

No numerical result is accepted until Base and Stress runs complete and the artifact is inspected.

## Phase 24 diagnostic checkpoint — 2026-09-25

Run 36051595562 completed successfully through tests and data acquisition but produced 270 variants, 52 setups, and 0 trades in both Base and Stress. It was invalidated as evidence after E0224 identified a Friday-only trading_day filter in the multi-day series loader.

Corrected run 36052354346 removed that filter but still returned 52 setups and 0 trades in Stress. E0226 identified exact-timestamp intersection across multiple option legs as a likely sparse-quote blocker for stop marking. The correction replaces exact inner joins with fixed one-minute backward-asof alignment only, without future quotes.

The newest corrected code is committed on phase-24-falcon-spread-backtest-v1. Runs triggered by the latest correction are queued/active; no Falcon P&L is accepted until a clean corrected run completes.
## Phase 24 current-expiry correction — 2026-09-25

User clarification: the Falcon video is an older Thursday-expiry-era strategy. Current NIFTY weekly contracts expire Tuesday. NSE's June 25, 2025 circular revised NIFTY weekly expiry from Thursday to Tuesday for new contracts expiring on/after September 1, 2025; current NSE contract specifications list Tuesday as the weekly expiry day. citeturn431147search15turn431147search2

Phase 24 has therefore been corrected so the source's old "close by Wednesday to avoid Thursday 0-DTE" rule becomes **close on Monday before Tuesday expiry** for the current regime. Historical validation is expiry-aware: the exit session is the actual trading session immediately preceding each contract's expiry; Monday-expiry transition contracts are skipped because the source's Monday adjustment cannot occur before a Monday expiry.

The previously running Phase 24 computation using the old Wednesday timeout is superseded and will not be used for P&L. The new timing correction will be validated by the next clean Base/Stress run before any performance conclusion is accepted.
## Phase 24 timing correction — 2026-09-25 (finalized)

Correct current-rule geometry is now **Wednesday entry → Thursday adjustment → Monday exit** for present-day NIFTY weekly options that expire Tuesday. This is the exact expiry-relative translation of the source's old **Friday entry → Monday adjustment → Wednesday exit** under the former Thursday-expiry regime.

The simulator no longer hard-codes weekdays for the strategy mechanics. It derives the event sessions from the actual contract expiry using trading-session offsets: entry = expiry − 4 sessions; adjustment = expiry − 3 sessions; exit = expiry − 1 session. This preserves the source geometry across the historical Thursday-to-Tuesday expiry transition.

No P&L from the earlier incorrect timing implementation is accepted.

## Phase 24 execution status — 2026-09-25
The expiry-relative timing correction is implemented as Wednesday entry → Friday adjustment → Monday exit for current Tuesday-expiry NIFTY. A legacy `friday` variable defect in the strike-universe query was found and fixed before accepting any P&L. Latest corrected workflow runs are being re-executed after the timing, cost, caching and syntax fixes on GitHub Actions; no Phase 24 performance result is accepted yet.


## Phase 24 CI recovery — 2026-09-25
A stale pre-fix simulation run was holding the workflow concurrency group. CI was changed to cancel stale Phase 24 runs, and the corrected head is now queued as run **36054572240**. No performance result has been accepted from the cancelled/stale runs.


## Phase 24 timing correction — 2026-09-25 (second correction)
The expiry-relative mapping was rechecked against the source's historical Thursday-expiry sequence. The source geometry is **Friday entry → Monday adjustment → Wednesday exit**, corresponding to expiry−4, expiry−3, expiry−1 trading sessions. Therefore the current Tuesday-expiry analogue is **Wednesday entry → Thursday adjustment → Monday exit**. Earlier Friday-adjustment timing is superseded and produces no accepted P&L.


## Phase 24 cost-model correction — 2026-09-25
Current NSE STT rules are date-dependent: option-sale STT was 0.10% through 2026-03-31 and is 0.15% from 2026-04-01. The simulator now applies STT separately to entry and exit sale dates. Static-rate results are superseded. Corrected Phase 24 run **36055156251** is queued.


## Phase 24 performance correction — 2026-09-25
The simulator now caches repeated per-setup option series and mark panels across the 9 adjustment/stop combinations. This is an execution optimization only; it does not change strategy rules, timing or cost assumptions. Static-rate and pre-cache runs remain superseded.


## Phase 24 cost-model correction — NSE March 2026 transaction charges
The simulator now applies the NSE equity-options premium transaction charge date-wise: 0.03503% before 2026-03-01 and approximately 0.0355299% from 2026-03-01, in addition to date-aware STT. The pending prior run is superseded by the new correction.


## Phase 24 data coverage audit — 2026-09-25
The corrected TradeMarkk Stress artifact is **data-limited**: 270 variants, but only 32 executable setups / 5 unique entry dates across the nominal 2021-07 to 2026-08 window. The apparent 18 target-qualified variants are single-trade or otherwise tiny-sample observations and are rejected as evidence. External dataset documentation also states that TradeMarkk option coverage is partial. The family is therefore moving to an independent minute-data validation source before any strategy conclusion.


## Phase 24 execution coverage audit — 2026-09-25
Run **36056063674** completed the Stress friction job successfully. The Stress artifact reports 270 preregistered variants but only **32 executable setups / 5 unique entry dates** (2023-12-15, 2025-06-13, 2025-12-17, 2026-03-18, 2026-06-29) and 288 trade records. The apparent 18 target-qualified cells are dominated by single-trade observations and are rejected as strategy evidence. The audit indicates the restored exact-expiry cache was under-covered for the nominal research window; data-acquisition completeness must be validated before accepting any Phase 24 P&L. Base friction is still running from the same ref and will be treated as non-evidentiary until the cache problem is corrected.

Phase 24 next execution requirement: rebuild/reacquire a coverage-validated exact-expiry cache, then rerun the unchanged 270-cell grid. No parameter retuning is authorized from the sparse Stress leaderboard.


## 2026-09-25 — Phase 24 audit closure and Phase 25 launch

Phase 24 TradeMarkk execution is quarantined for evidence because its accepted artifact contained only 5 unique executable entry dates and 32 setup combinations across the nominal research window. The apparent target-qualified cells were dominated by single-trade observations. This is logged as E0237/E0238; no Phase 24 leaderboard cell is promoted.

Phase 25 is now the active independent replication branch: `phase-25-falcon-rissin-independent-v1`. It uses pinned Rissin/Upstox NIFTY 1-minute data revision `78b1c5468255d18cf492984bfe6fe4e3ac874d7c`, exact expiry metadata, the unchanged 270-cell Falcon grid, Wednesday→Thursday→Monday current-rule geometry, historical Friday→Monday→Wednesday geometry, Paytm Money/NSE costs, and doubled slippage. Promotion is blocked until the independent source produces adequate sample size and survives base/stress gates.


## 2026-09-25 — Testing pause / Equity Income archive program

At the user's direction, the previous daily/intraday strategy tournament is paused. The next research objective is a weekly strategy program sourced from the full Equity Income YouTube channel.

A fixed acquisition branch `equity-income-channel-archive-v1` contains Python-only channel discovery and transcript-fetching infrastructure, metadata/provenance manifests, integrity checks and an encrypted transcript archive design. The archive workflow requires the user-configured `EQUITY_INCOME_ARCHIVE_KEY` secret before its first execution.

Separate branches for Phases 26–35 are created. The new weekly economic target is **₹5,000 net per traded week at a fixed declared reference position size**, with Base/Stress friction, weekly risk statistics, nested WFA and later-period OOS validation.

## 2026-09-25 — Keyless archive activation

The Equity Income archive is now converted from the blocked GitHub-secret design to a keyless hybrid-encryption design.

- Canonical fixed branch: `equity-income-channel-archive-v1`
- Public key committed at `config/equity_income_archive_public_key.pem`
- Local decrypt utility: `scripts/decrypt_equity_income_transcript.py`
- No `EQUITY_INCOME_ARCHIVE_KEY` secret is required.
- A default-branch weekly workflow now runs the keyless Python archive and pushes encrypted transcript records to the fixed archive branch.
- Local hybrid-encryption round-trip test passed; the actual full-channel GitHub Actions acquisition has not yet been executed.

Trading research remains paused until the channel inventory/transcript archive is complete.

## 2026-09-25 — Keyless archive first-run syntax correction

The first live keyless archive run (GitHub Actions **36118488376**) reached Python execution and failed before channel discovery because two generated string literals in `archive_equity_income_keyless.py` contained literal newlines. This was a code-generation defect, not a data or encryption failure.

The canonical archive branch was corrected at commit `6bd858822117ac89afa6f62596b09c934b6b15e4`. A fresh run was triggered from `main`; no transcript data from the failed run was accepted.

## 2026-09-25 — Archive discovery-first correction

The first full keyless archive retry discovered **169 unique videos**, confirming channel enumeration, but every per-video yt-dlp metadata request hit YouTube anti-bot challenges. Because the script required successful metadata enrichment before transcript retrieval, that run produced no transcripts.

The archive implementation is now transcript-first: channel discovery supplies stable video IDs/URLs/titles/provenance; transcript retrieval proceeds without per-video metadata extraction. The metadata enrichment path is no longer a hard completion gate.

The canonical archive workflow was also corrected to operate on the canonical `equity-income-channel-archive-v1` branch and remain manual-only there; the unattended schedule remains on `main`.

## 2026-09-25 — Keyless archive CLI correction

Run **36122852931** failed immediately because the default-branch workflow passed `--workers 4` while the checked-out archive commit did not yet expose that option. The canonical keyless script now exposes one `--workers` option; no strategy or encryption design changed.

A fresh archive run will be used to test actual transcript acquisition.

## 2026-09-25 — InnerTube transcript acquisition added

The archive runner successfully enumerated all **169 channel videos**, but the transcript-first implementation still produced **169 transcript errors**. Current YouTube subtitle/player enforcement is the blocking mechanism rather than channel discovery or encryption.

The next deterministic Python acquisition method is now **InnerTube caption-track retrieval**, using the pinned yt-dlp client's own current definitions for TV/TV-downgraded/web-embedded clients. The script requests the player response, extracts `playerCaptionsTracklistRenderer.captionTracks`, and downloads the returned server-signed caption `baseUrl` as JSON3. No transcript text is generated by the model. citeturn686473search0turn863015search0

## 2026-09-25 — PO-token-enabled transcript acquisition

InnerTube caption-track retrieval did not solve the GitHub-runner acquisition problem: the full 169-video retry still failed. Current yt-dlp documentation identifies Proof-of-Origin tokens as relevant to YouTube subtitle/player requests, and the BgUtils provider is specifically designed to supply those tokens and has been used to address bot-check failures. citeturn863015search1turn408341view0

The archive now pins **bgutil-ytdlp-pot-provider 2.0.0**, starts its matching provider container on localhost, and makes PO-token-enabled yt-dlp the primary transcript acquisition path. The public-key archive design is unchanged; no GitHub secret is introduced. PyPI currently lists 2.0.0 as the latest provider release. citeturn434885search0

## 2026-09-25 — Resumable archive checkpoint

Run **36123998811** produced the first partial transcript success: **1/169** videos archived before 168 failures. That success was not previously durable. The subsequent workflow was changed to persist encrypted partial progress and to fail explicitly after commit when the archive remains incomplete.

The latest canonical archive snapshot currently records **169 discovered videos, 0 archived, 169 transcript errors** because the next run's new fallbacks were added after that snapshot. The next run will test the new acquisition ladder, now including curated Invidious caption APIs and a no-key transcript proxy, while retaining direct yt-dlp/PO-token, YouTube Transcript API, InnerTube and timedtext paths.

No trading/backtest phase has started; Phase 26 remains metadata-only until transcript acquisition is adequately resolved.

## 2026-09-25 — Equity Income archive continuation after 169 transcript failures

The latest completed archive snapshot established a stable 169-video inventory but 0 validated transcripts. All 169 transcript attempts were rejected by the GitHub runner's YouTube anti-bot layer; no transcript text was accepted as evidence.

The fixed archive branch equity-income-channel-archive-v1 has now been hardened with a single bounded Python acquisition ladder:
- PO-token-aware yt-dlp clients using the pinned bgutil provider;
- additional TV/embedded/VR client paths;
- youtube-transcript-api;
- direct InnerTube caption tracks;
- direct timedtext;
- one no-key third-party transcript endpoint as a last resort, with explicit provenance.

A regression test covers the timestamped fallback parser. Partial encrypted successes remain resumable and are committed even when the full-channel pass is incomplete.

Latest archive code commits:
- c644494194672a08f11c27822b8d81c099305fc8 — transcript acquisition ladder hardening
- 0e1bbf61ef1b354743eefcfe6cc7b2d66f4f69b0 — fallback parser regression test
- e1e5284dd4eed5af0b22b5a097919cd6659a87bd — bounded third-party fallback
- 524168276d4c7da28fc3ad0beef1674048224249 — fixed-branch manual workflow hardening
- 55e2e893a0bc3992a5395c3db14e130b0e2243f0 — archive status checkpoint

Trading/strategy testing remains PAUSED until the archive completion gate is passed. No transcript-derived strategy interpretation is promoted from the pre-archive catalogue.

## 2026-09-25 — Hardened archive rerun triggered

After the 169/169 transcript failure snapshot, the fixed archive branch was hardened with the bounded source-preserving transcript ladder, parser regression coverage, resumable partial writes and a fixed-branch manual workflow using the same PO-token provider.

Main trigger commit a26be8c4f9ca3c07b0bbe40732557e362edc63ed has been pushed. The next acceptance checkpoint is the resulting GitHub Actions run and its persisted archive snapshot. No trading research has resumed.

## 2026-09-25 — Archive CI trigger workaround

The connected GitHub tool surface does not expose workflow dispatch. A tightly scoped pull_request trigger was therefore added to the main archive workflow, and PR #36 was opened with only the archive trigger-file change.

PR #36 head: 1204ff2b0b4004eac29892df9c79b7d4cebfbcff. The workflow checks out the fixed equity-income-channel-archive-v1 branch and can persist partial encrypted results there.

No trading research has resumed; the next evidence checkpoint is the archive snapshot produced by this controlled run.

## 2026-09-25 — Hardened archive run currently executing

Controlled PR run 36125157622 is active on GitHub Actions. Job 108039526067 has successfully completed checkout, Python setup, dependency installation, PO-token provider startup, fallback probe, and public-key verification.

The Python archive acquisition step is currently executing. No transcript count, P&L, or strategy conclusion is accepted until the job completes and the encrypted archive manifest/snapshot is persisted.

Current fixed branch inventory remains 169 discovered videos and 0 persisted encrypted transcripts from the prior completed snapshot.

## 2026-09-25 — Equity Income archive result and next acquisition escalation

The hardened archive run 36126797339 recovered **39 of 169** public videos with **39/39 encrypted envelopes passing integrity validation**. The remaining 130 are unresolved because the GitHub-runner YouTube paths remain blocked and the previous no-key proxy commonly returned HTTP 200 without parseable timestamp lines.

The fixed archive branch has now added a structured youtubegpt.ai JSON caption fallback that returns millisecond-timed source caption segments and an explicit generated/human track flag. The next run will reuse the 39 persisted successes and attempt only the 130 unresolved videos.

Weekly trading research remains PAUSED until the archive gate passes.

## 2026-09-25 — Phase 27 source-rule evidence checkpoint

Phase 26 inventory passed with 169/169 verified transcripts. Phase 27 run 36130444316 then processed 71 title-selected strategy candidates with zero acquisition errors.

The automatic extractor intentionally did not promote any strategy to testing: all 71 candidates still require source-faithful manual reconstruction of economically material entry, adjustment, strike, stop, target and exit rules.

No Equity Income backtest is being accepted yet. The next step is timestamped transcript-context extraction and frozen rule-sheet construction.

## 2026-09-25 — Phase 29 data-feasibility checkpoint

Phase 29 run 36132032411 completed successfully. The 71 Equity Income candidate members split into 51 preliminary index-option-feasible, 16 data-limited, and 4 unresolved mappings. No member is backtest-eligible because strategy-specific quote completeness and historical lot-size validation remain outstanding.

Current research focus remains source-faithful rule reconstruction plus per-family data validation; no performance tuning is being used to fill unresolved rules.

## 2026-09-25 — Phase 27.2 reconstruction-priority result

Clean idempotent run **36132902868** completed all gates.

Evidence-completeness prioritization now identifies **8 T1**, **10 T2**, and **53 T3** candidates out of 71. This is an evidence-quality triage only; it is not a performance ranking and **0 candidates are backtest-eligible**.

The T1 set is the next source-fidelity reconstruction workload. Four T1/near-T1 candidates already have independent YouTube-description evidence cached in the repository; exact source rules remain transcript-dependent.

## 2026-09-25 — Phase 27.4 evidence precision checkpoint

Phase 27.4 run 36133569295 succeeded for all 8 T1 candidates. The parser now rejects clock-as-ratio/lot false positives, but **8/8 T1 records still contain at least one conflicting material rule field**. Therefore no T1 strategy is yet backtest-ready.

Next: frozen T1 source-resolution matrix and conflict reconciliation. Backtesting remains blocked until entry, strike, adjustment, stop/target, exit and contract-timing fields are source-resolved.

## 2026-09-25 — Target realignment for Equity Income YouTube research

User instruction: drop the former ₹1,000/day criterion for the YouTube-channel analysis and pursue at least ₹5,000 net per week with consistent weekly execution.

Research decision:
- Weekly target is measured at a fixed declared reference strategy position size, not by silently multiplying lots.
- Primary OOS economic targets are mean weekly net ≥ ₹5,000 and median weekly net ≥ ₹5,000.
- Consistency is measured with ≥70% positive eligible OOS weeks and ≥80% execution coverage unless the source rule explicitly defines a no-trade week.
- Paytm Money/NSE costs, date-specific lot sizes, Base/Stress slippage, WFA and later-period OOS remain mandatory.
- No existing Phase 29.4 source evidence or P&L conclusion is changed by this target update.


## 2026-09-25 — Phase 30 numerical gate opened, then invalidated pre-conclusion

The Equity Income YouTube program has now moved from source-rule formalization into numerical testing against the frozen 12-cell NIFTY Iron Dome family. The active objective is **₹5,000 NET per completed trading week**, with the weekly consistency gates already registered in the research plan.

The first vectorized Base run completed its coverage and simulation stages, but static result audit identified a critical data-loader defect: the option-series loader restricted each exact-expiry parquet to the single entry/adjustment `trading_day`, causing later marks to be carried forward instead of using the full timestamp range to expiry. Therefore **no Phase 30 P&L result from the affected run is accepted**.

The corrected rerun must:
1. load the full timestamp range from each pinned exact-expiry NIFTY parquet;
2. preserve the frozen 12-cell rule set;
3. run Base and doubled-slippage Stress;
4. report weekly mean, median, positive-week rate, execution coverage, worst week/drawdown and tail-risk metrics;
5. only then open the WFA/OOS gate.

The ₹1,000/day objective remains retired for the Equity Income YouTube program.

## 2026-09-25 — Phase 30 v7 corrected numerical rerun launched

Branch: `phase-30-equity-income-weekly-backtest-v7-corrected`.
The frozen 12-cell Iron Dome rules remain unchanged. v7 removes the invalid exact-expiry `trading_day` filter, preserves the full timestamp range through expiry, adds a multi-day loader regression test, and retains sequential Base then Stress execution.
No Phase 30 P&L is accepted until the corrected Base/Stress run completes and the resulting weekly distribution passes review.

## 2026-09-25 — Phase 30 v8 authoritative execution

Run **36157105595** on `phase-30-equity-income-weekly-backtest-v8-state-isolation` is the authoritative Phase 30 execution. Unit tests, pinned TradeMarkk acquisition/reuse and coverage validation passed; Base friction is currently executing.

A prior v8 Base artifact from run **36153419405** completed before persistence failed. Its numerical output is provisionally auditable but not a full Phase 30 conclusion: 262 eligible expiry files, 774 executable setups, 3,092 unique rows, no duplicate trade keys, and 0/12 cells meeting the weekly ₹5,000 preliminary gate. Best Base mean weekly net was **-₹585.85**, median **-₹1,193.72**, positive-week rate **39.77%**, execution coverage **98.85%**. Stress was not executed in that run.

No WFA/OOS selection is permitted until the current Base+Stress execution and artifact audit complete.

## 2026-09-25 — Phase 27.6 aRj evidence rerun queued

Controlled launcher-only PR **#86** created from `phase-27.6-trigger-rerun-20260925`; GitHub Actions run **36157884412** is queued. The workflow uses the fixed Python transcript extractor for video `aRjY_O6U3nQ` (Air Defense) and will persist only structured timestamped evidence/hashes. No strategy or P&L rule is changed and `backtest_allowed` remains false until the evidence is independently resolved.

## 2026-09-25 — Phase 27.7 Air Defense source-resolution branch prepared

A dedicated branch `phase-27.7-equity-income-air-defense-source-resolution-v1` now contains Python-only contextual transcript extraction for the Equity Income Air Defense candidate `aRjY_O6U3nQ`. The extractor records source-caption hashes plus timestamped context windows around delta, entry, adjustment, stop, structure, India-VIX/range and expiry-exit phrases. No numerical backtest is permitted until this evidence is reconciled into a deterministic rule card.

## 2026-09-25 — Phase 30 v8 final closure

Authoritative run **36157105595** completed all gates. Base and doubled-slippage Stress both completed successfully from the state-isolated engine. The frozen 12-cell Iron Dome family generated **3,092 unique rows**, 262 eligible expiry files and 774 executable setups. **0/12 cells passed** the weekly ₹5,000 mean/median/positive-rate/coverage gate in either friction setting.

Best Base cell: ID30_02_WING_60_RECENTER_BOTH, mean weekly net **-₹585.85**, median **-₹1,193.72**, positive-week rate **39.77%**, execution coverage **98.85%**, worst week **-₹10,486.42**, profit factor **0.68**, ES95 **-₹7,036.14**.

Best Stress cell: ID30_02_RISK_60_ONE_STRIKE_INSIDE, mean weekly net **-₹807.58**, median **-₹281.21**, positive-week rate **46.51%**, execution coverage **98.47%**, worst week **-₹9,274.17**, profit factor **0.62**, ES95 **-₹8,311.61**.

Phase 30 is **RETIRED**. No WFA/OOS or parameter selection is authorized from this family. The next distinct source-faithful family is Air Defense.

## 2026-09-25 — Phase 30.1 Air Defense active

Phase 30 v8 Iron Dome is retired after clean Base+Stress failure of the frozen 12-cell weekly gate. The next distinct source-faithful family is **Air Defense / India-VIX expected-range weekly short strangle** on branch `phase-30.1-equity-income-air-defense-v1`.

Authoritative workflow run **36159121044** is executing. Unit tests and the cached TradeMarkk source restore have passed; exact-expiry acquisition is in progress. The frozen 24-cell grid uses prior-day India VIX, 1/2-sigma range selection, expiry-relative entry offsets -2/-3 sessions, 09:30/10:00 entries, and NONE / 50%-distance / 75%-distance challenged-short reduction modes. Base brokerage is ₹10/order from the current Paytm Money F&O schedule; Base/Stress slippage remains ₹0.20/₹0.40.

No Air Defense P&L is accepted until Base and Stress complete and the artifacts pass duplicate-key, coverage and information-barrier audit.

## 2026-09-25 — Phase 30.1 Air Defense final closure

Authoritative run **36159644022** completed Base and Stress successfully after deterministic NSE India VIX acquisition fallback/chunking corrections. The frozen 24-cell Air Defense family generated complete Base/Stress artifacts with **42 normal Tuesday expiries** and **236 VIX observations**. **0/24 cells passed** the ₹5,000/week preliminary gate in either friction setting.

Best Base cell: **AD30_03_093000_S1_NONE**, 35 completed weeks, mean weekly net **₹2,126.52**, median **₹2,746.24**, positive-week rate **85.71%**, execution coverage **83.33%**, worst week **-₹23,467.55**, profit factor **3.00**, ES95 **-₹14,042.99**.

Best Stress cell: same rule cell, mean weekly net **₹2,070.63**, median **₹2,686.24**, positive-week rate **85.71%**, execution coverage **83.33%**, worst week **-₹23,519.55**, profit factor **2.93**, ES95 **-₹14,094.99**.

The family is **retired for the ₹5,000/week promotion gate**. No WFA/OOS or result-driven retuning is authorized. The source mechanism is economically positive in this sample but below the declared weekly target at the one-lot-per-short reference position.

## 2026-09-25 — Phase 30.2 Falcon independent weekly replication launched

New distinct branch: `phase-30.2-equity-income-falcon-weekly-v1`. This is the next source-faithful Equity Income candidate after Air Defense. The frozen 270-cell Falcon grid preserves the source's ratio-diagonal structure, current Tuesday-expiry timing analogue (Wednesday entry → Thursday adjustment → Monday exit), 25-point premium zone sensitivity, one-strike wing adjustment and hard-stop grid. The numerical gate has been rewritten for the current **₹5,000 net/week** objective rather than the retired ₹1,000/day criterion.

Authoritative workflow run **36160694325** is queued/pending. No Falcon P&L is accepted yet.



## 2026-09-25 — Phase 30.2 Falcon monitoring checkpoint
Phase 30.2 Falcon independent replication is executing under the frozen 270-cell weekly matrix. Both Base and doubled-slippage Stress have passed unit tests and exact Rissin acquisition; numerical friction is now running. No result is accepted until both jobs complete and the persisted summaries/leaderboards are audited.

The registered promotion gate remains mean weekly net ≥ ₹5,000, median weekly net ≥ ₹5,000, ≥70% profitable weeks, ≥20 completed weeks and ≥80% execution coverage, with Base/Stress costs and risk statistics disclosed. If the gate is not met, Falcon is retired without result-driven tuning and the next distinct source-faithful Equity Income candidate is opened.


## Parallel next-candidate research — 2026-09-25
While Falcon is computing, the next distinct Equity Income candidate has been identified for source-resolution work: **Bear Put Spread Attack Plan: When to Enter and How to Adjust** (YouTube video, published 2026-01-04). The public video description confirms that the source presents a bear-put-spread setup, explicit entry/exit rules, adjustments and stop-loss/risk-management rules, but the public indexed page does not expose the numerical rule details needed for a source-faithful backtest. citeturn371664youtube0turn117451youtube28

Research question: can the source-defined bear-put spread, once the archived Python-acquired transcript is deterministically recovered, be formalized into a current Tuesday-expiry NIFTY rule set that clears the ₹5,000/week consistency gate after realistic costs without contaminating the test set?

No numerical Bear Put test has been started and no rule values are being invented from the public description. The existing channel catalogue records this candidate as distinct from the prior short-vol families but requiring exact adjustment-rule recovery before execution.


## 2026-09-25 — Parallel research advance while Falcon computes
- **Falcon / Phase 30.2:** authoritative run 36160873596 remains in Base + Stress friction. No P&L accepted.
- **Source-resolution:** the Bear Put video `IpCuGEDxF1k` has a primary repository rule card, but economically material entry/adjustment/exit/stop fields remain unresolved. The public YouTube description confirms the strategy is a bear-put-spread method with entry/exit, adjustment and risk-management discussion, but that is corroboration only. citeturn358529youtube20
- **Archive infrastructure:** the keyless Python archive script was corrected and the canonical archive workflow was promoted to `main`; the workflow now targets `equity-income-channel-archive-v2-hybrid-keyless`, has manual dispatch plus a push trigger, and retains the weekly schedule. This addresses archive scheduling defect E0254 and script defect E0255.
- **Cost verification:** NSE's current STT page confirms option-sale STT is 0.10% through 2026-03-31 and 0.15% from 2026-04-01; NSE's Feb 27, 2026 transaction-charge circular confirms equity-options premium transaction charges of ₹3,503/crore before the March 1 revision and ₹3,553/crore from March 1, consistent with the date-aware model used by the current Falcon simulator. citeturn833533search0turn704031view0

## 2026-09-26 — Phase 30.2 Falcon runtime correction

The prior authoritative Falcon run **36213335815** was quarantined for runtime failure after Base and Stress both remained in `Run friction` beyond six hours. No P&L was accepted. A static audit identified repeated full-file Parquet scans per exact leg/strike and setup-level cached DataFrames retained through the whole sweep. Branch **`phase-30.2-falcon-runtime-fix-v1`** preserves the frozen 270-cell source-faithful grid and changes only execution architecture: bounded exact-expiry loading per calendar, in-memory snapshot/strike/series selection, one-calendar-at-a-time processing, explicit cache release and progress logging. Authoritative rerun **36216668042** is now executing; Base is in friction and Stress is queued by design.



## 2026-09-26 — Phase 30.2 Falcon final closure

Authoritative run **36220915944** completed the corrected 270-cell Falcon test. Base and Stress each produced **468 setups and 4,212 trade records**. **0/270 variants passed** the ₹5,000/week gate. The zero-setup artifacts from earlier runs are quarantined as engineering defects; the corrected run had 96.875% execution coverage on the leading measured cell.

Phase 30.2 is **CLOSED** without WFA/OOS. The next distinct Equity Income frontier is Bear Put source resolution (Phase 30.3/30.4), with numerical testing still blocked until its source ambiguities are frozen.

[Final audited Falcon report](https://github.com/vishnuvcr/Daily-Options/blob/phase-30.2-falcon-closure-v1/reports/phase30_2_falcon_final_result.md)


## 2026-09-26 — Main-branch synchronization

The previous Phase 30.2-era README/status text is superseded by the current YouTube research state.

**Phase 30.7 Bear Put:** completed authoritative run 36233110210; 18/18 shards successful; 6,480/6,480 aggregate cells; 0 cells passed Base and Stress weekly gate. Phase retired.

**Phase 30.8 No More Straddles:** active source-resolution-only phase on `phase-30.8-equity-income-no-more-straddles-source-resolution-v1`. Automated run 36234096126 passed the deterministic evidence tests and generated the source report. P&L remains blocked.

A main-branch launcher is currently running to reproduce the same source-resolution report from the pinned phase branch.

## 2026-09-26 — Live frontier: Phase 30.10

Phase 30.7 Bear Put is retired after the complete frozen matrix failed the ₹5,000/week promotion gate.

Phase 30.8 is source-blocked/data-limited; no P&L is accepted.

Phase 30.9 completed the India VIX study-window cache: **248 unique trading days, 2025-09-01 to 2026-08-31**. The initial 70-row NSE endpoint response was quarantined as incomplete; the subsequent deterministic paginated acquisition produced the full window and persisted it to the phase branch.

Phase 30.10 is the active numerical phase. Corrected workflow run **36234923838** is executing the preregistered **720 cells per regime** with Base slippage ₹0.20/order and Stress slippage ₹0.40/order. No result has been promoted yet.


## 2026-09-26 — Main synchronization: Phase 30.11 active

Phase 30.10 full-sample Air Defense result is audited: 1,440 total cells, 31 cells pass both Base and Stress. No live-trading conclusion is drawn from full-sample selection.

Phase 30.11 rolling WFA is now the active validation phase. Corrected run **36235740035** is executing three rolling folds. Phase 30.12 final holdout remains blocked pending WFA completion.


## 2026-09-26 — Phase 30.11 WFA corrected execution frontier

Phase 30.10 Air Defense full-grid validation is closed as discovery evidence:
- 720 Base cells, 720 Stress cells, 0 duplicates.
- 34 Base gate passes, 31 Stress gate passes.
- **31 cells pass in both friction regimes.**

Phase 30.11 is the current validation phase on `phase-30.11-strangle-air-defense-wfa-v1`.

Corrections logged before accepting any WFA result:
- **E0350:** stale Fold 3 synchronization — fixed.
- **E0351:** weekly event series overwrite — fixed; weekly cell results now accumulate all events.
- **E0352:** holdout calendar wording — fixed; reserved interval is 2026-08-03 through 2026-08-30 plus 2026-08-31.
- **E0353:** WFA aggregate cardinality — fixed; 24 regime/shard artifacts contain 144 leaderboard/weekly files total.

Current clean WFA run: **36236079821** is queued behind the previous stale computation run; the previous run will not be accepted. The clean run uses the corrected WFA engine and aggregate auditor. No WFA survivor has been accepted yet.

Phase 30.12 final holdout remains blocked until the WFA aggregate produces audited survivors.

## 2026-09-26 — Phase 30.11 WFA v2 checkpoint

The first packed-fold WFA topology was superseded after execution/cancellation issues. WFA v2 splits the validation into **72 independent jobs** (3 folds × 12 definition shards × 2 regimes) and audits 144 leaderboard/weekly files before any survivor is accepted.

Clean v2 run **36236257189** is queued. The preceding v2 run **36236194154** is closed with failures caused by the WFA engine scope declaration; those results are quarantined.

## 2026-09-26 — Phase 31.1 fixed-ratio audit and next frontier

Phase 31.1 tested the fixed NIFTY 09:30 ratio structure (2x +200 CE, 2x -200 PE, 1x -400 PE; exit 15:10) on the pinned exact-expiry source across 1,209 executable trading days / 260 calendar weeks.

- Base slippage ₹0.20/order: total net **-₹537,097.06**; mean weekly net **-₹2,065.76**; median weekly net **-₹2,534.49**; positive-week rate **26.92%**; max daily drawdown **-₹545,051.50**.
- Stress slippage ₹0.40/order: total net **-₹537,032.22**; mean weekly net **-₹2,065.51**; median weekly net **-₹2,534.28**; positive-week rate **26.92%**; max daily drawdown **-₹544,992.80**.
- Execution coverage: **97.97%**; 25 trading days had no complete executable trade.
- The ₹5,000/week mean, median and 70% positive-week gates all failed in both regimes.

Decision: **RETIRED / NEGATIVE**. No WFA or holdout promotion; no result-driven tuning is authorized. Implementation defects E0357–E0360 were fixed and logged before accepting this numerical result.

The next source-faithful frontier is **Phase 30.13 — Equity Income Low-VIX Diagonal source resolution** on branch `phase-30.13-equity-income-low-vix-diagonal-source-resolution-v1`. Numerical P&L remains blocked until its transcript-defined mechanics are fully resolved.


## 2026-09-26 — Phase 30.13 source-resolution closure

Phase 30.13 Low-VIX Diagonal is **SOURCE-BLOCKED / DATA-LIMITED**. GitHub Actions could reach the public YouTube page but deterministic Python caption acquisition was blocked by YouTube bot/IP controls across yt-dlp client modes and YouTubeTranscriptApi. No transcript evidence was accepted and no P&L was calculated. The candidate remains frozen for possible reopening when a reproducible primary-evidence path is available.

[Phase 30.13 final result](https://github.com/vishnuvcr/Daily-Options/blob/phase-30.13-equity-income-low-vix-diagonal-source-resolution-v1/reports/phase30_13_final_result.md) · [Phase 30.13 plan](https://github.com/vishnuvcr/Daily-Options/blob/phase-30.13-equity-income-low-vix-diagonal-source-resolution-v1/docs/phase30_13_plan.md)


## 2026-09-26 — Phase 31.2 forensic audit completed

Phase 31.1 is **quarantined**, not retired. Independent raw-data reconciliation completed successfully on branch `phase-31.2-phase31-1-forensic-audit-v1`: 30/30 stratified executed days matched the persisted ledger within ₹0.10 material tolerance, and the persisted 1,209-day ledger reconciles to its summary and weekly aggregation to numerical tolerance.

The audit found E0375: the persisted Phase 31.1 Base artifact uses raw gross P&L minus transaction/statutory costs, while the current checked-in simulator applies slippage inside execution gross. Reconstructed leg-level slippage totals **₹130,750.00**. After applying that missing friction, Base becomes **-₹667,847.06 total net**, **-₹2,568.64 mean weekly**, **-₹3,057.21 median weekly**, with **25.38% positive weeks** over 260 weeks. The earlier -₹537,097.06 figure is therefore retained only as the persisted artifact's accounting result, not as the final friction-corrected research result.

Next authorized step: provenance-corrected Phase 31.1 reproduction with one frozen accounting definition. No parameter optimization is authorized until that reproduction is frozen.

[Phase 31.2 plan](docs/phase31_2_forensic_audit_plan.md) · [audit branch](https://github.com/vishnuvcr/Daily-Options/tree/phase-31.2-phase31-1-forensic-audit-v1) · [final audit report](https://github.com/vishnuvcr/Daily-Options/blob/phase-31.2-phase31-1-forensic-audit-v1/reports/phase31_2/final_result.md)


## 2026-09-26 — Phase 31.5 ORB discovery closure

Phase 31.5 finite NIFTY ORB discovery completed successfully in authoritative run **36245174834** on branch **phase-31.5-finite-candidate-testing-v1**. The frozen 18-cell Base/Stress grid completed with persisted daily ledgers and diagnostics.

- Best Base cell: **30-min OR / 1.00×**, 512 trades, **₹47,477.23 total net**, **₹92.73 mean weekly net**, **47.13% positive weeks**.
- Same cell Stress: **₹25,955.61 total net**, **₹50.69 mean weekly net**, **45.90% positive weeks**.
- The grid did not meet the preregistered **₹5,000/week** mean/consistency target or **70% positive-week** gate.
- **Decision: Phase 31.5 closed; no candidate promoted to WFA/OOS and no result-driven tuning authorized.**

[Phase 31.5 plan](https://github.com/vishnuvcr/Daily-Options/blob/phase-31.5-finite-candidate-testing-v1/docs/phase31_5_plan.md) · [Phase 31.5 final result](https://github.com/vishnuvcr/Daily-Options/blob/phase-31.5-finite-candidate-testing-v1/reports/phase31_5/final_result.md)

## 2026-09-26 — Phase 31.7 current frontier

Phase 31.7 is the bounded OI/volume microstructure discovery family after Phase 31.6 closed negative. The data gate passed in run 36250115094 with 1,228 eligible sessions, 2,094 feature rows, 98.13% nearest-expiry coverage, and 72.39% next-expiry coverage.

Run 36250115094 is quarantined: Base and Stress completed but every signal cell had zero executable price coverage and validation failed before any P&L could be accepted. The defect chain is recorded as E0388/E0389/E0391.

The phase branch has now been corrected to use normalized timestamp-derived execution dates/times and to build null controls from the full feature panel before thresholding. Regression tests are persisted. The next authoritative run is run 9 from branch head eb4724c74ec064d7b5d7e6490186d8766e5188fc.
## 2026-09-26 — Phase 31.7 run 9 closure and run 10 preparation

Authoritative run 36250452425 (run 9) failed at pytest collection because the added regression test file contained a literal backslash-n sequence. No data gate, Base, Stress or P&L computation ran. E0393 is logged and the phase branch test file is corrected.

Run 10 will use the corrected Phase 31.7 branch head 0fc95b29fba8558070368bdeb076d793d494e2ab. No Phase 31.7 numerical result has yet been accepted.
## 2026-09-26 — Phase 31.7 run 10 closure and run 11 preparation

Run 36250549825 (run 10) reached the data gate, Base and Stress, but validation failed before any P&L acceptance. The concurrent branch audit then replaced the execution-price join with explicit per-expiry IST date and strike filters. That revision exposed E0394: strike_sql was referenced before definition in the query f-string. The branch source and regression tests are now corrected.

Run 11 will use the corrected Phase 31.7 branch head 408d8d1cbb1fa5e121d2d2f72f3778432d07fa60. No Phase 31.7 numerical result is accepted yet.
## 2026-09-26 — Phase 31.7 run 11 closure / run 12 diagnostic frontier

Run 36250863176 reached the data gate, Base and Stress, but validation again failed before any Phase 31.7 P&L was accepted. The latest phase branch now includes a raw five-sample execution-row probe; the authoritative launcher has been instrumented to run it after the data gate.

Run 12 will use the latest corrected Phase 31.7 branch head a73da3a7f29668b32f81fe1612b6ef31c40492a8. The probe is diagnostic only and does not change the frozen 12-cell strategy grid, entry/exit, slippage or cost model.
## 2026-09-26 — Phase 31.7 run 12 closure / run 13 frontier

Run **36251100372** completed unit tests, data gate, raw execution probes, Base and Stress, but validation failed because every executable trade set was still empty. The run-12 artifact showed valid source rows at 09:31/15:10; the remaining defect was localized to expiry-file selection, where feature expiry timestamps were compared against Python-date expiry-map keys.

The phase branch now normalizes feature expiry to a dedicated Python-date `expiry_key` before file selection, with a regression test. The launcher persist step now retries fetch/rebase after non-fast-forward push failures, and the workflow has non-canceling concurrency. Run 12 remains quarantined; no Phase 31.7 P&L is accepted.

 
## 2026-09-26 — Phase 31.7 closure / Phase 31.8 activation
 
Phase 31.7 is closed after authoritative run **36251189770**. The frozen OI/volume microstructure family produced **0/12 Base** and **0/12 Stress** promotion passes; all true cells had negative total net P&L. The best observed cell was VOL_IMB at threshold 0.40 with nearest expiry: **-₹191.41 mean weekly Base** and **-₹245.58 mean weekly Stress**, with **42.27% positive weeks**. No WFA/OOS was authorized.
 
Phase 31.8 is now the active bounded numerical frontier on `phase-31.8-global-overnight-transmission-v1`. The preregistered hypothesis, literature review, unit tests and manual launcher are persisted. The first gate is global-data acquisition/coverage; no P&L will be interpreted until the gate passes.

 
## 2026-09-26 — Phase 31.8 run 1 closure / corrected rerun
 
Run **36251942190** completed global-source acquisition but failed in the data-gate stage before any numerical testing. E0398 records the date-key type mismatch in the strict `merge_asof` alignment. The six global source files and manifest were persisted successfully; the branch is corrected to normalize NIFTY/global dates to datetime64 and a regression test now covers the prior-date barrier.
 
Next authoritative run: **Phase 31.8 run 2** from branch head `d73ce5e48d2d40a5a86bd53da91fec4629bab711`. No Phase 31.8 P&L is accepted.

 
## 2026-09-26 — Phase 31.8 run 2 closure / run 3 frontier
 
Run **36252076237** passed unit tests and global acquisition but failed before P&L in `build_panel`. The traceback showed that `main()` had passed a reduced NIFTY session frame without `time` into the session builder. E0400 records the actual defect; the earlier E0398 diagnosis is explicitly superseded.
 
The corrected branch now passes the full NIFTY index frame and has a regression test. Next authoritative run: **run 3** from phase branch head `c08f1bc9faa126dbe5eaae84075963d0a66f18be`.

 
## 2026-09-26 — Phase 31.8 run 3 closure / run 4 frontier
 
Run **36252203841** reached the no-lookahead panel but failed on a pandas datetime-unit mismatch in `merge_asof` (microseconds vs nanoseconds). E0401 is logged. The corrected branch now forces both merge keys to datetime64[ns] inside `build_panel` and covers the case with a regression test.
 
Next authoritative run: **Phase 31.8 run 4** from branch head `902098ba07db15388a99d32a0c5b5b74f038b3ad`.

 
## 2026-09-26 — Phase 31.8 run 4 closure / run 5 frontier
 
Run **36252301406** correctly skipped numerical discovery because its 95% coverage gate counted 64 deterministic pre-lookback sessions, yielding 94.788%. The phase plan now explicitly excludes only this required warm-up from the coverage denominator while retaining the full raw session count and strict prior-date barrier.
 
Next authoritative run: **Phase 31.8 run 5** from branch head `0963392cb7f1a9b73ec2e02e1bb66277f97f54bd`.

 
## 2026-09-26 — Phase 31.8 run 5 closure / run 6 frontier
 
Run **36252470696** stopped at a regression test that still reflected the old coverage denominator. E0403 is closed after aligning the test with methodological erratum 31.8-1. No data acquisition or P&L computation ran.
 
Next authoritative run: **Phase 31.8 run 6** from branch head `491644ec70ab9c5d69fb0d8b7db85cf21f383f43`.

 
## 2026-09-26 — Phase 31.8 run 6 closure / run 7 frontier
 
Run **36252561747** passed the corrected unit tests and global gate, then failed at Base-stage expiry attachment with a Timestamp-vs-date comparison. E0404 is logged; Stress/Validate were skipped and no P&L is accepted.
 
The branch now normalizes the NIFTY trade date to Python `date` before selecting the nearest expiry and has a regression test. Next authoritative run: **Phase 31.8 run 7** from branch head `2c04627733afb93d4bf0c08670b0da035e942874`.

 
## 2026-09-26 — Phase 31.8 run 7 closure / run 8 frontier
 
Run **36252692972** stopped at a regression-test fixture after the E0404 engine fix. E0405 is closed; no data acquisition or P&L ran. The corrected expiry regression now asserts the actual Python-date expiry keys.
 
Next authoritative run: **Phase 31.8 run 8** from branch head `5b933104ca2551d0890d71f1541c199b9087d151`.

 
## 2026-09-26 — Phase 31.8 run 8 closure / run 9 frontier
 
Run **36252808290** passed the corrected tests and global gate but failed in Base price loading on a stale `exit_ts` column reference. E0406 is logged; no P&L is accepted.
 
Next authoritative run: **Phase 31.8 run 9** from branch head `7094f73d35fa0c5644dc4e0ec98b40fd2283712f`.

 
## 2026-09-26 — Phase 31.8 CLOSED / Phase 31.9 activated
 
Phase 31.8 authoritative run **36252922418** completed its frozen 12-cell Base/Stress discovery, five-seed null controls and validation. **0/12** cells passed the ₹5,000/week promotion gate in Base and **0/12** in Stress. Best cell: **ASIA_LEAD | z=1.00 | H10_30**, mean weekly net **₹107.37 Base / ₹37.13 Stress**, 45.45% positive weeks, negative medians. The final report is persisted on the Phase 31.8 branch.
 
Phase 31.9 is now the next separately branched, preregistered family: **India VIX vs realized-volatility regime conditioning of NIFTY opening-gap direction**.

 
## 2026-09-26 — Phase 31.9 preregistration / ready to run
 
Phase 31.8 is closed without promotion after authoritative run **36252922418**: 0/12 cells passed the ₹5,000/week gate in Base or Stress.
 
The new active branch is `phase-31.9-vix-rv-gap-opening-direction-v1`. Phase 31.9 tests the prior India VIX / prior-only NIFTY RV20 ratio as a three-regime state variable for opening-gap FOLLOW versus FADE with 10:30/15:10 exits. The 12-cell grid, five full-panel null seeds, official NSE VIX acquisition, strict prior-data barrier, Base/Stress costs and promotion gate are frozen in the plan before computation.
 
No Phase 31.9 P&L is accepted yet. The next step is the authoritative unit-test + data-gate run.

## 2026-09-26 — Phase 31.9 run 1 closure / run 2 frontier

Run **36253432190** stopped in unit tests before data acquisition. E0407/E0408/E0409 are closed; no numerical computation ran.

Next authoritative run: **Phase 31.9 run 2** from branch head `d60f99a5da07a227dffa3ced9e18c9abb7b4c75d`.

## 2026-09-26 — Phase 31.9 run 2 closure / run 3 frontier

Run **36253528975** stopped in unit tests before acquisition. E0410 (null fixture) and E0411 (failure-path persistence) are closed.

Next authoritative run: **Phase 31.9 run 3** from branch head `f56b5102f3e95356fbc8f6109947fff7c9dc54ee`.
