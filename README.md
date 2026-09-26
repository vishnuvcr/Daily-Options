# Daily-Options Research Lab

Research program for discovering and validating reproducible NSE options strategies, with the current Equity Income YouTube program focused on a **weekly** objective rather than the retired daily-profit target.

## Current program target — 2026-09-25

**Equity Income / YouTube target:** at least **₹5,000 NET per completed trading week** at a fixed, explicitly declared reference position size, after Paytm Money brokerage, date-aware NSE/statutory charges, and conservative Base/Stress execution costs.

The earlier **₹1,000 NET per active lot per trading day** target applied to the pre-YouTube intraday tournament. It is **retired for the Equity Income channel analysis** and must not be used as the promotion criterion for Phases 29.5 onward.

“Consistent every week” is operationalized as a measurable research gate rather than an assumption:

- mean weekly net ≥ ₹5,000 on untouched OOS weeks;
- median weekly net ≥ ₹5,000 on untouched OOS weeks;
- ≥70% of eligible OOS weeks net-positive;
- ≥80% of eligible OOS weeks contain an executed source-faithful trade, unless the frozen source rule explicitly defines a no-trade week;
- Base and doubled-slippage Stress are both reported, with no test-period tuning;
- weekly drawdown, worst week, expected shortfall/CVaR, profit factor, trade concentration and calendar-regime stability are reported.

The final decision still requires nested walk-forward selection followed by independent later-period OOS validation. These gates are research criteria, not a claim that the ₹5,000 objective is achievable.

## Current research frontier

| Phase | Purpose | Status |
|---|---|---|
| 26 | Complete Python-acquired Equity Income channel archive | COMPLETE — 169/169 transcripts verified |
| 27 / 27.4 | Source-fidelity evidence extraction and precision cleanup | COMPLETE |
| 29.1 | Data readiness | COMPLETE |
| 29.2 | Contract coverage | COMPLETE |
| 29.3 | Iron Dome content validation | COMPLETE |
| 30 v8 | Iron Dome weekly numerical test | RETIRED — 0/12 cells passed the ₹5,000/week gate |
| 30.1 | Air Defense weekly replication | RETIRED — 0/24 cells passed; best frozen mean weekly net ≈₹2.13k |
| 30.2 | Falcon Spread weekly independent replication | **ACTIVE — authoritative run 36160873596, Base + Stress friction executing** |

Current frontier links: [Research status](https://github.com/vishnuvcr/Daily-Options/blob/main/docs/research_status.md) · [Research plan](https://github.com/vishnuvcr/Daily-Options/blob/main/docs/research_plan.md) · [Error log](https://github.com/vishnuvcr/Daily-Options/blob/main/docs/error_log.md) · [Phase 30.2 plan](https://github.com/vishnuvcr/Daily-Options/blob/phase-30.2-equity-income-falcon-weekly-v1/docs/phase30_2_falcon_weekly_plan.md)

## Current YouTube strategy program design

Research is limited to the archived **Equity Income** channel source set. Candidate rules are reconstructed from the Python-acquired transcript archive and verified against pinned historical option data. No model-generated transcript is treated as primary evidence.

For current NIFTY weekly strategies, expiry-relative session offsets are used so historical weekday labels are not blindly carried across the September 2025 Thursday→Tuesday expiry change. Contract selection, lot size, slippage and transaction charges remain date-aware.

### Phase 29.5 → Phase 30 sequence

Phase 29.5 must first freeze the source-faithful formalization matrix and prove contract/lot readiness. Only then can Phase 30 calculate weekly P&L for the frozen cells. Phase 30 must report the ₹5,000 weekly target and the consistency metrics above; the old daily target is out of scope.

### Weekly economic normalization

Because Equity Income strategies can be multi-leg and ratio-based, performance is compared at a **declared reference strategy position size**. Every leg, lot ratio, brokerage charge, statutory charge, slippage assumption and capital requirement must be disclosed so ₹5,000/week is not achieved through hidden scaling.

## Historical intraday tournament

The remaining Phase 0–25 material below is retained as auditable historical research. Those earlier intraday phases used the former ₹1,000/active-lot/day target and are not the active stopping rule for the Equity Income YouTube program.

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

## 2026-09-25 — Phase 29 data-feasibility result

Phase 29 launcher run **36132032411** completed. Of 71 candidate family members, 51 have a preliminary 1-minute index-option data path, 16 are data-limited (primarily stock-option/LEAPS-type requirements), and 4 remain unresolved. Quote completeness and historical lot-size verification are still pending, so **0 are backtest-eligible**.

Current research remains on source-fidelity reconstruction and coverage validation before weekly numerical testing.

[Phase 29 plan](https://github.com/vishnuvcr/Daily-Options/blob/phase-29-equity-income-data-feasibility-v1/docs/phase29_plan.md) · [Phase 29 report](https://github.com/vishnuvcr/Daily-Options/blob/phase-29-equity-income-data-feasibility-v1/reports/phase29_data_feasibility.csv)

## 2026-09-25 — Phase 27.1 / 27.2 source-fidelity continuation

Phase 27.1 context-aware evidence extraction completed for all 71 strategy candidates with zero acquisition errors. It now retains structured facts with source timestamps rather than flattening transcript context.

Phase 27.2 then produced an evidence-completeness triage of **8 T1 / 10 T2 / 53 T3** candidates. This is only a reconstruction-priority metric; **no backtesting is permitted yet**.

The next step is frozen rule-sheet reconstruction of the highest-information T1 candidates, with external YouTube-description evidence used only as corroboration; the archived source captions remain primary.

## 2026-09-25 — Phase 29.1 Equity-Income data readiness

Phase 29.1 completed on dedicated branch `phase-29-equity-income-data-feasibility-v1` and workflow run **36133844640**. The readiness pipeline now inventories the exact pinned Hugging Face revisions with the official Python client rather than treating directory metadata as market-data presence.

### Accepted Phase 29.1 evidence

| Item | Result |
|---|---|
| Candidate registry | 71 Equity-Income candidate rows |
| Preliminary data-feasible families | 51 |
| Data-limited families | 16 |
| Unresolved families | 4 |
| TradeMarkk revision | `51ca58c` |
| Rissin revision | `78b1c5468255d18cf492984bfe6fe4e3ac874d7c` |
| Actual TradeMarkk NIFTY 1-minute option partitions | 267 Parquet expiry files |
| Actual Rissin NIFTY intraday partitions | 4 Parquet year files |
| Bid/ask execution quotes verified | 0 |
| Strategy-specific quote completeness verified | 0 |
| Fully verified historical NIFTY lot-size schedule | 0 |
| Phase 30 numerical backtest gate | **BLOCKED** |

The public source cards describe the TradeMarkk dataset as 1-minute NIFTY/BANKNIFTY/SENSEX spot and option-chain OHLCV(+OI) data with exact-expiry option files, while Rissin documents 1-minute NIFTY/BANKNIFTY/SENSEX coverage and a canonical Parquet schema; Rissin also notes that Upstox intraday OI is unavailable/NaN. These sources are treated as research data, not as perfect executable bid/ask quotes. citeturn308533search0turn365658search0

NSE currently specifies Tuesday expiry for NIFTY weekly contracts, with the previous trading day used when Tuesday is a trading holiday. Historical expiry and lot-size rules are versioned rather than back-projected. NSE's 2025 expiry circular moved NIFTY weekly expiry from Thursday to Tuesday, and the exchange publishes current contract specifications separately. citeturn557934search0turn557934search27

### Phase 29.1 research documents

- [Phase 29.1 plan](https://github.com/vishnuvcr/Daily-Options/blob/phase-29-equity-income-data-feasibility-v1/docs/phase29.1_data_readiness_plan.md)
- [Phase 29.1 source inventory](https://github.com/vishnuvcr/Daily-Options/blob/phase-29-equity-income-data-feasibility-v1/data/equity_income/phase29_readiness_source_inventory.json)
- [Phase 29.1 readiness matrix](https://github.com/vishnuvcr/Daily-Options/blob/phase-29-equity-income-data-feasibility-v1/reports/phase29_readiness_matrix.csv)
- [Phase 29.1 summary](https://github.com/vishnuvcr/Daily-Options/blob/phase-29-equity-income-data-feasibility-v1/reports/phase29_readiness_summary.json)
- [Phase 29.1 workflow](https://github.com/vishnuvcr/Daily-Options/blob/phase-29-equity-income-data-feasibility-v1/.github/workflows/phase-29.1-equity-income-data-readiness-v1.yml)
- [Research status](https://github.com/vishnuvcr/Daily-Options/blob/phase-29-equity-income-data-feasibility-v1/docs/research_status.md)
- [Error log](https://github.com/vishnuvcr/Daily-Options/blob/phase-29-equity-income-data-feasibility-v1/docs/error_log.md)

### Next research phase

Phase 29.2 will perform strategy-specific contract coverage and exact-expiry joins for the 51 preliminary-feasible candidates, while preserving the hard execution-quality gate: no bid/ask inference, explicit slippage/transaction costs, historical lot sizes from dated exchange evidence, and no future information. Phase 30 cannot start from aggregate source availability alone.


## 2026-09-25 — Phase 29.2 Equity-Income contract coverage

Phase 29.2 workflow **36135151445** completed successfully on branch `phase-29.2-equity-income-contract-coverage-v1` and pull request [#70](https://github.com/vishnuvcr/Daily-Options/pull/70).

The 71 Phase-28 candidate rows were cross-checked against the frozen Equity Income archive: 169 discovered videos and 169 archived transcript-manifest records. Contract-readiness was then tightened beyond Phase 29.1 aggregate source availability.

| Contract-readiness state | Rows |
|---|---:|
| UNDERLYING_UNRESOLVED | 54 |
| DATA_PARTIAL_INDEPENDENT_GAP | 10 |
| RULE_RECONSTRUCTION_REQUIRED | 4 |
| LONG_DATED_DATA_LIMITED | 1 |
| CONTRACT_READY_FOR_CONTENT_JOIN | 2 |

The two currently contract-ready rows are the duplicate **NIFTY Iron Dome** candidates (videos published Apr 30 and May 2, 2026). Their public YouTube descriptions describe an Ironfly-adjustment framework for market movement, but exact strike/leg/timing rules still need content-level reconstruction before any P&L test. citeturn650277youtube0turn650277youtube1

All 71 rows remain `backtest_allowed=NO`. Phase 30 is still blocked pending exact leg composition, dated expiry/lot-size joins, contract-content coverage, and an executable-price model with explicit slippage, brokerage and statutory charges.

### Phase 29.2 research documents

- [Phase 29.2 plan](https://github.com/vishnuvcr/Daily-Options/blob/phase-29.2-equity-income-contract-coverage-v1/docs/phase29.2_contract_coverage_plan.md)
- [Phase 29.2 contract matrix](https://github.com/vishnuvcr/Daily-Options/blob/phase-29.2-equity-income-contract-coverage-v1/reports/phase29_2_contract_coverage_matrix.csv)
- [Phase 29.2 summary](https://github.com/vishnuvcr/Daily-Options/blob/phase-29.2-equity-income-contract-coverage-v1/reports/phase29_2_summary.json)
- [Phase 29.2 source manifest](https://github.com/vishnuvcr/Daily-Options/blob/phase-29.2-equity-income-contract-coverage-v1/data/equity_income/phase29_2_contract_manifest.json)
- [Phase 29.2 workflow](https://github.com/vishnuvcr/Daily-Options/blob/phase-29.2-equity-income-contract-coverage-v1/.github/workflows/phase-29.2-equity-income-contract-coverage-v1.yml)
- [Phase 29.2 error log](https://github.com/vishnuvcr/Daily-Options/blob/phase-29.2-equity-income-contract-coverage-v1/docs/error_log.md)

### Next phase

Phase 29.3 will take the two NIFTY Iron Dome candidates into exact contract-content validation: reconstruct the leg sequence and adjustments from the archived evidence, map every leg to the pinned 1-minute option contracts, verify dated NIFTY expiry/lot-size rules, and establish a reproducible entry/adjustment/exit specification. No trading result will be accepted until this gate passes.


## 2026-09-25 — Phase 29.3 NIFTY Iron Dome content validation

Phase 29.3 workflow **36135786342** completed successfully on branch `phase-29.3-equity-income-iron-dome-content-v1` and pull request [#72](https://github.com/vishnuvcr/Daily-Options/pull/72).

Both contract-ready Iron Dome videos were processed with Python transcript tooling. The primary `youtube-transcript-api` method was blocked by YouTube/cloud-IP restrictions, so the workflow used a deterministic `yt-dlp` auto-caption fallback. Seven relevant pinned TradeMarkk NIFTY expiry Parquet files were then content-inspected successfully; the verified schema includes timestamp, strike, option_type, expiry, OHLCV and open_interest.

The source evidence now supports a **provisional** weekly Iron Fly/Iron Dome reconstruction: symmetric 200-point wings in an illustrated example, a 60% adjustment mark, no more than two planned adjustments, Monday/Tuesday adjustment examples, and an expiry-day theta-decay scenario. It does **not** yet freeze the exact entry timing, the mathematical definition of the 60% trigger, the complete adjustment formulas, lot ratios or the exact exit rule. Therefore no P&L result is being treated as source-faithful yet.

### Phase 29.3 documents

- [Iron Dome rule reconstruction](https://github.com/vishnuvcr/Daily-Options/blob/phase-29.3-equity-income-iron-dome-content-v1/reports/phase29_3_iron_dome_rule_reconstruction.md)
- [Rule evidence](https://github.com/vishnuvcr/Daily-Options/blob/phase-29.3-equity-income-iron-dome-content-v1/reports/phase29_3_iron_dome_rule_evidence.json)
- [Expiry content checks](https://github.com/vishnuvcr/Daily-Options/blob/phase-29.3-equity-income-iron-dome-content-v1/reports/phase29_3_expiry_content_checks.json)
- [Phase 29.3 summary](https://github.com/vishnuvcr/Daily-Options/blob/phase-29.3-equity-income-iron-dome-content-v1/reports/phase29_3_summary.json)
- [Phase 29.3 workflow](https://github.com/vishnuvcr/Daily-Options/blob/phase-29.3-equity-income-iron-dome-content-v1/.github/workflows/phase-29.3-equity-income-iron-dome-content-v1.yml)

### Next phase

Phase 29.4 will freeze a pre-registered **variant matrix** for the remaining source ambiguities instead of silently choosing one interpretation. Candidate dimensions are entry timing, the formal definition of the 60% trigger, first/second adjustment strike movement, and exit convention. Variants will be evaluated with historical lot-size rules and full transaction-cost/slippage modelling before any candidate is allowed into walk-forward testing.


## Research frontier — 2026-09-25 — Equity Income / Iron Dome

The current Equity Income research frontier is **Phase 29.4: NIFTY Iron Dome source-fidelity reconstruction**. Phase 29.1 established source/data feasibility, Phase 29.2 established strict contract-content readiness for the two duplicated Iron Dome candidates, and Phase 29.3 programmatically acquired and content-checked both source videos plus seven relevant pinned NIFTY expiry partitions. Phase 29.4 then converted the source captions into a structured rule-fact ledger.

The current evidence supports a weekly NIFTY Iron Fly / Iron Dome family with two adjustments and a source-described 60% adjustment mark. The source also contains a 200-point balanced-wing illustration and directional/deeper-ITM adjustment examples. The exact mathematical meaning of the 60% trigger, initial entry clock, precise leg movements, universal wing width, lot ratio and hard exit remain unresolved, so **no numerical backtest has been accepted and Phase 30 remains blocked**.

NIFTY weekly options currently expire on Tuesday; NSE moved the weekly expiry from Thursday to Tuesday effective September 2025. The April/May 2026 Iron Dome videos are therefore already in the Tuesday-expiry regime and should not be shifted back to Thursday-based day labels. Current NIFTY weekly/monthly strikes use a 50-point interval. The October 2025 NSE lot-size revision set NIFTY's revised market lot at 65, with the existing weekly/monthly lot continuing through the December 30, 2025 expiry; the Phase 29.5 contract-readiness work will therefore use date-specific lot files rather than a hard-coded lot size.

**Next bounded phase: Phase 29.5 — source-fidelity formalization + contract/lot readiness.** It will freeze a small, preregistered set of source-anchored interpretations, verify dated Tuesday-expiry/lot mapping, and only then open the numerical Phase 30 weekly backtest with Paytm Money/NSE costs and Base/Stress slippage.

[Research status](https://github.com/vishnuvcr/Daily-Options/blob/main/docs/research_status.md) · [Error log](https://github.com/vishnuvcr/Daily-Options/blob/main/docs/error_log.md) · [Phase 29.4 plan](https://github.com/vishnuvcr/Daily-Options/blob/phase-29.4-equity-income-iron-dome-rule-reconstruction-v1/docs/phase29.4_iron_dome_rule_reconstruction_plan.md)

### Phase 30 v7 correction — 2026-09-25
Dedicated branch: `phase-30-equity-income-weekly-backtest-v7-corrected`.
The first vectorized result was quarantined after a pre-result audit found that the exact-expiry option loader filtered by a single trading day. v7 uses the complete timestamp range within each exact-expiry file, adds a multi-day regression test, and keeps the frozen 12-cell rule/cost model unchanged. Base and Stress must complete before any strategy conclusion.

### Phase 30 v7 invalidation / v8 correction — 2026-09-25
The completed v7 Base/Stress run is permanently quarantined: a shared mutable-leg-state bug caused later parameter cells to skip closing orders and report opening-credit-only P&L. The active branch is `phase-30-equity-income-weekly-backtest-v8-state-isolation`, with state-isolation regression tests and the frozen rules unchanged. WFA/OOS remains blocked until v8 completes and passes the audit gate.

### Phase 30 v8 execution checkpoint — 2026-09-25

Authoritative v8 run **36157105595** is executing on `phase-30-equity-income-weekly-backtest-v8-state-isolation`. Unit tests and pinned-data coverage checks passed; Base friction is in progress. A prior v8 Base-only artifact (run 36153419405) is provisionally auditable: 262 exact-expiry files, 774 executable setups, 3,092 unique trade rows across all 12 frozen cells, and **0/12 preliminary-pass cells**. Best Base cell was **-₹585.85 mean weekly net**, with **39.77% positive weeks** and **98.85% execution coverage**. This is not yet the final Phase 30 result because the prior run failed before Stress; the current run is repeating Base then Stress cleanly.

### Phase 30 v8 final closure — 2026-09-25

Authoritative run **36157105595** completed Base and doubled-slippage Stress successfully. The frozen 12-cell Iron Dome family produced **3,092 unique trade rows** across 262 eligible expiry files and 774 executable setups. **0/12 cells met the ₹5,000/week preliminary gate** in either friction setting. Best Base mean weekly net was **-₹585.85**; best Stress mean weekly net was **-₹807.58**. No cell reached the 70% positive-week target; execution coverage was high, so the failure is economic rather than primarily a coverage failure. Phase 30 is retired without WFA/OOS selection or retuning.

The next distinct Equity Income family is the source-resolved **Air Defense / India-VIX expected-range weekly short-volatility system**; its Python transcript evidence is being converted into a bounded numerical grid before testing.

### Phase 30.1 — Air Defense active frontier

The Iron Dome family is retired after the complete v8 Base+Stress audit. Phase 30.1 now tests the **Air Defense / India-VIX expected-range weekly short-strangle** family on `phase-30.1-equity-income-air-defense-v1`. The source evidence is Python-acquired and hashed; the 24-cell numerical grid is frozen before execution. [Phase 30.1 plan](https://github.com/vishnuvcr/Daily-Options/blob/phase-30.1-equity-income-air-defense-v1/docs/phase30_1_air_defense_plan.md)

### Phase 30.1 closure — Air Defense

Phase 30.1 completed Base and Stress on 42 normal Tuesday expiries and 236 official NSE India VIX observations. **0/24 frozen cells passed the ₹5,000/week gate.** Best cell: mean weekly net ₹2,126.52 Base / ₹2,070.63 Stress, 85.71% positive weeks and 83.33% execution coverage. The family is retired without WFA tuning.

### Phase 30.2 active frontier — Falcon Spread

The next Equity Income family is the source-formalized Falcon Spread. The new branch `phase-30.2-equity-income-falcon-weekly-v1` uses the current Tuesday-expiry analogue **Wednesday entry → Thursday adjustment → Monday pre-expiry exit** and a frozen 270-cell grid. The gate is now the declared **₹5,000 net/week** target with weekly consistency and cost stress. [Phase 30.2 plan](https://github.com/vishnuvcr/Daily-Options/blob/phase-30.2-equity-income-falcon-weekly-v1/docs/phase30_2_falcon_weekly_plan.md)



## 2026-09-25 — Phase 30.2 Falcon live checkpoint
The former daily ₹1,000 objective is not being used for the Equity Income YouTube program. Falcon is being tested against the frozen **₹5,000 NET per completed trading week** consistency gate. Authoritative run **36160873596** is executing on `phase-30.2-equity-income-falcon-weekly-v1`: Base and Stress have passed unit tests and exact Rissin NIFTY acquisition, and both are running the numerical friction stage. No Falcon P&L is accepted until completion and artifact audit. See [active run ledger](https://github.com/vishnuvcr/Daily-Options/blob/main/docs/active_run_ledger.md), [research status](https://github.com/vishnuvcr/Daily-Options/blob/main/docs/research_status.md), and [Phase 30.2 plan](https://github.com/vishnuvcr/Daily-Options/blob/phase-30.2-equity-income-falcon-weekly-v1/docs/phase30_2_falcon_weekly_plan.md).


## 2026-09-25 — Research continuation checkpoint
Falcon Phase 30.2 remains the authoritative active numerical run (36160873596; Base + Stress friction still executing). In parallel, the Equity Income transcript archive infrastructure was advanced: the malformed keyless Python archive writer was corrected, and the canonical archive workflow was promoted to `main` so the weekly schedule and manual dispatch can operate while updating the dedicated archive branch. The Bear Put candidate remains source-resolution blocked until its material rules are recovered from primary transcript evidence; no public description is being substituted for missing rule fields.

### Phase 30.2 Falcon runtime correction — 2026-09-26

The initial corrected Falcon run **36213335815** is quarantined: Base and Stress remained in the friction step for more than six hours. No P&L was accepted. Static audit found repeated full-file Parquet scans and unbounded setup-cache growth. The runtime-fix branch **`phase-30.2-falcon-runtime-fix-v1`** preserves the frozen 270-cell strategy grid and changes only execution architecture. New authoritative run **36216668042** is executing the fixed engine with serialized Base/Stress jobs.



## 2026-09-26 — Phase 30.2 Falcon final closure

The corrected Falcon experiment is closed after authoritative run **36220915944**. Base and Stress each produced **468 setups / 4,212 trades**; **0/270 variants** passed the preregistered ₹5,000/week promotion gate. Base leading mean weekly net: **₹1,432.03**; Stress: **₹733.84**. No WFA/OOS or result-driven retuning is authorized.

[Final Falcon audited report](https://github.com/vishnuvcr/Daily-Options/blob/phase-30.2-falcon-closure-v1/reports/phase30_2_falcon_final_result.md) · [Phase 30.2 plan](https://github.com/vishnuvcr/Daily-Options/blob/phase-30.2-falcon-closure-v1/docs/phase30_2_falcon_weekly_plan.md) · [Next: Bear Put source resolution](https://github.com/vishnuvcr/Daily-Options/tree/phase-30.3-equity-income-bear-put-source-resolution-v1)


## 2026-09-26 — Phase 30.7 Bear Put interpretation grid

After source reconstruction and spot-only feasibility, the Bear Put candidate has **45/54** eligible resistance/trigger definitions with at least 20 signal weeks (33–53 weeks). No option P&L was used in this filter.

Phase 30.7 freezes **6,480** explicit interpretation cells covering expiry, strike construction, gap-up adjustment threshold/wait, risk/exit convention and time exit. This is a preregistered interpretation experiment, not a claim about the video's unstated rules. [Phase 30.7 plan](https://github.com/vishnuvcr/Daily-Options/blob/phase-30.7-bear-put-contract-interpretation-grid-v1/docs/phase30_7_bear_put_contract_interpretation_grid_plan.md) · [Grid manifest](https://github.com/vishnuvcr/Daily-Options/blob/phase-30.7-bear-put-contract-interpretation-grid-v1/reports/phase30_7_bear_put_interpretation_grid_manifest.json)

**P&L remains blocked until implementation/contract audit passes.**


## 2026-09-26 — Live research frontier synchronization

The stale Phase 30.7 screenshot checkpoint is superseded by authoritative repository state. Phase 30.7 Bear Put completed all **18/18 shards** and the aggregate audited **6,480/6,480 cells** with 0 duplicate cells. Base and Stress both had **0 passing cells** for the frozen ₹5,000/week gate, so Bear Put is retired with no WFA/OOS retuning.

The active frontier is now **Phase 30.8 source resolution** for **OvaJumYancs — “No More Straddles. This Strategy Is Smarter.”** The deterministic Python evidence workflow completed successfully (run **36234096126**): tests passed, the source-resolution report was generated, and the artifact was uploaded. The candidate remains **BLOCKED_FOR_PNL** because exact payoff structure, entry/expiry timing, strike construction, adjustment mechanics, stop, target, exit and capital convention are unresolved in the pinned primary evidence.

[Phase 30.7 final result](https://github.com/vishnuvcr/Daily-Options/blob/phase-30.7-bear-put-contract-interpretation-grid-v1/reports/phase30_7_bear_put_final_result.md) · [Phase 30.8 plan](https://github.com/vishnuvcr/Daily-Options/blob/phase-30.8-equity-income-no-more-straddles-source-resolution-v1/docs/phase30_8_plan.md) · [Phase 30.8 source report](https://github.com/vishnuvcr/Daily-Options/blob/phase-30.8-equity-income-no-more-straddles-source-resolution-v1/reports/phase30_8_no_more_straddles_source_resolution.json) · [Phase 30.8 workflow](https://github.com/vishnuvcr/Daily-Options/blob/phase-30.8-equity-income-no-more-straddles-source-resolution-v1/.github/workflows/phase-30.8-equity-income-no-more-straddles-source-resolution-v1.yml)

A separate main-branch launcher is queued to keep Phase 30.8 source-resolution reporting reproducible without depending on hidden/private transcript material.

## 2026-09-26 — Phase 30.10 numerical research active

The live frontier has advanced beyond the stale screenshot checkpoint:

- **Phase 30.7 Bear Put:** closed and retired after the full 6,480-cell Base/Stress matrix produced 0 passing cells in both friction regimes.
- **Phase 30.8 No More Straddles:** source-blocked/data-limited; no P&L accepted because the exact payoff and timing mechanics could not be reconstructed from the available primary archive without the private decryption key.
- **Phase 30.9 Air Defense/VIX:** India VIX cache completed with **248 unique trading-day rows from 2025-09-01 through 2026-08-31**. An initial 70-row partial endpoint response was rejected; deterministic coverage checks now prevent silent truncation.
- **Phase 30.10 Air Defense P&L:** active corrected Base/Stress run **36234923838**, frozen **720 cells per regime / 1,440 total**, 12 definition shards × 2 friction regimes. The first matrix run was cancelled after a YAML interpolation defect and the corrected run is now executing.

[Phase 30.10 numerical plan](https://github.com/vishnuvcr/Daily-Options/blob/phase-30.10-strangle-air-defense-pnl-v1/docs/phase30_10_strangle_air_defense_pnl_plan.md) · [Phase 30.9 VIX acquisition plan](https://github.com/vishnuvcr/Daily-Options/blob/phase-30.9-strangle-air-defense-vix-source-resolution-v1/docs/phase30_9_strangle_air_defense_plan.md) · [Phase 30.7 final Bear Put result](https://github.com/vishnuvcr/Daily-Options/blob/phase-30.7-bear-put-contract-interpretation-grid-v1/reports/phase30_7_bear_put_final_result.md)


## 2026-09-26 — Phase 30.11 rolling WFA active

Phase 30.10 Air Defense/VIX numerical evaluation is complete and audited:
- 720 Base cells and 720 Stress cells were aggregated with 0 duplicates.
- **34 Base cells** and **31 Stress cells** passed the frozen weekly gate.
- **31 cells passed in both friction regimes.**
- The full-sample best Base and Stress cells are not being promoted directly; Phase 30.11 treats the full-sample result as discovery evidence and runs preregistered rolling walk-forward validation.

Active branch: `phase-30.11-strangle-air-defense-wfa-v1`.

Corrected WFA run: **36235740035**. It uses three rolling 20-week training / 12-week OOS folds, 720 cells per fold per friction regime, and no new parameter values. WFA results are not yet final.


## 2026-09-26 — Phase 30.11 corrected WFA frontier

Phase 30.10 Air Defense/VIX full-grid validation is complete: **720 Base + 720 Stress cells**, with **31 cells passing both friction regimes**. These are discovery results only.

Phase 30.11 is now validating the frozen grid with rolling training/OOS folds. The WFA pipeline has been corrected before accepting any survivor:
- WFA engine study-window parameterization fixed;
- weekly event accumulation fixed;
- final-holdout date documentation corrected;
- aggregate cardinality corrected to the actual **144 leaderboard/weekly files** generated by 24 shards × 3 folds × 2 stages.

Clean WFA run: **36236079821**. No WFA survivor is accepted yet.

[Phase 30.11 WFA plan](https://github.com/vishnuvcr/Daily-Options/blob/phase-30.11-strangle-air-defense-wfa-v1/docs/phase30_11_wfa_plan.md) · [Phase 30.10 audited aggregate](https://github.com/vishnuvcr/Daily-Options/tree/phase-30.10-strangle-air-defense-pnl-v1/reports/phase30_10_aggregate)

## 2026-09-26 — Phase 30.11 WFA v2 checkpoint

Air Defense/VIX Phase 30.10 produced 31 cells passing both Base and Stress. Phase 30.11 is now validating those frozen definitions through three rolling WFA folds.

The execution topology was hardened to **72 independent fold/shard/regime jobs** with a 144-file aggregate audit. Clean v2 run **36236257189** is queued; no WFA survivor is accepted yet.

[Phase 30.11 WFA plan](https://github.com/vishnuvcr/Daily-Options/blob/phase-30.11-strangle-air-defense-wfa-v1/docs/phase30_11_wfa_plan.md)

## 2026-09-26 — Phase 31.2 forensic audit

The Phase 31.1 fixed NIFTY ratio result is **provisionally quarantined** for forensic reconciliation. E0364 found a provenance mismatch between the checked-in Phase 31.1 simulator and its persisted weekly artifact: the simulator currently references a `costs` aggregation field that it does not create, while the artifact contains that field.

Phase 31.2 freezes the strategy and independently re-reads the pinned raw NIFTY/index-options dataset to reconcile leg prices, strikes, expiry, lot size, raw P&L, execution P&L, costs, weekly aggregation and the empirical 09:30→15:10 loss-region diagnostic. No tuning is allowed.

[Phase 31.2 plan](docs/phase31_2_forensic_audit_plan.md) · [Phase 31.2 workflow](.github/workflows/phase-31-2-phase31-1-forensic-audit.yml) · [Phase 31.2 branch](https://github.com/vishnuvcr/Daily-Options/tree/phase-31.2-phase31-1-forensic-audit-v1)
