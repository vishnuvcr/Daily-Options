# Daily-Options Research Lab

Research program for discovering and validating an intraday NSE options strategy with a target of at least Rs 1,000 NET profit per trading day per active lot, after brokerage, statutory charges, exchange charges, spread/slippage, and conservative execution assumptions.

## Current status — 2026-09-23

The repository began empty and is now an auditable research lab. No strategy has yet cleared the full promotion gate.

### Latest validated evidence

| Phase | Result | Evidence |
|---|---|---|
| Phase 2: simple directional option buying | FAIL | 244 trading days, 12 variants; best tested baseline averaged Rs -304.90 net/lot/day |
| Phase 3: vertical spreads | FAIL_PRELIMINARY | 21 chain days testable; best tested width averaged Rs -5.75 net/lot/day |
| Phase 3: VRP-filtered directional buying | FAIL_PRELIMINARY | Best recorded threshold averaged Rs -127.60 net/lot/day |
| Phase 3: unfiltered intraday short straddle | FAIL_PRELIMINARY | 244 trading days; best tested variant averaged Rs +233.91 net/lot/day, PF 1.35 |
| Phase 3: IV-RV-filtered short volatility | PENDING | Implemented; requires the next manual Phase 3 workflow run |

The short-volatility family is the strongest hypothesis tested so far, but it remains below the Rs 1,000 target and is not considered live-ready.

## Research design

The core design is pre-specified: leakage-safe timestamps, deterministic contract selection, date-aware lot sizes, Paytm Money brokerage, NSE statutory/exchange costs, conservative spread/slippage, nested walk-forward OOS tests, blocked bootstrap confidence intervals, adverse-cost stress and paper/shadow validation.

The research is open-ended within the defined phases, not an unlimited parameter-tuning loop. A family is retired after repeated OOS/robustness failure; a materially new hypothesis becomes a new branch.

## Phase map

| Phase | Branch | Goal | Status |
|---|---|---|---|
| 0 | `main` | Research charter, audit trail, cost model, repository scaffolding | COMPLETE |
| 1 | `phase-1-data-foundation` | Acquire/cache/validate spot, futures, option-chain, OI, IV and context data | COMPLETE-SCAFFOLD |
| 2 | `phase-2-baseline-tournament` | Benchmark ORB, VWAP, EMA and other simple intraday baselines | COMPLETE — GATE FAIL |
| 3 | `phase-3-options-structure` | Test spreads, short volatility, VRP and regime-conditioned structures | ACTIVE |
| 4 | `phase-4-walk-forward-selection` | Freeze candidates and validate on untouched rolling OOS windows | SCAFFOLDED |
| 5 | `phase-5-robustness` | Stress costs, slippage, delays, regimes and parameter perturbations | PLANNED |
| 6 | `phase-6-paper-shadow` | Validate execution behavior without live capital | PLANNED |
| 7 | `phase-7-manuscript` | Final structured manuscript, figures, appendices and future work | PLANNED |

## Key research documents

- [Research plan](https://github.com/vishnuvcr/Daily-Options/blob/main/docs/research_plan.md)
- [Research status](https://github.com/vishnuvcr/Daily-Options/blob/main/docs/research_status.md)
- [Error log](https://github.com/vishnuvcr/Daily-Options/blob/main/docs/error_log.md)
- [Literature and data review](https://github.com/vishnuvcr/Daily-Options/blob/phase-3-options-structure/docs/literature_review.md)
- [2026 cost model](https://github.com/vishnuvcr/Daily-Options/blob/main/config/cost_model_2026.yaml)

## Data and cost baseline

NSE's derivatives reports provide daily market activity, premium turnover for options, open interest, participant-wise open interest/trading volume and FII derivatives statistics. citeturn496856search0

The current model uses Paytm Money's announced flat Rs 20 brokerage structure as the broker baseline and versions statutory/exchange charges separately. NSE's current option-sale STT is 0.15% from 2026-04-01.

Candidate historical intraday sources include the 2017-2020 Zenodo NIFTY one-minute options archive, the 2020-2025 Hugging Face NIFTY options dataset, and the newer multi-underlying 1-minute dataset covering NIFTY/BANKNIFTY/SENSEX from 2024 onward. citeturn496856search7turn496856search5

## Important interpretation

The Rs 1,000/day number is a research target, not an assumed outcome. The repository will only promote a candidate after it survives realistic costs, OOS validation, robustness tests and execution-quality checks.


## Active research continuation — 2026-09-24

The user has changed the global stopping rule: the research continues until a reproducible strategy clears the Rs 1,000 net per active lot per trading day target under realistic costs and untouched out-of-sample validation.

Active bounded families:
- Phase 8 — phase-8-hybrid-ml-momentum-v2: hybrid NIFTY momentum/mean-reversion + ATM option confirmation, 96 pre-registered variants.
- Phase 9 — phase-9-regime-credit-spread-v1: regime-filtered bull-put/bear-call defined-risk credit spreads, 96 pre-registered variants.
- Phase 10 — phase-10-cross-index-1m-v1: NIFTY/BANKNIFTY relative-strength leadership + option confirmation using the public 1-minute index/options dataset, 128 pre-registered variants.

No result from these active runs is accepted yet. Earlier Phase 3/4 results remain frozen historical evidence and are not being silently retuned.

Known active run heads:
- Phase 8 v2: run 35937700542 — base numerical stage active.
- Phase 9: run 35937112092 — base numerical stage active on attempt 3.
- Phase 10: run 35937773719 — data acquisition/base stage active after the pytz dependency correction.

The promotion gate remains unchanged: positive net OOS expectancy; at least one untouched test window >= Rs 1,000/lot/day; realistic brokerage/statutory/exchange charges; base and doubled slippage reported; and no test-period parameter selection.

A preliminary backtest is never treated as a promoted strategy.

- Phase 11 preregistered: breakout-pullback continuation with ATM option OI/volume confirmation, 64 variants; held until needed after Phases 8-10.


## Current continuation checkpoint — 2026-09-24

The three active research families have not yet produced an accepted strategy result.

- Phase 8 v2: run 35937700542 failed with E0067; latest branch commit 7f1ed0b explicitly guards the executable `open` entry column and requires a fresh rerun.
- Phase 9: the previous runner-cancelled attempt was retried; current job 107543124203 is executing base friction.
- Phase 10: run 35937773719 failed with E0069; latest branch commit 7558c90 fixes pandas Series key access and requires a fresh rerun.
- Phase 11 is preregistered but not launched yet.

[Detailed active-run ledger](https://github.com/vishnuvcr/Daily-Options/blob/main/docs/active_run_ledger.md) · [Error log](https://github.com/vishnuvcr/Daily-Options/blob/main/docs/error_log.md) · [Research status](https://github.com/vishnuvcr/Daily-Options/blob/main/docs/research_status.md)

- Phase 11 is now executable on its dedicated branch: 64 pre-registered BANKNIFTY breakout-pullback/OI-confirmation variants, with base/stress slippage and walk-forward gates. A pre-run option-side selection defect was fixed before accepting any result.

- Phase 11 v2 / PR #12 corrects nearest-wing selection for PUT debit spreads before any P&L is accepted; the original Phase 11 PR #11 is retained as audit history.


### Updated evidence — 2026-09-24
- Phase 8 exact-ref v3: **RETIRED** — best base mean all-day net -₹6.13/lot/day; stress -₹36.13; 0/96 target-qualified.
- Phase 10 exact-ref v4: **RETIRED** — best base mean all-day net -₹113.62/lot/day; stress -₹136.48; 0/128 target-qualified; 0/3 positive WFA windows.
- Phase 9: active sharded computation remains underway after runner/resource remediation.
- Phase 11: preregistered breakout-pullback/OI family remains pending execution.

The next accepted candidate must still clear the unchanged ₹1,000 net/active-lot/day OOS gate after realistic costs and stress slippage.

## Latest completed research result — Phase 10

Phase 10 is retired after complete base/stress + walk-forward validation: best base ₹-113.62/lot/day, best stress ₹-136.48/lot/day, and no positive untouched WFA window. Result reports are archived under `reports/phase10/` on the Phase 10 execution branch. The active search continues through the remaining preregistered families and the next distinct phase only if required.


### Phase 12 parked frontier — 2026-09-24
A data-gated derivative-versus-spot lead/lag hypothesis is preregistered in [PR #20](https://github.com/vishnuvcr/Daily-Options/pull/20). It is intentionally parked while Phases 9 and 11 complete. No Phase 12 trading result exists.


### Phase 9 closure — 2026-09-24
Phase 9 is retired after corrected global evaluation: 96 variants, 106,152 trades, best base mean active-day net -₹168.79/lot/day, stress -₹228.79, and 0/16 positive WFA windows. The next live frontier is Phase 11.


### 2026-09-24 Phase 11 v5e authoritative execution
The current authoritative Phase 11 execution is isolated on phase-11-breakout-pullback-oi-v5e-authoritative (workflow run 35978104824). Unit tests and cached BANKNIFTY data acquisition passed; Base friction is in progress. No Phase 11 P&L is accepted until base, stress and decision/walk-forward gates complete. Earlier Phase 8/9/10 negative families remain frozen, and Phase 12 remains parked.


### Phase 12 closed / Phase 13 active frontier — 2026-09-24
Phase 12 v3 completed successfully and is retired after 52,476 entries / 51,760 executable trades. Best base net was -₹151.50/lot/active day; stress -₹211.50; all four walk-forward windows were negative. See `reports/phase12_v3_final_result.md` and `docs/research_status_2026-09-24.md`.

Phase 13 will use modern 1-minute NIFTY option data with a materially different volatility-regime + price-structure + defined-risk execution hypothesis. Current source candidates: `thetrademarkk/india-index-options-1m` and `rissin/nse-options-intraday`.


## 2026-09-24 live frontier checkpoint

Phase 14 is now frozen after independent later-period validation of the exact selected rule: 12 executable trades, ₹352.05/lot mean active-day net at base friction and ₹322.05 under doubled slippage, with only one contributing calendar year. It is not promoted.

Phase 15 is the active frontier. Run 36005428946 on branch phase-15-vrp-jump-brake-short-vol-v1 has passed tests, data acquisition and a timestamp/quote alignment probe; Base is currently running. No Phase 15 result is accepted yet.


## Current research frontier — 2026-09-24

Phase 15 has been retired after a clean rerun exposed and corrected a critical CALL/PUT execution-leg join defect (E0145). The corrected result did not reach the ₹1,000 net/active-lot/day target: WEEK best ₹30.82 base / -₹9.23 stress; MONTH best -₹90.53 / -₹128.53. Earlier positive Phase 15 artifacts are explicitly invalidated.

Phase 16 is active on `phase-16-iv-skew-tail-credit-v1`: a preregistered IV-skew tail credit-vertical family using 288 cells per expiry shard, realistic Paytm Money/NSE costs and doubled slippage. The first corrected feature run produced 3,626 WEEK / 3,517 MONTH feature rows and ~4,861 executable setups per shard; its zero-trade artifact was traced to a DATE/TIMESTAMP join defect and is invalidated. The latest corrected outcome-cache run is `36030055443`, currently queued for a runner; no Phase 16 P&L is accepted yet.

Research status: [docs/research_status.md](https://github.com/vishnuvcr/Daily-Options/blob/main/docs/research_status.md) · [error log](https://github.com/vishnuvcr/Daily-Options/blob/main/docs/error_log.md) · [Phase 16 hypothesis](https://github.com/vishnuvcr/Daily-Options/blob/phase-16-iv-skew-tail-credit-v1/docs/phase16_hypothesis.md)


## Current frontier sync — 2026-09-24

Phase 16 (`phase-16-iv-skew-tail-credit-v1`) is the current research frontier. Its previous run `36021088602` failed before numerical computation because of a unit-test syntax defect. The dedicated branch has since been corrected for hold-window enforcement, deterministic nearest-future-expiry selection, CI cancellation behavior, and IST-derived trade dates. Corrected branch head: `893247ee787ac7703c53965f2400ec304810278a`. No Phase 16 P&L is accepted yet; base/stress numerical execution and the subsequent untouched walk-forward promotion gate remain pending.


## Current research frontier — Phase 17 (2026-09-24)

Phase 16 is classified DATA-LIMITED because the pinned Artist23 source lacks the actual expiry and IV fields required by its preregistered hypothesis; no Phase 16 P&L is accepted.

Phase 17 is the active exact-expiry NIFTY family: premium-skew + option volume/OI pressure + spot-momentum confirmation, expressed as defined-risk credit spreads. It uses TradeMarkk revision 51ca58c, where NIFTY options are partitioned by exact expiry-date files and expose strike, option type, OHLCV and OI. The frozen tournament contains 384 variants with base/stress slippage of ₹0.20/₹0.40 per leg.

[Phase 17 plan](https://github.com/vishnuvcr/Daily-Options/blob/phase-17-nifty-exact-expiry-premium-skew-v1/docs/phase17_plan.md) · [Phase 17 status](https://github.com/vishnuvcr/Daily-Options/blob/phase-17-nifty-exact-expiry-premium-skew-v1/docs/research_status.md) · [Phase 17 workflow](https://github.com/vishnuvcr/Daily-Options/blob/phase-17-nifty-exact-expiry-premium-skew-v1/.github/workflows/phase-17-nifty-exact-expiry-premium-skew-v1.yml)


## Phase 19 parked fallback — 2026-09-24

Phase 19 is preregistered but **not launched**: global overnight returns + NIFTY opening gap as a pre-open regime classifier, followed by intraday volatility-compression confirmation and exact-expiry defined-risk iron-condor execution. The 384-cell grid is frozen in `docs/phase19_plan.md`; it will not be tuned from Phase 18 results.


## Active continuation checkpoint — 2026-09-25

Phase 19 — NIFTY short strangle regime is the active execution frontier on branch `phase-19-nifty-short-strangle-regime-v1`. Authoritative GitHub Actions run **36042015205** (commit `2ed269eb2bc875671c818f5cde2707e0a97e4499`) is currently running both Base and Stress friction. Unit tests and exact-expiry cached-data acquisition have passed; the numerical friction step is still in progress. No P&L is accepted until both friction jobs complete and the frozen 144-cell result is reviewed.

The E0195 correction derives option `trade_date` from the normalized UTC→IST timestamp; no strategy, regime, entry, exit, slippage or cost parameter was changed.

## Phase 19 runtime correction — 2026-09-25

The original corrected Phase 19 execution (run `36042015205`) is retained as non-evidentiary execution history because the friction stage stalled without artifacts. A pre-result audit found E0197: the simulation layer still used the dataset's `trading_day` key after E0195 had established timestamp-derived IST trade dates as authoritative.

The active corrected runtime is **Phase 19 v2** on `phase-19-nifty-short-strangle-regime-v2-runtime`. It keeps the frozen 144-cell strategy grid, exact-expiry source, Paytm Money/NSE cost model and Base/Stress slippage values unchanged, while using timestamp-safe execution joins, vectorized exit-event calculation and exact cost-equivalence tests. Latest run: `36043078139`; v2 unit tests passed, Stress is acquiring/reusing cached data and Base is queued. No Phase 19 P&L is accepted yet.


## Phase 13 integrity correction — 2026-09-25

A retrospective audit found that the authoritative Phase 13 Base/Stress trade artifacts contained exact two-for-one duplicates caused by the simulator expanding both risk profiles after `risk_id` was already part of the unique setup key. The published ₹285.45/₹225.45 near-miss is therefore invalid. Exact-deduplication recomputation gives a best full-sample mean active-day net of **₹142.72 base / ₹112.72 stress**, with 0 target-qualified cells and corrected nested-WFA mean test-window net of **₹121.82 base / ₹91.82 stress**. Phase 13 remains non-promoted; no tuning is authorized.


## Frontier update — 2026-09-25

### Phase 20 closure
Phase 20 (global-gated interaction with the corrected Phase 13 late-day volatility-acceleration family) completed authoritative Base and Stress run 36045068043. The frozen 384-cell grid produced 3,872 trades; best mean active-day net was ₹481.73 base / ₹451.73 stress; 0 cells reached ₹1,000 and 0 walk-forward windows cleared the promotion gate. The family is retired without retuning.

### Phase 21
Phase 21 is the distinct regime-switching hypothesis: long ATM straddle in expansion regimes and short OTM strangle in calm regimes. The first corrected runs returned zero setups because of a data/alignment implementation problem; those runs are non-evidentiary and are not treated as a strategy failure.

### Phase 22
Phase 22 is the corrected IV-skew tail-credit family. Run 36048113026 passed tests and data acquisition but failed in report assembly (pandas DataFrame received nested DataFrames). No P&L was accepted. The bug is logged as E0220 and the unchanged experiment has been rerun on the corrected branch.

### Phase 23 — Equity Income YouTube strategy discovery
The Equity Income YouTube channel is now a formal hypothesis source. The research catalogue records VIX expected-range/strangle-iron-condor “Air Defense”, low-VIX weekly structures, low-VIX calendars and diagonals, bear-put spread adjustments, Set & Strike/iron-fly structures, a NIFTY Jade Lizard, a monthly debit-spread + short-call overlay, and other channel ideas. Video descriptions/examples are treated as hypotheses only; no claim of profitability is accepted without the repository's cost-aware WFA/OOS tests.

[Phase 23 plan](https://github.com/vishnuvcr/Daily-Options/blob/phase-23-equity-income-video-hypotheses/docs/phase23_plan.md) · [Equity Income strategy catalogue](https://github.com/vishnuvcr/Daily-Options/blob/phase-23-equity-income-video-hypotheses/docs/equity_income_channel_catalog.md) · [Phase 23 workflow](https://github.com/vishnuvcr/Daily-Options/blob/phase-23-equity-income-video-hypotheses/.github/workflows/phase-23-equity-income-video-hypotheses.yml)

Channel: https://www.youtube.com/@equityincome

## Frontier update — 2026-09-25 — Falcon Spread

The supplied transcript for Equity Income's **Falcon Spread — Top Hedging Trick Public Won't Know** has been formalized as Phase 24. The frozen source mechanics are the 5:3 near-week/far-week ratio-diagonal structure around the ~25-point premium zone, one-strike outer-wing adjustment, hard stop and pre-expiry exit.

### Correct current-rule timing

The source-era Thursday-expiry sequence was **Friday entry → Monday adjustment → Wednesday exit**. Preserving the expiry-relative trading-session geometry gives the current NIFTY Tuesday-expiry analogue:

**Wednesday entry → Thursday adjustment → Monday pre-expiry exit.**

Current NSE specifications state that NIFTY 50 weekly options expire every Tuesday, moving to the previous trading day when Tuesday is a holiday. [NSE current contract specification](https://www.nseindia.com/static/products-services/equity-derivatives-nifty50)

Phase 24 v1 was run first on the pinned TradeMarkk exact-expiry source, but its cached option coverage was too sparse for inference: the corrected Stress artifact had only 5 executable entry dates. Those apparent high-P&L cells are rejected as evidence.

### Phase 24 v2 — independent-source validation

The frozen 270-cell Falcon grid is now being rerun without parameter retuning on independent **Rissin/Upstox 1-minute NIFTY option data**, pinned to raw-parquet revision 78b1c5468255d18cf492984bfe6fe4e3ac874d7c. The dataset documents 1-minute NIFTY options from October 2024 onward with explicit expiry, strike, option type and IST timestamps. [Rissin dataset](https://huggingface.co/datasets/rissin/nse-options-intraday) · [Pinned raw-parquet revision](https://huggingface.co/datasets/rissin/nse-options-intraday/commit/78b1c5468255d18cf492984bfe6fe4e3ac874d7c)

Latest v2 Actions run: 36057816149. The first data-acquisition attempts on revision c97e450 were rejected because that revision exposed auto-converted default/train shards instead of the documented raw file paths; this is logged as E0239. The workflow is now pinned to the raw-parquet revision and rerunning. No Phase 24 v2 P&L is accepted yet.

[Phase 24 v1 plan](https://github.com/vishnuvcr/Daily-Options/blob/phase-24-falcon-spread-backtest-v1/docs/phase24_plan.md) · [Phase 24 v1 simulator](https://github.com/vishnuvcr/Daily-Options/blob/phase-24-falcon-spread-backtest-v1/research/phase24_falcon_spread.py) · [Phase 24 v2 plan](https://github.com/vishnuvcr/Daily-Options/blob/phase-24-falcon-spread-backtest-v2-rissin/docs/phase24_v2_plan.md) · [Phase 24 v2 simulator](https://github.com/vishnuvcr/Daily-Options/blob/phase-24-falcon-spread-backtest-v2-rissin/research/phase24_falcon_spread_rissin.py) · [Phase 24 v2 workflow](https://github.com/vishnuvcr/Daily-Options/blob/phase-24-falcon-spread-backtest-v2-rissin/.github/workflows/phase24-falcon-spread-v2-rissin.yml)


## 2026-09-25 — Phase 24 audit and Phase 25 independent replication

Phase 24 Falcon results are quarantined after execution audit: only 5 unique executable entry dates were present in the nominal 2021-2026 TradeMarkk run, so single-trade target-qualified cells are not evidentiary. The exact frozen Falcon rules are being independently replicated in Phase 25 using Rissin/Upstox NIFTY 1-minute data, exact expiry metadata, the unchanged 270-cell grid, realistic Paytm Money/NSE costs and doubled slippage. The current-rule timing remains Wednesday entry → Thursday adjustment → Monday exit.

- [Phase 25 plan](https://github.com/vishnuvcr/Daily-Options/blob/main/docs/phase25_plan.md)
- [Research status](https://github.com/vishnuvcr/Daily-Options/blob/main/docs/research_status.md)
- [Error log](https://github.com/vishnuvcr/Daily-Options/blob/main/docs/error_log.md)


## 2026-09-25 — Equity Income archive / weekly research program

Trading-strategy testing is paused. A dedicated fixed acquisition branch now archives the public Equity Income YouTube channel with deterministic Python tooling, transcript provenance and integrity hashes. Full transcripts are stored encrypted rather than plaintext because this repository is public.

[Equity Income archive branch](https://github.com/vishnuvcr/Daily-Options/tree/equity-income-channel-archive-v1) · [Archive plan](https://github.com/vishnuvcr/Daily-Options/blob/equity-income-channel-archive-v1/docs/equity_income_channel_archive_plan.md) · [Weekly research plan](https://github.com/vishnuvcr/Daily-Options/blob/equity-income-channel-archive-v1/docs/equity_income_weekly_research_plan.md)

The next research program is weekly rather than daily, with a fixed-position reference target of **₹5,000 net per traded week**, plus Base/Stress costs, weekly drawdown analysis, nested WFA and later-period OOS validation. Separate Phase 26–35 branches have been created for the research pipeline.

## 2026-09-25 — Equity Income archive keyless activation

The fixed `equity-income-channel-archive-v1` branch now uses **RSA-OAEP + Fernet hybrid encryption** and no longer requires a GitHub repository secret. The repository stores only the public key; the matching private key is kept outside GitHub.

A weekly archive workflow is now on `main`. It checks out the fixed archive branch, runs the Python-only discovery/transcript program, verifies the encrypted envelopes, and pushes only new archive records back to the fixed branch. GitHub requires scheduled workflows to live on the default branch, so the schedule is intentionally hosted here while the research data remains isolated on the archive branch. citeturn445342search0turn445342search1

[Equity Income archive branch](https://github.com/vishnuvcr/Daily-Options/tree/equity-income-channel-archive-v1) · [Key management](https://github.com/vishnuvcr/Daily-Options/blob/equity-income-channel-archive-v1/docs/equity_income_archive_key_management.md) · [Archive plan](https://github.com/vishnuvcr/Daily-Options/blob/equity-income-channel-archive-v1/docs/equity_income_channel_archive_plan.md)

## 2026-09-25 — Equity Income archive retry correction

The first live full-channel attempt enumerated 169 videos but was stopped by YouTube anti-bot challenges during per-video metadata enrichment. No transcript result was accepted. The archive was corrected to use channel discovery as the deterministic inventory and retrieve transcripts directly by video ID/URL, so metadata-page challenges no longer block transcript acquisition.

## 2026-09-25 — Equity Income archive continuation checkpoint

The channel inventory is now confirmed at 169 public videos, but the latest completed archive pass produced 0 validated transcripts because YouTube anti-bot controls blocked every transcript attempt from the GitHub runner. This is treated as an acquisition failure, not as evidence that the videos lack transcripts.

The fixed branch equity-income-channel-archive-v1 has been hardened with a source-preserving Python fallback ladder using the pinned PO-token provider, additional yt-dlp clients, youtube-transcript-api, InnerTube, timedtext, and one bounded no-key third-party transcript endpoint with explicit provenance. Partial encrypted successes are committed for resumable continuation.

[Archive status](https://github.com/vishnuvcr/Daily-Options/blob/equity-income-channel-archive-v1/docs/equity_income_archive_status.md) · [Archive plan](https://github.com/vishnuvcr/Daily-Options/blob/equity-income-channel-archive-v1/docs/equity_income_channel_archive_plan.md)

Trading research remains paused until every current video has a validated transcript or an explicit durable failure record and the full integrity gate passes.

## 2026-09-25 — Equity Income archive acquisition checkpoint

Archive run 36126797339 recovered **39/169** public video transcripts; all 39 encrypted payloads passed integrity validation. The archive is still incomplete.

The next fixed-branch acquisition escalation adds a structured source-caption JSON fallback with millisecond timings and generated/human provenance. Existing successful transcripts are persisted and will be skipped on reruns.

[Archive status](https://github.com/vishnuvcr/Daily-Options/blob/equity-income-channel-archive-v1/docs/equity_income_archive_status.md) · [Archive plan](https://github.com/vishnuvcr/Daily-Options/blob/equity-income-channel-archive-v1/docs/equity_income_channel_archive_plan.md)

Trading research remains paused until the 169-video archive completion gate is satisfied.

## 2026-09-25 — Equity Income archive → Phase 26 → Phase 27 → Phase 28 continuation

**Archive gate passed:** 169/169 public channel uploads have encrypted transcript envelopes with 169/169 integrity checks.

**Phase 26:** deterministic 169-video inventory completed successfully. 71 videos were flagged as strategy candidates from title/family hints; no backtests were run.

**Phase 27:** run 36130444316 and its corrected segment-aware rerun 36130863898 completed successfully. 71 candidate videos were processed with zero acquisition errors. Structured evidence now preserves extracted facts plus source timestamps; 71/71 still require source-fidelity review because economically material rules remain incomplete.

**Phase 28:** corrected launcher run 36131564013 completed successfully. 71 candidate videos were conservatively mapped to 69 family clusters. No cluster is automatically backtest-eligible; 71/71 remain review-required.

**Current frontier:** source-faithful strategy reconstruction/deduplication is still the gate before weekly numerical testing. Phase 29 data-feasibility work is next. The weekly objective remains ₹5,000 net per traded week at fixed reference sizing, with Paytm Money/NSE costs, Base/Stress slippage and WFA/OOS gates.

[Phase 26 plan](https://github.com/vishnuvcr/Daily-Options/blob/phase-26-equity-income-inventory-v1/docs/phase26_plan.md) · [Phase 27 plan](https://github.com/vishnuvcr/Daily-Options/blob/phase-27-equity-income-reconstruction-v1/docs/phase27_plan.md) · [Phase 28 plan](https://github.com/vishnuvcr/Daily-Options/blob/phase-28-equity-income-dedup-v1/docs/phase28_plan.md) · [Research status](https://github.com/vishnuvcr/Daily-Options/blob/main/docs/research_status.md) · [Error log](https://github.com/vishnuvcr/Daily-Options/blob/main/docs/error_log.md)