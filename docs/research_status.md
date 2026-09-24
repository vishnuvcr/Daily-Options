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

Correct current-rule geometry is now **Wednesday entry → Friday adjustment → Monday exit** for present-day NIFTY weekly options that expire Tuesday. This is the exact expiry-relative translation of the source's old **Friday entry → Monday adjustment → Wednesday exit** under the former Thursday-expiry regime.

The simulator no longer hard-codes weekdays for the strategy mechanics. It derives the event sessions from the actual contract expiry using trading-session offsets: entry = expiry − 4 sessions; adjustment = expiry − 2 sessions; exit = expiry − 1 session. This preserves the source geometry across the historical Thursday-to-Tuesday expiry transition.

No P&L from the earlier incorrect timing implementation is accepted.