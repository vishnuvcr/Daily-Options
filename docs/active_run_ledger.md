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
