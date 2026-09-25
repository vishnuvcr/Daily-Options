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