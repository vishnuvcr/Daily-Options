# Phase 10 — Cross-Index Relative-Strength Option Strategy

## Why this phase is different

Previous failed families mostly conditioned one underlying and then selected option parameters around that same price series. Phase 10 changes the information source: the strategy first identifies whether NIFTY or BANKNIFTY is displaying a short-horizon relative-strength shock, then expresses that signal through the leader's option market.

## Data

The primary research dataset is `thetrademarkk/india-index-options-1m`, which documents 1-minute NIFTY/BANKNIFTY/SENSEX spot and option bars with strike, option type, expiry and OI fields. It is approximately 377M rows / 4GB and is CC-BY-NC-4.0. The data are research-only; licensed/executable validation remains mandatory before deployment.

## Pre-registration

128 variants:
- standardized leader-strength gap: 0.75 / 1.25;
- entry: 09:45 / 10:00;
- expiry: next WEEK / next MONTH;
- spread width: 1 / 2 available strike steps;
- hold: 15 / 30 / 45 / 60 minutes;
- exit profile: stop 30% or 50% of debit; target 60% or 100%.

The chosen leader is determined solely by NIFTY vs BANKNIFTY relative strength at the signal time. No result-based selection of the underlying is permitted.

## Execution and costs

- Signal uses completed 1-minute spot bars.
- Option confirmation is an ATM premium increase over the prior 3 minutes in the same direction as the index signal.
- Entry occurs at the next executable minute.
- Strike and expiry are frozen at entry.
- Debit spread risk is bounded.
- Base slippage 0.20 points/leg; stress 0.40.
- Brokerage, statutory costs, exchange charges and date/contract-aware lots are included.

## Promotion

Preliminary: mean active-day net >= Rs 1,000/lot.
Formal: positive untouched-test expectancy, at least one untouched test window >= Rs 1,000/lot/day, and no material stress failure.

A failure of this family terminates only the family; the overall Rs 1,000 target remains active.
