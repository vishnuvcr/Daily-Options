# Phase 30 — Equity Income / NIFTY Iron Dome weekly numerical backtest

## Objective

Evaluate the frozen Phase 29.5 Iron Dome formalization family on historical exact-expiry NIFTY 1-minute option data. This is the first numerical phase for the Equity Income YouTube program.

The active economic objective is ₹5,000 NET per completed trading week at the declared reference position size, after Paytm Money/NSE costs and Base/Stress slippage. The retired ₹1,000-per-day criterion is not used.

## Frozen 12-cell grid

- Entry: expiry minus 4, 3, or 2 trading sessions.
- Entry clock: 09:30 IST.
- Initial center: nearest 50-point strike to 09:30 NIFTY spot, plus one 50-point strike as the source-anchored bearish formalization.
- Wings: ±200 points.
- Ratio: 1:1:1:1.
- Trigger A: underlying moves 120 points from the active center reference toward a challenged side.
- Trigger B: running gross mark-to-market loss reaches 60% of the current active structure's defined maximum loss.
- Adjustment A: close the active four-leg structure and rebuild a 200-point centered four-leg structure around current rounded ATM; maximum two adjustments.
- Adjustment B: close only the challenged short leg and move it one 50-point strike deeper ITM; other active legs are preserved; maximum two adjustments.
- Exit: 15:00 IST on expiry day, executed on the next minute open to enforce the information barrier.
- Maximum adjustments: 2.

These are the bounded source-anchored formalizations from Phase 29.5, not claims that the videos specified every mathematical detail.

## Execution model

- Signal marks use minute closes available at or before the signal timestamp.
- Any signal at t is filled at the next available minute open.
- No bid/ask is inferred.
- OHLC is used as an explicitly labelled executable-price proxy.
- Base slippage: 0.20 premium points per executed order.
- Stress slippage: 0.40 premium points per executed order.
- Every executed order receives Paytm Money brokerage and date-aware NSE/statutory charges.
- Historical NIFTY lot size is selected by expiry date from the registered schedule.
- Current and historical NIFTY expiry weekday changes are handled by expiry-relative trading-session offsets, never by hard-coded weekday labels.

## Weekly evaluation

Each completed expiry week contributes one weekly strategy result per cell when the frozen rule is executable.

Primary metrics:
- mean weekly net P&L;
- median weekly net P&L;
- profitable-week rate;
- executed-week coverage;
- worst week;
- weekly max drawdown;
- profit factor;
- expected shortfall / lower-tail loss;
- calendar-year and regime breakdown;
- transaction-cost and slippage sensitivity.

Preliminary target gate:
- mean weekly net ≥ ₹5,000;
- median weekly net ≥ ₹5,000;
- profitable-week rate ≥70%;
- executed-week coverage ≥80%.

A cell is not promoted from the preliminary leaderboard. Any survivor must enter a separate untouched nested walk-forward and independent later-period validation branch.

## Data

Primary source: thetrademarkk/india-index-options-1m, revision 51ca58c.
Expected files:
- index/NIFTY.parquet
- options/NIFTY/{expiry}.parquet

The GitHub Actions workflow must cache the pinned source and validate expiry-file/date coverage before simulation.

## Outputs

- reports/base/trades.csv
- reports/stress/trades.csv
- reports/base/leaderboard.csv
- reports/stress/leaderboard.csv
- reports/base/weekly.csv
- reports/stress/weekly.csv
- reports/base/summary.json
- reports/stress/summary.json

## Stop condition

Do not tune the 12-cell grid from numerical results. Phase 30 preliminary execution ends after Base and Stress complete and the frozen leaderboard plus weekly-consistency metrics are reviewed.
