# Phase 28 — Deduplication and family clustering

## Objective

Reduce the 71 Phase 26 strategy-candidate videos into conservative canonical research families without promoting unresolved rules into backtests.

## Inputs

- Phase 26 video inventory
- Phase 27 timestamped rule-evidence metadata

## Method

1. Use structural payoff-family hints from titles and Phase 27 metadata.
2. Compare normalized titles and structural-family overlap.
3. Merge only strong candidates above a preregistered similarity threshold.
4. Mark each cluster HIGH or REVIEW_REQUIRED.
5. Preserve unresolved source fidelity and prohibit backtesting.

## Outputs

- data/equity_income/strategy_families.csv
- data/equity_income/phase28_summary.json

## Completion gate

Every candidate has one family ID, every family has a review status, and zero rows are backtest-eligible.
