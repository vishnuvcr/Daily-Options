# Phase 24 Plan — Falcon Spread: 5:3 Weekly Ratio-Diagonal Strangle With Monday Caps

## Purpose
Translate the user-supplied transcript summary of Equity Income's "Falcon Spread - Top Hedging Trick Public Won't Know" into a deterministic, transaction-level NIFTY options backtest.

## Research questions
1. Does the Friday 5:3 near-week/far-week ratio-diagonal strangle generate positive net P&L after realistic Paytm Money/NSE costs?
2. Does the Monday one-strike outer-wing conversion materially reduce tail losses without destroying the theta-capture edge?
3. Does the structure remain profitable under doubled slippage and across years/regimes?
4. Can any frozen configuration reach the project gate of >= ₹1,000 net per active lot per active trading day in untouched validation?

## Source-derived rules
- Friday: sell 5 near/current-week CE and 5 near/current-week PE at approximately 25 premium points each.
- Friday: buy 3 next-week CE and 3 next-week PE at approximately the same 25-point premium zone.
- Monday: buy 5 near-week CE one strike above the original short CE and 5 near-week PE one strike below the original short PE.
- Hard stop is mandatory; the supplied summary does not give a numeric threshold.
- **Current-rule translation:** NIFTY weekly options now expire Tuesday, so the analogue of "close by Wednesday, avoid Thursday 0-DTE" is **close on Monday before the Tuesday expiry session**. NSE's transition changed NIFTY weekly expiry from Thursday to Tuesday effective for new contracts expiring on/after 2025-09-01. citeturn431147search15turn431147search2
- Avoid deliberately tightening the initial strangle toward richer premiums such as 50 points.

## Formalization of unspecified items
These are modelling choices, not claims about the video:
- Friday entry-time sensitivity: 09:30, 10:00, 11:00, 13:00, 14:00 IST.
- Premium target sensitivity: 20, 25, 30 points, with 25 as the source-primary cell.
- Far-week strike mode: DIAGONAL_PREMIUM (primary; independent strike closest to target premium while remaining no-closer-to-ATM than the near short) and SAME_STRIKE (sensitivity).
- Monday adjustment time: 09:30, 10:00, 11:00 IST.
- Hard-stop threshold: 0.50, 1.00, 1.50 × initial gross credit. Stop is evaluated on close-to-close mark-to-market and exits at the next minute open.
- Friday signal uses the minute close; actual opening fills are taken from the next minute open, preventing look-ahead.
- Monday wing purchase uses the Monday signal minute close and the next minute open.
- The exit is the last available minute of the **pre-expiry trading session**. Under the current Tuesday-expiry regime this is Monday, with execution at the next available open where present; otherwise the last valid close is used.
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
2026-09-25 — current-expiry translation corrected: Monday is the pre-expiry exit day for today's Tuesday NIFTY weekly expiry. Historical runs use the actual contract expiry and its immediately preceding trading session; Monday-expiry transition contracts are excluded because the source's Monday adjustment and pre-expiry exit cannot both be satisfied.