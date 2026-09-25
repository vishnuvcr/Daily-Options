# Phase 30.2 — Falcon Spread weekly independent replication

## Purpose
Complete the previously blocked Falcon Spread independent-source replication using the Equity Income source mechanics already formalized, but apply the current research target of ₹5,000 NET per completed trading week.

## Source-faithful mechanics
- Source-era sequence: Friday entry → Monday defensive wing purchase → Wednesday exit for Thursday expiry.
- Current NIFTY Tuesday-expiry analogue: **Wednesday entry → Thursday adjustment → Monday pre-expiry exit**.
- Initial structure: sell 5 near-week CE + 5 near-week PE around a registered premium band; buy 3 next-week CE + 3 next-week PE.
- Adjustment: buy 5 near-week CE one listed strike above the original short CE and 5 near-week PE one listed strike below the original short PE.
- Hard stop is a preregistered multiple of initial gross credit.
- No holding into 0-DTE expiry.

## Frozen grid
270 cells:
- entry: 09:30, 10:00, 11:00, 13:00, 14:00 IST
- target premium: 20, 25, 30 points
- far-week mode: DIAGONAL_PREMIUM, SAME_STRIKE
- adjustment time: 09:30, 10:00, 11:00 IST
- stop multiple: 0.50, 1.00, 1.50 × initial gross credit

No result-driven selection.

## Independent data
Use the Rissin/Upstox NIFTY 1-minute parquet source. The pinned 78b1 dataset commit is retained as the provenance anchor, but the workflow resolves the repository's current dataset commit at runtime because the historical pinned snapshot exposed an incomplete NIFTY-year file set to the GitHub runner. The resolved SHA is persisted with the run; no unpinned data is silently mixed into the backtest.

The dataset documentation describes 1-minute NIFTY options from October 2024 onward with explicit expiry, strike, option type and IST timestamps. citeturn0search0turn0search1

## Information barrier
All entry/adjustment selections use only timestamps at or before the signal. Fills use the next minute open. Stop marks trigger on minute closes and execute on the next minute open. Exit uses the last available minute of the pre-expiry session.

## Costs
- Paytm Money current F&O FAQ reports ₹10 per executed F&O order; use ₹10/order as Base and ₹20/order as a conservative brokerage sensitivity.
- Base slippage ₹0.20 premium points/order.
- Stress slippage ₹0.40 premium points/order.
- NSE/STT/SEBI/stamp/GST are included using the repository's date-aware framework.

## Weekly promotion gate
A variant is preliminarily qualified only if:
- mean weekly net ≥ ₹5,000;
- median weekly net ≥ ₹5,000;
- profitable-week rate ≥70%;
- at least 20 completed weeks and ≥80% execution coverage.

Report worst week, max drawdown, profit factor, expected shortfall, 2025/2026 breakdown and Base vs Stress.

## Continuation
- If 0 variants pass: retire Falcon without WFA and proceed to the next distinct source-faithful candidate.
- If ≥1 passes: freeze passing cells and open a separate nested-WFA/OOS phase.
