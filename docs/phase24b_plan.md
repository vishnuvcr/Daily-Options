# Phase 24b Plan — Falcon Spread Independent Rissin/Upstox Replication

## Purpose
Replicate the frozen Falcon Spread rules on an independent 1-minute NIFTY options source after the primary TradeMarkk cache was found to be materially under-covered. This is a source-replication phase, not a parameter-retuning phase.

## Research questions
1. Does the frozen 5:3 weekly ratio-diagonal strangle remain positive after realistic Paytm Money/NSE costs on an independent source?
2. Does the source-derived expiry-relative timing remain executable with exact expiry metadata?
3. Does the family survive doubled slippage and multiple calendar regimes without depending on a handful of trades?
4. Does any frozen configuration justify a separate untouched walk-forward/OOS validation?

## Frozen strategy rules inherited from Phase 24
- Old source geometry: Friday entry → Monday adjustment → Wednesday exit under Thursday expiry.
- Current Tuesday-expiry analogue: Wednesday entry → Thursday adjustment → Monday exit.
- Formal offsets: entry = expiry − 4 trading sessions; adjustment = expiry − 3 sessions; exit = expiry − 1 session.
- Entry: sell 5 near-expiry CE + 5 near-expiry PE and buy 3 next-expiry CE + 3 next-expiry PE.
- Entry strike/premium rule: near legs and far legs are selected around the frozen target premium; 25 points is the source-primary target.
- Far-strike modes: DIAGONAL_PREMIUM and SAME_STRIKE.
- Adjustment: buy 5 near-expiry CE one listed strike above the original short CE and 5 near-expiry PE one listed strike below the original short PE.
- Entry times: 09:30, 10:00, 11:00, 13:00, 14:00 IST.
- Premium targets: 20, 25, 30 points.
- Adjustment times: 09:30, 10:00, 11:00 IST.
- Hard stops: 0.50, 1.00, 1.50 × initial gross credit.
- Stop mark: close-to-close; execution is the next minute open.
- Exit: 15:15 on the pre-expiry trading session when no stop has triggered.
- No parameter retuning is allowed from this independent dataset.

## Independent data source
Hugging Face dataset: rissin/nse-options-intraday.
- Intraday source: Upstox historical 1-minute candles.
- NIFTY intraday coverage advertised from October 2024 through 2026.
- Canonical fields include trade date, IST timestamp, exact expiry, strike, CE/PE, OHLC, volume and OI.
- Reproducibility pin: dataset commit 78b1c5468255d18cf492984bfe6fe4e3ac874d7c.
- Workflow downloads only the NIFTY 2024, 2025 and 2026 partitions and caches them.

Source documentation: https://huggingface.co/datasets/rissin/nse-options-intraday

## Coverage gate
The workflow must fail before P&L if:
- 2024, 2025 and 2026 NIFTY yearly files are not present;
- minimum observed NIFTY date is after 2024-10-01 or maximum observed date is before 2026-08-04;
- fewer than 400 distinct NIFTY trading dates are present;
- fewer than 80 distinct exact-expiry dates are present;
- fewer than 80 executable expiry-relative candidate entry dates are derivable.

A cache's mere existence is not sufficient.

## Costs and execution
Inherited unchanged from Phase 24:
- Paytm Money brokerage ₹20/order.
- Option-sale STT: 0.10% before 2026-04-01; 0.15% on/after 2026-04-01.
- Stamp duty on buys: 0.003%.
- SEBI fee: 0.0001%.
- NSE premium transaction charge: 0.03503% before 2026-03-01; 0.0355299% from 2026-03-01.
- GST: 18% on brokerage + exchange + SEBI charges.
- Base slippage: 0.20 premium points/order.
- Stress slippage: 0.40 premium points/order.

## Statistical analysis
Report for every frozen cell:
- mean and median net P&L per active trading day per active lot-equivalent;
- active-day count and trade count;
- win rate and profit factor;
- maximum drawdown from daily active-day P&L;
- calendar-year breakdown;
- base vs stress comparison.

A positive independent-source result is not automatically promoted. A candidate may advance only after a separately preregistered untouched WFA/OOS validation branch. A sparse sample is rejected as non-evidentiary.

## Decision rules
- If the 25-point source-primary geometry is non-positive and the frozen family has no robust target-level evidence, retire the Falcon family.
- If one or more frozen cells are strongly positive on this independent source, freeze the exact cell(s) without retuning and launch Phase 24c for untouched WFA/OOS.
- Never use the independent-source leaderboard to invent a new parameter combination.

## Phase status
2026-09-25 — Phase 24 primary source is data-limited. Phase 24b begins independent exact-expiry replication on Rissin/Upstox with the complete 270-cell frozen grid.