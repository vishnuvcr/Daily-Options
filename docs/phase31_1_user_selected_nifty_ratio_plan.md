# Phase 31.1 — User-selected NIFTY 09:30 ratio strategy

## Status
PREREGISTERED — numerical testing pending.

## User-selected fixed rule
Underlying: NIFTY index options.

Entry: 09:30 IST on each eligible trading day.

Exit: 15:10 IST on the same trading day.

At entry, define ATM as the nearest valid listed NIFTY strike to the NIFTY spot/index reference available at 09:30.

Execute exactly:
1. Buy 2 lots NIFTY ATM + 200 Call.
2. Buy 2 lots NIFTY ATM - 200 Put.
3. Sell 1 lot NIFTY ATM - 400 Put.

Example:
- NIFTY = 23,200
- Buy 2 x 23,400 CE
- Buy 2 x 23,000 PE
- Sell 1 x 22,800 PE

The user's example contained "28,800 PE"; this is normalized to 22,800 PE because the declared rule is ATM - 400.

No discretionary adjustment, stop, target, re-entry, averaging or parameter optimization is part of this phase.

## Position sizing
The reference strategy size is 2:2:1 lots.
Historical NIFTY lot size is date-aware from exchange contract metadata; the current screenshot's 65-unit lot therefore corresponds to 130 / 130 / 65 units.

## Execution specification
- Signal/reference timestamp: 09:30:00 IST.
- Entry fill: first valid executable quote/bar at or immediately after 09:30, subject to the repository's established information-barrier and fill rules.
- Exit fill: first valid executable quote/bar at or immediately after 15:10, using the same deterministic execution convention.
- If a required leg lacks valid executable data within the permitted execution window, the trade is recorded as not executable rather than silently substituted.
- No look-ahead.
- No parameter selection from test results.

## Cost and friction
Apply the repository's current date-aware Paytm Money/NSE/statutory cost model, including:
- brokerage;
- exchange transaction charges;
- SEBI/statutory charges;
- STT;
- stamp duty where applicable;
- GST where applicable;
- Base slippage;
- doubled-slippage Stress.

The final report must separately show gross P&L, each cost component, total costs and net P&L.

## Research question
Does this exact user-selected 09:30 NIFTY 2-2-1 option structure produce a reproducible and sufficiently consistent net return, after realistic costs, to meet the active Equity Income target of >= Rs 5,000 net per completed trading week when evaluated on the predefined weekly aggregation and untouched OOS/WFA framework?

## Primary outputs
- Every executable trade chronologically.
- Entry/exit timestamp for every leg.
- Spot/reference price.
- ATM and all selected strikes.
- Quantities/lots.
- Entry and exit prices.
- Gross leg P&L and total gross P&L.
- Brokerage, exchange/statutory charges, STT, GST/stamp duty as applicable.
- Slippage under Base and Stress.
- Final net P&L.
- Capital/margin proxy.
- Daily and weekly aggregation.
- Win rate, payoff, expectancy, profit factor, drawdown, worst day/week, 5% tail and expected shortfall.
- Execution coverage and missing-data diagnostics.
- Walk-forward/OOS results without test-period tuning.

## Promotion gate
The active Equity Income gate remains:
- mean weekly net >= Rs 5,000 on untouched OOS weeks;
- median weekly net >= Rs 5,000;
- >=70% eligible OOS weeks net-positive;
- >=80% eligible OOS weeks executed unless a source-frozen no-trade rule applies;
- Base and doubled-slippage Stress both reported;
- robustness and drawdown diagnostics disclosed.

This phase is a fixed-rule test, not an optimization tournament. A negative result will not be tuned into a positive result.

## Required data integrity
Before accepting P&L:
- exact NIFTY option contract identity;
- date-aware expiry and lot size;
- timestamp/timezone validation;
- strike availability validation;
- leg-level quote/bar coverage;
- no duplicated execution rows;
- no future information;
- deterministic ATM selection;
- deterministic entry/exit fill logic.

## Deliverables
1. Preregistered implementation and tests.
2. Cached input-data manifest.
3. Trade-level ledger.
4. Base and Stress results.
5. Weekly aggregation.
6. Statistical/robustness report.
7. Error log updates for every implementation defect.
8. Research-status update after each execution step.
9. Final phase decision: PASS / FAIL / DATA-BLOCKED.
