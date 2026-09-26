# Phase 30.4 — Contract/data feasibility result

## NIFTY contract geometry

NSE's current equity-derivatives contract specifications state that NIFTY 50 index options have four weekly expiry contracts (excluding the monthly contracts) and that the expiry day is Tuesday, moving to the previous trading day if Tuesday is a trading holiday. This is the current contract framework as published by NSE and updated August 11, 2026.

## Historical NIFTY lot-size schedule for the research window

NSE Circular NSE/FAOP/70616 dated October 3, 2025 revised NIFTY market lot from 75 to 65 and specified that the revised lot applies after the transition; existing weekly/monthly contracts continued with the existing lot through the December 30, 2025 expiry.

For a Sep 1, 2025 through Aug 31, 2026 backtest window, the source-backed ordinary weekly-expiry schedule is therefore:

| Expiry date | Lot size |
|---|---:|
| Through 2025-12-30 | 75 |
| From 2026-01-06 | 65 |

This matches the lot-size transition already encoded in the Falcon runtime.

## Intraday data readiness

The Rissin/Hugging Face dataset card documents NIFTY 1-minute intraday coverage from October 2024 onward, in Parquet files partitioned by year. Its canonical schema includes trading date, timestamp, expiry, strike, option type, OHLC, source, and granularity.

The completed Falcon runtime run pinned the source revision during execution and found 32 calendar expiries within its working window (September 2025 through August 2026 cap). Both Base and Stress acquired the exact NIFTY 2025/2026 files successfully.

## Blocking condition

Data and contract infrastructure are sufficient for a later numerical test, but the Bear Put strategy itself remains **not authorized for P&L testing**. The source transcript does not yet freeze the exact weekly/monthly expiry choice, a deterministic resistance rule, a quantitative crack/gap-down trigger, a fixed stop-loss, a fixed profit target, or a fixed time exit.

## Next phase
Source-resolution extension is required before any result-driven grid is defined. Any interpretation of an unresolved source rule must be preregistered as an experimental dimension and kept out of the strategy promotion gate until validated out-of-sample.
