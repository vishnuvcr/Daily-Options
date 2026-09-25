# Phase 30 v7 — Corrected weekly Iron Dome rerun

## Purpose
Rerun the frozen 12-cell Phase 30 Iron Dome numerical experiment after the first vectorized result was invalidated by an option-series data-loader defect.

## Correction
Each NIFTY options parquet is already scoped to one exact expiry. The corrected loader therefore selects rows by timestamp range, strike and option side and preserves the full series from execution through expiry. It no longer filters the parquet by the single entry or adjustment trading day.

A regression test constructs a synthetic exact-expiry parquet with two trading days and verifies that both days remain available to the simulator.

## Frozen experiment
The strategy grid is unchanged: entry offsets expiry−4, expiry−3 and expiry−2 trading sessions; 09:30 IST signal; source-anchored centre; ±200-point wings; WING_60 or RISK_60 trigger; RECENTER_BOTH or ONE_STRIKE_INSIDE adjustment; maximum two adjustments; 15:00 expiry-day exit at next-minute open.

## Costs
Base/Stress slippage remains ₹0.20 / ₹0.40 premium points per executed order. NSE option transaction charges, option-sale STT, SEBI turnover fee, stamp duty, GST and historical NIFTY lot size remain date-aware. The research keeps a conservative fixed ₹20 brokerage assumption per executed F&O order for comparability rather than silently changing the preregistered cost model.

## Acceptance
No v7 P&L is accepted until the corrected Base and Stress runs complete, coverage is validated, the weekly leaderboard is inspected, and any surviving cell advances to the preregistered WFA and independent later-period OOS gate. The active YouTube objective is ₹5,000 net per completed trading week at fixed reference sizing.