# Phase 31.5 — finite candidate testing v1

## Purpose
Test the first data-gated, materially distinct candidate family: NIFTY opening-range breakout (ORB) translated into defined-risk option debit spreads.

Global-gap, India-VIX, and order-book families remain blocked by the Phase 31.4 data gate and are not silently substituted.

## Frozen research question
Can a deterministic NIFTY ORB signal, using only information available by the breakout minute, produce positive weekly net P&L after Paytm-style costs and Base/Stress slippage?

## Frozen grid
- OR windows: 5, 15, 30 minutes.
- Break multiplier: 0.25, 0.50, 1.00 × opening-range width beyond the OR high/low.
- Direction: continuation only; long call debit spread for upside break, long put debit spread for downside break.
- Entry: first 1-minute bar whose close crosses the threshold after the OR window.
- Option structure: buy near-ATM option and sell one further OTM option, 200-point strike separation.
- Expiry: nearest available expiry >= trade date.
- Entry price: option open at signal minute.
- Exit: 15:10 same day.
- No stop-loss/target in this discovery grid.
- One trade per day maximum.
- ATM: nearest ₹50 strike to NIFTY spot at signal.
- Slippage: Base ₹0.20/order; Stress ₹0.40/order.
- Full transaction/statutory charges using the frozen Phase 31.3 model.
- No parameter selection using test results.

## Information barrier
Opening range uses bars strictly before the breakout test. Signal is generated only after a completed 1-minute bar. Contract selection uses only signal-time spot and the deterministic nearest-expiry rule.

## Acceptance / rejection
Discovery outputs every grid cell. No promotion is permitted from discovery alone. A candidate may advance to nested WFA only if the preregistered Phase 30 promotion gates are met on the designated OOS protocol.

## Required outputs
- Cell-level daily ledger
- Weekly ledger
- Base and Stress summaries
- Coverage/missing-data diagnostics
- Parameter heatmap CSV
- Drawdown and tail-risk diagnostics
- Explicit rejection reasons
