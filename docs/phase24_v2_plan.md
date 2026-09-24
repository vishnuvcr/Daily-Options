# Phase 24 v2 Plan — Falcon Spread on independent Rissin/Upstox 1-minute data

## Purpose
Validate the frozen Phase 24 Falcon Spread rules on an independent intraday source after the pinned TradeMarkk source proved too sparse to support inference.

## Source and evidence
Primary independent source: rissin/nse-options-intraday, immutable revision 78b1c5468255d18cf492984bfe6fe4e3ac874d7c.
The dataset documentation states that its upstox_intraday track contains 1-minute NIFTY/BANKNIFTY/SENSEX data from October 2024 onward, with explicit expiry, strike, option_type, OHLC and IST timestamps. citeturn840136search3turn792835search0
The current NSE specification says NIFTY 50 weekly options expire every Tuesday; a Tuesday trading holiday moves expiry to the previous trading day. citeturn840136search1turn840136search2

## Frozen strategy rules
The Phase 24 v1 grid is carried forward unchanged:
- 5 entry times: 09:30, 10:00, 11:00, 13:00, 14:00 IST.
- 3 target-premium bands: 20, 25, 30 points.
- 2 far-week strike modes: DIAGONAL_PREMIUM, SAME_STRIKE.
- 3 adjustment times: 09:30, 10:00, 11:00 IST.
- 3 hard-stop multiples: 0.50, 1.00, 1.50 × initial gross credit.
- Total: 270 frozen variants.

Legs:
- Entry: sell 5 near-week CE + 5 near-week PE near target premium.
- Simultaneously buy 3 next-week CE + 3 next-week PE near target premium.
- Adjustment: buy 5 CE one listed strike above the original short CE and 5 PE one listed strike below the original short PE.
- Hard stop uses leak-safe minute marks and next-minute-open execution.
- Exit is the last available minute of the pre-expiry session.

## Current expiry-relative timing
Source-era Thursday expiry:
Friday entry → Monday adjustment → Wednesday exit.

Trading-session offsets:
- entry = expiry − 4 sessions
- adjustment = expiry − 3 sessions
- exit = expiry − 1 session

Current Tuesday-expiry analogue:
Wednesday entry → Thursday adjustment → Monday exit.

The code derives these dates from actual expiry and available trading sessions, including holiday weeks. citeturn840136search1turn840136search2

## Validation population
- Start: 2025-09-01
- End: maximum available date in pinned Rissin files, capped at 2026-08-31.
- Current Tuesday-expiry regime only.
- April-August 2025 Monday-expiry transition excluded.

## Costs
- Paytm Money model: ₹20 per executed F&O order, represented as ₹40 roundtrip brokerage per leg.
- Base slippage: 0.20 premium points/order.
- Stress slippage: 0.40 premium points/order.
- Option-sale STT: 0.10% through 2026-03-31 and 0.15% from 2026-04-01. citeturn840136search0
- NSE option premium transaction charge: 0.03503% before 2026-03-01 and 0.0355299% from 2026-03-01.
- SEBI: 0.0001%.
- Stamp duty: 0.003% on buys.
- GST: 18% on brokerage + exchange + SEBI.

## Gates
Reject as non-evidentiary if unique executable entry dates <20, unit tests fail, expiry/date alignment requires future information, duplicate rows contaminate legs, or levy calculations fail reconciliation.

## Deliverables
Coverage JSON, trade CSV, 270-cell leaderboard, base/stress summaries, unit tests, manual GitHub Actions workflow, status/error logs, and a later frozen WFA/OOS branch only if the source clears the data and performance gates.

## Status
2026-09-25 — TradeMarkk v1 is data-limited: only 5 unique executable entry dates. This v2 branch uses independent Rissin/Upstox minute data and carries forward the exact frozen strategy grid.
