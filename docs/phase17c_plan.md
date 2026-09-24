# Phase 17c — Executable Entry Exact-Expiry

## Purpose
Resolve the source's sparse per-strike minute coverage without changing the Phase 17 signal hypothesis.

## Frozen signal rule
All 384 signal variants remain unchanged:
3 entry times × 2 skew thresholds × 2 jump brakes × 2 RV states × 2 widths × 2 holds × 2 stop ratios × 2 sides.

## Execution feasibility rule
At each signal timestamp, select the earliest common minute at or after signal+1 minute where both the short and wing option have executable OHLC rows, with a hard maximum delay of 3 minutes.
Record the actual entry delay in minutes.
Signals with no common executable quote inside the bound are skipped.

No P&L-based selection of the 3-minute bound is performed; it is a pre-specified data/execution constraint.

## Economics
Entry price: option OPEN on the executable minute.
Exit: paired option OHLC bars through 15/30 minutes after entry.
Costs: Paytm Money/NSE model; base slippage ₹0.20/leg; stress ₹0.40/leg.
Target metric: mean active-day net.

## Promotion
Base and stress must complete, and the candidate must still pass untouched walk-forward/holdout validation at ₹1,000 net per active lot per active trading day.


## 2026-09-24 — Phase 17c v2 implementation correction

The authoritative v2 engine preserves the pre-specified 3-minute maximum entry delay and earliest common short/wing minute, but now loads the entire signal-to-signal+3-minute quote window. This corrects an implementation mismatch that otherwise prevented +2/+3 minute quotes from being visible. No signal or economic parameter changes.
