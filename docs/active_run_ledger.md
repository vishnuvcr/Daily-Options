# Active Run Ledger — 2026-09-24

## Target
Rs 1,000 net per active lot per trading day, after brokerage, statutory/exchange charges and conservative slippage, with untouched out-of-sample validation.

## Current runs

| Phase | Branch | Run | Status | Accepted P&L? |
|---|---|---:|---|---|
| 8 | phase-8-hybrid-ml-momentum-v2 | 35937700542 | Base numerical stage running | No |
| 9 | phase-9-regime-credit-spread-v1 | 35937112092 attempt 3 | Base numerical stage running | No |
| 10 | phase-10-cross-index-1m-v1 | 35937773719 | Base numerical stage running | No |
| 11 | phase-11-breakout-pullback-oi-v1 | preregistered | Not yet executed | No |

## Evidence rule

A strategy result is not accepted unless:
1. the workflow completes without execution defects;
2. base and stress costs are both computed;
3. the strategy is evaluated by the preregistered walk-forward procedure;
4. at least one untouched test window reaches Rs 1,000/lot/day for promotion;
5. no parameter was selected from test data.

## Frozen negative evidence

The prior Phase 2/3/3F/3G/3H/3I results remain frozen and are not being retuned to fit the new target.


## 2026-09-24 execution refresh

- Phase 8 v2: failure E0067 reproduced from run 35937700542; corrected branch commit 7f1ed0b... was pushed. Fresh CI result not yet exposed through the GitHub connector.
- Phase 9: rerun of the cancelled job 107438515608 created a fresh in-progress job 107543124203; base numerical stage is running.
- Phase 10: failure E0069 reproduced from run 35937773719; corrected branch commit 7558c90... was pushed. Fresh CI result not yet exposed through the GitHub connector.
- Phase 11 remains preregistered and deliberately not launched until the corrected Phase 8-10 runs are inspected, avoiding unnecessary compute and premature family selection.


- Phase 11: implementation commits 2c9e442, 379c853, 8bfcfe9, 2178adc, then side-selection fix 1b6314c. CI is now triggered from the corrected branch; no result is accepted yet.

- Phase 9 attempt 3 job 107543124203 also cancelled by runner shutdown; no P&L accepted. Workflow concurrency was hardened to `cancel-in-progress: false`, and commit 20fa261f starts the next clean branch execution.

## Current PR / branch correction state — 2026-09-24

| Phase | Current branch/PR | Result status |
|---|---|---|
| 8 | phase-8-hybrid-ml-momentum-v2 / PR #9 | Fresh corrected execution pending; no accepted P&L |
| 9 | phase-9-regime-credit-spread-v1 / PR #10 | Runner cancellation reproduced; concurrency hardened; no accepted P&L |
| 10 | phase-10-cross-index-1m-v1 / PR #8 | Additional SQL projection correction at 5adf689; fresh execution pending |
| 11 | phase-11-breakout-pullback-oi-v2 / PR #12 | Corrected nearest-wing execution; fresh execution pending |

Phase 11 original PR #11 is retained as the first implementation audit trail; v2 is the corrected execution branch.

### Exact execution runs — 2026-09-24 08:02 UTC
| Phase | Execution branch | Commit | Workflow run | Job | Status |
|---|---|---|---:|---:|---|
| 8 v3 | phase-8-hybrid-ml-momentum-v3-exec | 4c660571 | 35972809477 | 107546216455 | base friction running |
| 9 v2 | phase-9-regime-credit-spread-v2-exec | 7068c2c0 | 35972822793 | 107546261010 | base friction running |
| 10 v2 | phase-10-cross-index-1m-v2-exec | 40436f5e | 35972869077 | 107546412046 | base friction running |
| 11 v3 | phase-11-breakout-pullback-oi-v3-exec | e5f495c1 | 35972926200 | — | queued |

These are the first runs using exact branch-parent construction after E0078. No numerical result is accepted until base, stress, and untouched WFA gates are complete.

### Additional execution fixes — 2026-09-24
- Phase 10 v3 execution branch phase-10-cross-index-1m-v3-exec, commit 2a2619d8, run 35973399377: tests passed; data acquisition in progress at last check.
- Phase 9 v4 memory-safe/retry branch phase-9-regime-credit-spread-v4-retry, commit bb74dffe, run 35973446515: dependency installation/data acquisition in progress at last check.
- Phase 11 v3 run 35972926200 remains queued.

### Phase 8 formal-gate correction — 2026-09-24
- Phase 8 v4 branch corrected in-place to exact-parent commit `ccfa4605d8dc3702bdab0a4f1091c0e78857a2be`, parent `96947e1`.
- The prior contaminated test commit `5792cb6` is retained only as an audit artifact; it is not the execution ref.
- The corrected v4 ref should now trigger the formal-gate workflow from the repository's push/PR workflow.

### Phase 8 closure
- Run 35972809477 / commit 4c660571 completed successfully.
- Base and doubled-slippage stress both failed the preliminary target gate.
- Phase 8 is frozen negative and retired. No further tuning from this family is permitted.
### Phase 10 closure
- Run 35973884459 / commit 89df76fd completed base, stress and WFA.
- Best base mean all-day net -₹113.62/lot/day; stress -₹136.48; WFA mean test-window net -₹122.39.
- Phase 10 is frozen negative and retired.
### Current frontier refresh
- Phase 8: retired negative after run 35972809477; no further compute.
- Phase 10: retired negative after run 35973884459; no further compute.
- Phase 9 v5 sharded run 35974727222: four shards active in base computation.
- Phase 11 v4 exact-parent commit fd3625b: run 35975025996 queued under isolated concurrency group; no result yet.

### Phase 10 completion — 2026-09-24
- Run `35973884459` completed successfully from commit `89df76f`.
- Numerical gate: FAIL. Family retired.
- Archive commit: `ddda47a627f49660ce5b8c98551ecd7c84d1f7f0`.
- No future tuning of Phase 10 is authorized; any further work must be a scientifically distinct phase.

### Phase 9 v5/v6 correction — 2026-09-24
- v5 run 35974727222 completed all four shards but produced 0 trades; shard logs showed 26,544 signals and 26,538 entries per shard. Investigation found the short and long legs were selected by expiry type rather than the same actual expiry date. v5 is NON-EVIDENTIARY and is not a strategy result.
- v6 exact-parent commit 1694d95b2778aedb18581724317c71e91be44740 locks both legs to the next actual WEEK/MONTH expiry and carries that expiry into simulation. Run 35975773169 is queued.

### Phase 12 parked research branch
- Branch: phase-12-derivative-lead-options-v1
- PR: #20
- Commit currently holds a manual data-gate workflow only.
- It is not being executed while Phases 9 and 11 are active.

### Phase 9 closure
- Corrected computation run: 35975698105.
- All four shards completed base and stress; global trade files were independently aggregated after reducer packaging defects.
- Final: best base -₹168.79/lot/day; stress -₹228.79; 0/16 positive WFA windows.
- Phase 9 is frozen negative and retired.

## 2026-09-24 — authoritative Phase 11 v5e checkpoint

| Phase | Execution branch | Workflow run | Job | Status | Accepted P&L |
|---|---|---:|---:|---|---|
| 11 v5e | phase-11-breakout-pullback-oi-v5e-authoritative | 35978104824 | 107563265459 | Tests/data passed; Base friction in progress | No |

This is the sole authoritative Phase 11 execution at this checkpoint. No competing Phase 11 run should be started unless this run fails for infrastructure or engineering reasons.


## Phase 16 v2 authoritative execution setup — 2026-09-24

| Phase | Execution branch | Workflow | Ref | Status | Accepted P&L |
|---|---|---|---|---|---|
| 16 v2 | phase-16-iv-skew-tail-credit-v2-exec | Phase 16 - Execution Bridge / v2 | `9608dcf41ca06354f846347c614a6f08dd794a65` | READY FOR CI | No |

The v2 run uses pinned Artist23 revision `45e0a04`, base/stress slippage ₹0.20/₹0.40 per leg, exact expiry propagation, exact 30/60-minute holds, outcome caching and the ₹1,000 active-day target gate. v1 P&L remains non-evidentiary.

## Phase 16 v2 — schema-correct execution ref

Superseded Base run `36030857048` failed in both shards at the feature SQL because Artist23 has no `expiry` column (E0165). The corrected authoritative preliminary ref is `65528f8e6012f1a9dfed15150d5ee1a3e557c6d7`. No P&L from the failed run is accepted.
