# Phase 28 — Deduplication and family clustering

## Objective
Map videos to canonical payoff families and remove duplicate experiments.

## Inputs
Phase 27 rule sheets

## Outputs
docs/equity_income_strategy_families.csv

## Weekly research gate
The program target is **₹5,000 net per traded week** at a fixed declared reference position size. Position size may not be increased solely to satisfy the target.

## Completion gate
Every tested strategy has a unique canonical family ID.

## Mandatory controls
- Keep strategy rules frozen once the phase's test definition is registered.
- Account for Paytm Money brokerage, NSE exchange charges, STT, SEBI fee, stamp duty, GST and explicit Base/Stress slippage.
- Preserve information barriers and historical lot sizes.
- Log every implementation/data error in `docs/error_log.md`.
- Update `docs/research_status.md` after each execution.
