# Phase 30.2 — Air Defense / India-VIX expected-range Iron Condor

## Purpose
Test the next distinct source-faithful Air Defense structure after the weekly short-strangle near-miss in Phase 30.1. The transcript explicitly says that an iron condor provides built-in hedging for range control.

## Source facts
- India VIX is used to estimate the expected NIFTY range.
- The video demonstrates one-sigma and two-sigma expected ranges.
- The range is a function of VIX, spot and days/time to expiry.
- The method is intended to identify strikes for weekly option selling.
- The video explicitly says that an iron condor provides built-in hedging for range control.
- Exit timing shown is five minutes before expiry.

## Inference controls
- Short CE and PE strikes are selected at/above and at/below the one- or two-sigma expected range.
- Long protective wings are not numerically specified in the transcript, so wing widths are frozen to 100, 200 and 300 NIFTY points before any result is observed.
- Entry offsets and clocks are inherited from the source-faithful Air Defense program: expiry-2/expiry-3 sessions and 09:30/10:00 IST.
- No adjustment is added to the primary iron-condor test because the structure itself is the source-mentioned hedge; adjustment variants would become a separate preregistered family.
- Reference position: one lot on each of four legs.

## Frozen grid
24 cells = 2 entry offsets × 2 entry clocks × 2 sigma levels × 3 wing widths.

## Universe and execution
- TradeMarkk NIFTY 1-minute exact-expiry source revision 51ca58c.
- Normal Tuesday weekly expiries from 2025-09-02 through 2026-08-04.
- Prior-day India VIX close only.
- Entry on next minute open; exit on next executable minute open after 15:25 IST expiry-day reference.
- Paytm Money brokerage ₹10/order; date-aware NSE/statutory charges; Base slippage ₹0.20/order, Stress ₹0.40/order.

## Gate
- mean weekly net ≥ ₹5,000
- median weekly net ≥ ₹5,000
- positive week rate ≥70%
- executed week coverage ≥80%

## Continuation
0 passing cells => retire this Air Defense structure without WFA and move to the next source-faithful YouTube family. Any passing cell => freeze and proceed to nested WFA and independent later OOS.