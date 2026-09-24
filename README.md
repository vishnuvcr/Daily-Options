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


## Phase 16 integrity correction — 2026-09-24

The active Phase 16 IV-skew tail-credit family remains **pre-result**. Run 36021088602 failed during unit-test collection, so it generated no numerical evidence. Before the next run, an implementation audit identified and corrected hold-window enforcement, deterministic nearest-future-expiry selection, and CI cancellation behavior. The 288-cell preregistered grid and cost/slippage assumptions are unchanged. No Phase 16 P&L is accepted until the corrected branch passes tests and completes both base and stress runs.
