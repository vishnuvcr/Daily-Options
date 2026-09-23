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
