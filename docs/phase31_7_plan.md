# Phase 31.7 — OI/Volume Microstructure Discovery

## Status
CLOSED — negative discovery; no promotion.

## Research question
Can lagged NIFTY option volume and open-interest microstructure at the 09:30 IST decision point identify same-day defined-risk directional option spreads whose net weekly P&L survives realistic transaction costs and Base/Stress slippage?

## Hypothesis
Three deterministic, bounded features are tested:
1. **Volume imbalance**: (ATM CE volume − ATM PE volume) / (ATM CE volume + ATM PE volume).
2. **OI-change imbalance**: [(CE OI change) − (PE OI change)] / [|CE OI change| + |PE OI change|], where OI change is 09:30 OI minus 09:25 OI.
3. **Joint pressure**: 50% volume imbalance + 50% OI-change imbalance.

Positive values map to a long ATM call debit spread; negative values map to a long ATM put debit spread. The wing is fixed at 200 NIFTY points.

## Frozen signal and execution
- Study window: 2021-07-01 through 2026-08-31, subject to exact data coverage.
- Signal timestamp: completed 09:30 IST bar.
- Feature inputs are restricted to 09:25 and 09:30 option observations.
- Entry: 09:31 option open.
- Exit: 15:10 same day.
- One trade/day per cell.
- ATM strike: nearest ₹50.
- Expiry buckets: nearest and next available NIFTY expiry on/after trade date.
- Structure: 1-lot 200-point debit spread; no stop, target, adjustment, leverage or discretion.
- Historical lot sizes and the frozen Phase 31.3 transaction/statutory charge model are mandatory.
- Base slippage: ₹0.20/order.
- Stress slippage: ₹0.40/order.

## Frozen 12-cell grid
3 features × 2 absolute-pressure thresholds × 2 expiry buckets:
- thresholds: 0.20 and 0.40;
- features: volume imbalance, OI-change imbalance, joint pressure;
- expiry: nearest, next.

No additional threshold, lookback, wing, entry time, exit time or structure dimensions may be introduced after observing results.

## Null controls
For each true signal cell, run five deterministic placebo controls using fixed seeds 101, 202, 303, 404 and 505. Within each expiry bucket, the feature values are permuted across trading days before applying the same signal threshold and execution rule. The shuffle destroys date-level association while preserving the empirical feature distribution.

Null controls are diagnostic only and cannot be promoted.

## Data gate
Before P&L:
- Exact-expiry NIFTY option files must exist.
- Volume and open-interest fields must be present and non-null at required timestamps.
- Nearest-expiry 09:25/09:30 feature coverage must be at least 70% of eligible study sessions.
- Next-expiry feature coverage must be at least 50% of eligible study sessions.
- Entry/exit option-leg coverage must be measured, not silently substituted.
- All feature timestamps must be no later than 09:30; entry is strictly 09:31.
- If the gate fails, the phase closes as DATA-LIMITED without inventing substitutes.

## Required outputs
- data_gate.json;
- daily feature ledger;
- true and null daily trade ledgers;
- weekly ledgers;
- true-cell Base/Stress summaries;
- null-control distributions;
- missing-data diagnostics;
- accounting reconciliation;
- drawdown, worst-week, tail-loss and positive-week statistics.

## Promotion
Discovery does not promote a strategy. A true cell can only advance to the existing WFA and independent later-period OOS process if it first clears the project gate in both Base and Stress. Null controls are retained as a robustness diagnostic.

## Stop rule
Close after the frozen 12 true cells plus five null controls per cell. Do not expand the grid because of observed results.

## External evidence note
The Phase 31.4 evidence matrix classifies OI/volume microstructure as testable-with-nulls because Indian literature reports information in OI/volume while recent work cautions that held-out predictive performance can disappear. The present phase therefore treats the microstructure signal as a hypothesis requiring out-of-sample confirmation rather than an established edge.

NSE's current NIFTY specification lists weekly expiries on Tuesday, with the prior trading day used when Tuesday is a holiday; the implementation uses actual expiry files in the pinned dataset.


## Phase closure — 2026-09-26

Authoritative workflow: **36251189770**. Artifact: **10909111158**.

The data gate passed with 1,228 eligible sessions, nearest-expiry feature coverage 98.13%, and next-expiry coverage 72.39%. The validated numerical run produced 4,060 true trade records per friction across the 12 declared cells. All 12 Base cells and all 12 Stress cells had negative total net P&L; **0/12** cleared the promotion gate.

The highest mean-weekly cell was VOL_IMB at threshold 0.40, nearest expiry:
- Base: -₹18,566.48 total, -₹191.41 mean weekly, -₹942.75 median weekly, 42.27% positive weeks.
- Stress: -₹23,821.47 total, -₹245.58 mean weekly, -₹974.92 median weekly, 42.27% positive weeks.

Five deterministic null seeds were executed for every true cell from the complete feature panel before thresholding. No true cell exceeded all five nulls on mean weekly P&L.

The correct accounting identity is raw gross minus slippage minus transaction/statutory costs equals net P&L; the run reconciled to below 2e-12 absolute row-level residual.

No WFA/OOS promotion is authorized. Phase 31.7 is closed as negative evidence.
