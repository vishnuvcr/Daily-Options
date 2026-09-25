# Phase 30.1 — Equity Income Air Defense / India-VIX expected-range weekly strategy

## Purpose
Test the source-resolved Air Defense candidate from Equity Income video aRjY_O6U3nQ after the Phase 30 Iron Dome retirement.

## Source facts
- Weekly option selling is the stated use case.
- India VIX is used to estimate an expected NIFTY range.
- The video demonstrates 1-sigma and 2-sigma ranges.
- The range depends on India VIX, spot and time/days to expiry.
- Strike selection is intended to be range-driven rather than trial-and-error.
- A short-strangle example is used for range defence.
- When price approaches the range/short strike, the stated response is to reduce size or hedge.
- The example exits about five minutes before expiry.
- The video also discusses an iron condor as a built-in hedge, but that is not mixed into the primary short-strangle family.

## Registered inferences
- Use the previous completed trading day's India VIX close to preserve the information barrier.
- Expected move = spot × (VIX/100) × sqrt(minutes_to_exit / (365×24×60)) × sigma.
- Select the nearest listed CE at/above spot + expected move and PE at/below spot − expected move from the exact-expiry strike universe.
- Test expiry-relative entry offsets −2 and −3 sessions and clocks 09:30/10:00 IST.
- Test adjustment modes NONE, reduce challenged short at 50% of the distance toward its short strike, and reduce at 75%.
- With a one-lot-per-short reference position, reduction is implemented as closing the challenged short; no undocumented hedge is inserted.
- No numeric stop is invented. The initial family uses the source's range-reduction rule and time exit.

## Frozen grid
24 cells = 2 entry offsets × 2 entry clocks × 2 sigma levels × 3 adjustment modes.

## Universe
- Pinned TradeMarkk NIFTY 1-minute exact-expiry source revision 51ca58c.
- Primary sample: normal Tuesday weekly expiries from 2025-09-02 through 2026-08-04.
- Tuesday-holiday/previous-trading-day expiries are excluded from the primary sample rather than changing the source weekend geometry.

## Information barrier
- Spot and option marks use only information at or before signal time.
- Entry and adjustment signals fill on the next minute open.
- Exit is the next executable minute open after the five-minute-before-expiry reference.
- VIX input is strictly prior-day close.

## Costs
- Reference size: 1 NIFTY lot short CE + 1 NIFTY lot short PE.
- Current Paytm Money F&O brokerage: ₹10 per executed order.
- Reuse the Phase 30 date-aware NSE/statutory charge framework.
- Base slippage ₹0.20/order; Stress ₹0.40/order.
- ₹20/order brokerage remains an optional post-run sensitivity only.

## Preliminary weekly gate
- Mean weekly net ≥ ₹5,000.
- Median weekly net ≥ ₹5,000.
- Positive eligible weeks ≥70%.
- Executed eligible weeks ≥80%.

## Continuation
If no cell passes, retire the family without WFA and advance to the next distinct source-faithful family. If a cell passes, freeze it and open a separate nested-WFA/later-OOS phase. No test-period tuning is allowed.

## Outputs
`reports/phase30_1_air_defense/base/` and `reports/phase30_1_air_defense/stress/` plus status/error/ledger updates.