# Conversation and Decision Log

## 2026-09-23

### User requirement
The user requested a daily, intraday Indian options strategy, with a target of at least Rs 1,000 profit per lot per day, and asked for extensive research to find, create and validate such a strategy.

### Research decision
Treat Rs 1,000 net profit per active lot per trading day as the primary quantitative target. Search broadly across strategy families and regimes. Never use gross P&L as the promotion criterion.

### Engineering decision
The repository was empty, so bootstrap it with a research charter, phase plan, status log, error log and reproducibility scaffolding.

### Communication decision
This log records requirements, research decisions, evidence and outcomes. It intentionally does not record private hidden chain-of-thought.

## 2026-09-24 — User: "Ok proceed"

### Continuation decision
Continue the bounded search under the revised stopping criterion: do not end the research until a reproducible intraday candidate clears Rs 1,000 net per active lot per trading day after realistic costs/slippage and untouched out-of-sample validation.

### Execution findings
- Phase 8 v2 run 35937700542 failed on executable-entry `open` schema handling; no P&L accepted. Branch guard added.
- Phase 9 attempts were cancelled by runner shutdown twice with no Python exception; no P&L accepted. Workflow concurrency changed to `cancel-in-progress: false`.
- Phase 10 run 35937773719 failed on pandas Series attribute access. A follow-up review found the candidate SQL also omitted `leader`; corrected in commit 5adf689.
- Phase 11 was implemented as the preregistered 64-variant breakout/pullback/OI-confirmation family. Pre-run option-side selection was corrected. A further review found the PUT wing selector used the farthest lower strike; Phase 11 v2 corrects this and adds a regression test.

### Research integrity decision
No P&L result from a failed or incomplete run is accepted. No parameter has been selected from a test period. Engineering corrections are applied before interpreting results, without changing the preregistered hypothesis families or numerical parameter grids.

### 2026-09-24 — Fresh corrected executions

The first fresh reruns still executed stale branch refs, exposing:
- Phase 8 missing `r.open` in the ranked SQL projection.
- Phase 10 missing `c.leader` in the candidate projection.

A branch-provenance issue in the GitHub file-update path was also identified: some commits were not advancing the intended branch ref. This was closed by constructing exact-parent blob/tree/commit objects and creating immutable execution branches.

Current runs:
- Phase 8: 35972809477, base running.
- Phase 9: 35972822793, base running.
- Phase 10: 35972869077, base running.
- Phase 11: 35972926200, queued.

No strategy result is accepted yet.

### 2026-09-24 — Latest execution frontier

Phase 8 completed the base friction calculation successfully; its doubled-slippage stress calculation is still executing. Phase 9’s retry successfully resolved the Hugging Face transport error but was again terminated by a GitHub runner shutdown during base computation. Phase 10 then failed on one final schema omission (premium_ret3); v4 corrects it. Phase 11 remains queued.

No strategy result is promoted or described as successful.

### Phase 8 closure — 2026-09-24

The first clean exact-ref Phase 8 run completed base and stress. Across all 96 preregistered variants, none reached ₹1,000 net/active lot/day. The best base mean all-day net was -₹6.13 and stress was -₹36.13. The family is retired without WFA promotion or test-period retuning.
### Phase 10 closure — 2026-09-24

The exact-ref Phase 10 v4 workflow completed. Across 128 variants, best base mean all-day net was -₹113.62/lot/day, stress -₹136.48, and all 3 walk-forward test windows were negative. The family is retired without retuning.

### 2026-09-24 — Phase 10 completed and retired

Phase 10 completed base and doubled-slippage stress execution. The best base result was ₹-113.62/lot/day and the best stress result ₹-136.48/lot/day. All three untouched WFA windows were negative in both friction settings. The family was retired with no post-result retuning.

### 2026-09-24 — Phase 12 preregistration

After reviewing current/historical lead-lag evidence, a futures/derivative-versus-spot price-discovery family was preregistered as the next distinct mechanism. It is data-gated and does not assume futures permanently lead spot. No strategy result has been produced from Phase 12.

### Phase 9 closure — 2026-09-24

The corrected Phase 9 engine produced real trades after the earlier path-join defect was fixed. All 96 variants and 106,152 trades were independently aggregated from the four shard artifacts. Best base mean active-day net was -₹168.79/lot/day; stress -₹228.79; all 16 WFA windows were negative. The family is retired without retuning.


## 2026-09-25 — Resume in new chat / Phase 19 monitoring

The research was resumed from the Phase 18 retirement and corrected Phase 19 execution checkpoint. Authoritative run `36042015205` is on `phase-19-nifty-short-strangle-regime-v1`, head `2ed269eb2bc875671c818f5cde2707e0a97e4499`. Both Base and Stress passed tests and data acquisition and are executing the unchanged frozen short-strangle grid. No P&L has been interpreted or promoted.

A live-log read returned a GitHub `BlobNotFound` response while the jobs remained in progress; workflow job-step state is used as the authoritative runtime monitor.

## 2026-09-25 — Phase 19 v2 runtime correction

The stalled Phase 19 execution was not treated as strategy evidence. E0197 was found during a static audit: execution simulation still keyed rows on the dataset `trading_day` instead of the corrected UTC→IST timestamp-derived trade date. A v2 branch was created with unchanged strategy parameters, timestamp-safe execution joins, vectorized exit selection, exact cost-model equivalence tests, and the same Base/Stress friction settings. Latest run `36043078139` has passed v2 unit tests; Stress is acquiring/reusing data and Base is queued.


## 2026-09-25 — Phase 19 v3 authoritative execution

After the v1 friction stall and v2 runner contention, an isolated Phase 19 v3 branch was created. It retains the frozen short-strangle parameters and corrected timestamp-derived option trade-date logic, uses clean output directories, and runs Base then Stress in one authoritative job. Latest run `36043694480`: tests/data acquisition passed; Base friction is executing. No numerical result is yet accepted.


## 2026-09-25 — Phase 13 integrity correction

The prior Phase 13 result was revisited during candidate-audit work. Every trade row in the authoritative Base/Stress artifact was an exact duplicate, caused by risk-profile expansion before merging on the already-keyed `risk_id`. The corrected result is about half the published net: ₹142.72 base / ₹112.72 stress best-cell mean active-day net, with no target-qualified cell and corrected WFA mean ₹121.82 / ₹91.82. This is an audit correction, not a new strategy search or parameter tuning.


## 2026-09-25 — Phase 20 final result / Phase 21 launch

Authoritative Phase 20 run 36045068043 completed Base and Stress cleanly. The frozen 384-cell global-gated late-day volatility-acceleration family produced 3,872 trades; best mean active-day net was Rs 481.73 base and Rs 451.73 stress, with 0 target-qualified cells and 0 nested-WFA windows. Phase 20 is retired without retuning. Phase 21 is the active frontier: a preregistered regime switch between long ATM straddles on fixed expansion regimes and short OTM strangles on fixed calm regimes.

## 2026-09-25 — Phase 29.1 readiness execution and correction

Phase 29.1 source-readiness audit was implemented with pinned TradeMarkk 51ca58c and Rissin 78b1c5468255d18cf492984bfe6fe4e3ac874d7c revisions, candidate-level readiness mapping, regression tests, and an Actions workflow with manual dispatch and push/pull-request execution. Run 36132533217 passed unit tests and the workflow gate, but its first source inventory exposed E0252: the Hugging Face repository ID was URL-encoded incorrectly, so every source-tree request returned HTTP 400. That artifact is rejected. The code is now corrected to preserve the repository slash, and source API failures are fatal rather than being allowed to silently change the feasibility counts. The rerun will be accepted only if the pinned NIFTY partitions are actually inventoried and the 51/16/4 regression distribution is reproduced. No P&L is involved.

## 2026-09-25 — Phase 29.1 recursive parquet validation

The first corrected source-tree run fixed the repository-slash encoding defect (E0252) and reproduced the 51/16/4 candidate classification, but the inventory still used a non-recursive HF tree listing. That returned only directory metadata files, so file_count>0 was not evidence of actual parquet availability. E0253 was logged and the code was corrected to recurse and count real .parquet files; the workflow now asserts parquet_file_count>0 for the pinned NIFTY partitions. A fresh Phase 29.1 run was triggered. No P&L is accepted from either preliminary artifact.
