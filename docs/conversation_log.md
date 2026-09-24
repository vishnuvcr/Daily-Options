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
