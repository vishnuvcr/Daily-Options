# Phase 30.10 — Air Defense / India-VIX full-grid result

## Status

**COMPLETE — discovery phase passed to preregistered WFA validation.**

Authoritative workflow run: **36235165086**.

The frozen numerical experiment completed:
- 720 Base cells;
- 720 Stress cells;
- 0 duplicate cells;
- 34 Base cells passed the weekly promotion gate;
- 31 Stress cells passed;
- **31 cells passed in both Base and Stress**.

The result is treated as **in-sample discovery evidence only**. No cell is being promoted directly to a trading strategy.

## Study window and friction

Study window: **2025-09-01 through 2026-08-31**.

India VIX coverage: **248 unique trading-day observations**.

Base slippage: **₹0.20 per order**.  
Stress slippage: **₹0.40 per order**.

The engine retained date-aware brokerage/statutory-cost handling and reported execution coverage, capital proxy, drawdown and tail statistics.

## Common Base + Stress gate survivors

There are **31 frozen cells** that pass the gate in both regimes.

The strongest full-sample cell by mean weekly net in both regimes uses:
- Friday;
- 10:00 entry;
- second-nearest future weekly expiry;
- 0.20-delta strike construction;
- 90% of entry-to-threatened-strike distance trigger;
- add-short adjustment;
- no separate stop.

Its full-sample metrics are:

| Metric | Base | Stress |
|---|---:|---:|
| Completed weeks | 41 | 41 |
| Mean weekly net | ₹8,601.43 | ₹8,525.81 |
| Median weekly net | ₹11,943.56 | ₹11,853.60 |
| Profitable-week rate | 82.93% | 82.93% |
| Profit factor | 2.98 | 2.95 |
| Max drawdown | -₹124,004 | -₹124,238 |
| Weekly 5% quantile | -₹22,434 | -₹22,512 |
| Weekly 5% expected shortfall | -₹45,100 | -₹45,178 |
| Execution coverage | 100% | 100% |
| Average capital proxy | ₹20,687 | ₹20,687 |
| Peak capital proxy | ₹44,852 | ₹44,852 |
| Net P&L | ₹352,658.59 | ₹349,558.28 |

These values are not an estimate of future profitability. They describe the frozen historical simulation only.

## Interpretation

The important result is not the apparent full-sample return. The important result is that a materially sized region of the preregistered interpretation space survives both Base and Stress friction assumptions.

At the same time, the full sample was used to discover which frozen definitions may have signal value. Selecting the best full-sample cell and stopping would introduce in-sample selection bias.

Therefore:
- Phase 30.10 is **not** the final strategy conclusion.
- No live-trading recommendation is made from these results.
- Phase 30.11 rolling WFA is mandatory.
- Only cells surviving the preregistered WFA rule can advance to the reserved final holdout.

## Known limitations carried forward

The Air Defense source contains some inferred mechanics. The 720-cell grid deliberately bounded those uncertainties rather than pretending they were source-explicit.

The capital figure is a **research capital proxy**, not a broker margin quote.

The numerical engine's successful aggregate does not independently establish execution quality under actual live market microstructure.

## Next phase

**Phase 30.11 — rolling walk-forward validation.**

The full 720-cell grid is being evaluated on three rolling training/OOS folds, with Base and Stress treated independently and no post-result parameter expansion.

See:
- `docs/phase30_11_wfa_plan.md`
- `research/phase30_11_wfa.py`
- `research/phase30_11_wfa_aggregate.py`
