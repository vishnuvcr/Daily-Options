# Phase 30.10 — STRANGLE AIR DEFENSE SYSTEM numerical evaluation

## Status
**OPEN — bounded Base/Stress numerical matrix.**

Phase 30.9 established complete India VIX study-window coverage (248 trading days, 2025-09-01 through 2026-08-31) using the NSE historical VIX endpoint. The earlier 70-row partial result was rejected. No P&L was computed from the incomplete file.

## Frozen matrix

To avoid silently choosing unresolved source mechanics, the numerical matrix preregisters:

- Entry day: Monday, Tuesday, Wednesday, Thursday, Friday (5)
- Entry time: 09:20, 10:00, 11:00 IST (3)
- Expiry: nearest future listed weekly expiry, second-nearest future listed weekly expiry (2)
- Strike construction:
  1. source-explicit 0.20-delta approximation using Black–Scholes with prior-trading-day India VIX close and zero risk-free rate;
  2. 1-sigma India VIX expected range;
  3. 2-sigma India VIX expected range (3)
- Adjustment trigger:
  1. first touch of the threatened short strike;
  2. first touch of 90% of the entry-to-threatened-strike distance (2)
- Adjustment action:
  1. add one additional short at the threatened short strike;
  2. buy one protective option at the next listed strike beyond the threatened short strike (2)
- Risk exit:
  1. no separate stop;
  2. close the complete open position when mark-to-market loss reaches 2x initial credit (2)

Registered cells: 5 x 3 x 2 x 3 x 2 x 2 x 2 = 720 per friction regime.

No cell is selected from results. The 720-cell grid is the full preregistered interpretation space for this numerical phase.

## Fixed mechanics

- Underlying: NIFTY.
- One lot per short/long leg using the date-aware NIFTY historical lot-size schedule already used by the project (75 through 2025-12-30; 65 thereafter).
- Weekly expiry selection is strictly future to the entry date; no same-day expiry entry is used.
- VIX input is the prior trading day's close. This is a no-lookahead convention because the repository contains daily VIX EOD values, not intraday VIX.
- Expected 1-sigma move: S x (India VIX / 100) x sqrt(T/365).
- 2-sigma move is twice the 1-sigma move.
- Listed strikes are selected from the cached option chain for the chosen expiry.
- 0.20-delta approximation uses Black–Scholes with sigma = prior-day India VIX / 100 and r = 0; call and put strikes are the listed strikes nearest the target absolute delta 0.20.
- Entry fills occur at the first available one-minute option quote at/after the entry decision minute.
- Adjustment fills occur at the first available one-minute quote one minute after the trigger.
- Hard exit is 15:25 IST on the actual listed expiry date.
- Base slippage = ₹0.20/order.
- Stress slippage = ₹0.40/order.
- Brokerage/fees/statutory charges use the project's date-aware Paytm Money/NSE cost model.
- Missing required quotes are counted as execution misses; no silent substitution.

## Capital reporting

The engine will report a capital proxy, not an asserted broker margin requirement. It is based on initial premium plus a defined worst-leg distance proxy for the open short position, with adjustment legs included. Exact Paytm Money margin should be separately verified before live use.

## Weekly statistics

Use completed trading weeks only:
- mean weekly net P&L;
- median weekly net P&L;
- profitable-week rate;
- profit factor;
- max drawdown;
- weekly 5% quantile;
- expected shortfall;
- execution coverage;
- average and peak capital proxy;
- gross P&L, costs and net P&L;
- cost share.

## Promotion gate

A cell passes only when:
- mean weekly net >= ₹5,000;
- median weekly net >= ₹5,000;
- profitable-week rate >=70%;
- >=20 completed weeks;
- execution coverage >=80%.

Both Base and Stress results must be reported. Stress failure prevents promotion to WFA/OOS.

## Numerical workflow

- 12 definition shards × 2 friction regimes.
- Every shard runs the same frozen code with only the registered definition slice and slippage changed.
- Aggregate audit requires exactly 720 cells per friction regime and zero duplicates.
- Any shard/artifact/runtime failure invalidates the affected regime until rerun.
- Results are committed only after aggregate audit.

## Research questions

1. Can the Air Defense interpretation space clear the fixed ₹5,000/week consistency gate after friction?
2. How sensitive are results to entry timing/day and VIX-derived strike construction?
3. Do adjustments improve tail losses without destroying weekly consistency after costs?
4. Does the signal survive stress slippage without result-driven retuning?

## Closure

The numerical phase ends with:
- PASS: one or more frozen cells clear Base and Stress and are eligible for WFA/OOS;
- FAIL: zero cells clear the frozen gate;
- DATA-BLOCKED: option/VIX data cannot meet the execution/data contract.

No extension of the grid is allowed merely because no cell passes.
