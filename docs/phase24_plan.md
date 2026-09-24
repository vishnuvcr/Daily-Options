# Phase 24 Plan — Falcon Spread: 5:3 Weekly Ratio-Diagonal Strangle With Expiry-Relative Timing

## Purpose
Translate the user-supplied transcript summary of Equity Income's "Falcon Spread - Top Hedging Trick Public Won't Know" into a deterministic, transaction-level NIFTY options backtest.

## Research questions
1. Does the 5:3 near-week/far-week ratio-diagonal strangle generate positive net P&L after realistic Paytm Money/NSE costs, using expiry-relative timing?
2. Does the one-strike outer-wing conversion materially reduce tail losses without destroying the theta-capture edge?
3. Does the structure remain profitable under doubled slippage and across years/regimes?
4. Can any frozen configuration reach the project gate of >= ₹1,000 net per active lot per active trading day in untouched validation?

## Source-derived rules
- Entry: preserve the source's expiry-relative distance. The old Thursday-expiry source entered on **Friday**; shifting the expiry day two calendar days earlier to Tuesday makes the current-rule entry **Wednesday**.
- At entry, sell 5 near/current-week CE and 5 near/current-week PE at approximately 25 premium points each.
- At entry, buy 3 next-week CE and 3 next-week PE at approximately the same 25-point premium zone.
- Adjustment: the source's old Monday adjustment shifts two days earlier with the expiry change, giving **Friday adjustment** for current Tuesday expiry.
- Friday adjustment: buy 5 near-week CE one strike above the original short CE and 5 near-week PE one strike below the original short PE.
- Exit: the source's old Wednesday exit shifts two days earlier, giving **Monday exit**, avoiding Tuesday 0-DTE.
- Hard stop is mandatory; the supplied summary does not give a numeric threshold.
- **Current-rule translation:** NIFTY weekly options now expire Tuesday, so the analogue of "close by Wednesday, avoid Thursday 0-DTE" is **close on Monday before the Tuesday expiry session**. NSE's transition changed NIFTY weekly expiry from Thursday to Tuesday effective for new contracts expiring on/after 2025-09-01. citeturn431147search15turn431147search2
- Avoid deliberately tightening the initial strangle toward richer premiums such as 50 points.

## Formalization of unspecified items
These are modelling choices, not claims about the video:
- Wednesday/current-regime entry-time sensitivity: 09:30, 10:00, 11:00, 13:00, 14:00 IST.
- Premium target sensitivity: 20, 25, 30 points, with 25 as the source-primary cell.
- Far-week strike mode: DIAGONAL_PREMIUM (primary; independent strike closest to target premium while remaining no-closer-to-ATM than the near short) and SAME_STRIKE (sensitivity).
- Friday/current-regime adjustment-time sensitivity: 09:30, 10:00, 11:00 IST.
- Hard-stop threshold: 0.50, 1.00, 1.50 × initial gross credit. Stop is evaluated on close-to-close mark-to-market and exits at the next minute open.
- Entry signal uses the entry-session minute close; actual opening fills are taken from the next minute open, preventing look-ahead.
- Adjustment wing purchase uses the adjustment-session signal minute close and the next minute open.
- Timing is encoded by trading-session offsets from the actual weekly expiry: entry = expiry − 4 trading sessions; adjustment = expiry − 2 trading sessions; exit = expiry − 1 trading session. Thus Thursday-era contracts map to Friday/Monday/Wednesday, while current Tuesday-era contracts map to Wednesday/Friday/Monday.
- One strike means one listed strike increment in the exact-expiry chain, not a hard-coded 50-point assumption.

## Frozen grid
5 entry times × 3 premium targets × 2 far-strike modes × 3 Monday adjustment times × 3 hard stops = 270 cells.

## Data
Pinned exact-expiry source: thetrademarkk/india-index-options-1m, revision 51ca58c.
- index/NIFTY.parquet
- options/NIFTY/{YYYY-MM-DD}.parquet

## Costs and execution
The research cost model uses:
- Paytm Money brokerage: ₹20/order
- NSE option-sale STT: 0.15%
- stamp duty on buys: 0.003%
- SEBI fee: 0.0001%
- NSE option premium turnover: 0.03503%
- GST: 18% on brokerage + exchange + SEBI charges
- Base slippage: 0.20 premium points per order
- Stress slippage: 0.40 premium points per order

## Statistical analysis
Primary metric: mean net P&L per active trading day per active lot-equivalent. Also report median active-day P&L, win rate, profit factor, expectancy, maximum drawdown, trade/day concentration, year/regime breakdown and cost sensitivity.

A preliminary positive result is not promoted. Any cell clearing the preliminary target in both friction settings must enter a new untouched nested-WFA/OOS stage with no result-driven retuning.

## Stop/retirement rules
- If no cell is positive after Base and Stress and no cell is near the target, retire the family without retuning.
- If a cell is strong enough to justify continuation, freeze its exact parameters and proceed to a separate validation branch.
- All implementation defects are logged before accepting P&L.

## Phase status
2026-09-25 — current-expiry translation corrected to expiry-relative session offsets: **Wednesday entry → Friday adjustment → Monday exit** for current Tuesday NIFTY expiry. Historical validation preserves the old Friday → Monday → Wednesday sequence for Thursday-expiry contracts automatically.