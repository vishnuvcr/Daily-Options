# Phase 31.6 — IV–realized-volatility defined-risk discovery

## Status
CLOSED — discovery complete; no cell advances to WFA/OOS.

## Research question
Can a deterministic intraday NIFTY signal based on the difference between ATM option-implied volatility and a pre-signal realized-volatility estimate identify defined-risk option structures whose net weekly P&L survives Paytm-style costs and Base/Stress slippage?

## Hypothesis
Positive IV–RV dislocations are tested with a defined-risk short iron condor; negative dislocations are tested with a defined-risk long ATM straddle. This is a volatility-pricing hypothesis, not a generic short-volatility search.

## Frozen signal
- Study window: 2021-07-01 through 2026-08-31, subject to exact data coverage.
- Signal: completed 09:30 IST NIFTY bar.
- Realized volatility: 20-session Yang–Zhang annualized volatility, using only sessions strictly before the signal date.
- Implied volatility: ATM call+put straddle implied volatility from the selected NIFTY expiry, solved from 09:30 option opens with Black–Scholes, q=0 and observed NIFTY spot.
- Entry: 09:31 option open.
- Exit: 15:10 same day.
- One trade/day.
- ATM: nearest ₹50 strike.
- Expiry buckets: nearest and next available expiry on/after trade date.

## Frozen finite 12-cell grid
- IV–RV threshold: 2, 4, 6 volatility points.
- Structure side: positive-spread short iron condor / negative-spread long ATM straddle.
- Expiry bucket: nearest and next available.
- Iron-condor wing width: fixed at 200 NIFTY points (not optimized).
- No stop, target, adjustment, leverage, or discretionary override.

The executable implementation must enumerate exactly 12 declared cells (3 thresholds × 2 structure sides × 2 expiry buckets), without adding result-dependent combinations.

## Costs
- Base slippage ₹0.20/order.
- Stress slippage ₹0.40/order.
- Frozen Phase 31.3 transaction/statutory charge model.
- Historical lot-size and expiry schedules mandatory.

## Required outputs
Daily ledger, weekly ledger, Base/Stress summaries, signal/data coverage diagnostics, IV/RV distributions, drawdown/tail-risk diagnostics, parameter heatmap, and accounting reconciliation.

## Promotion
Discovery does not promote a candidate. Any survivor must pass the existing nested WFA and independent later-period OOS gates. No test-period retuning is authorized.

## Stop rule
Close after the finite grid and diagnostics. Do not expand the grid because of observed results.

## Evidence note
NSE states that NIFTY weekly index options expire Tuesday, with the prior trading day used when Tuesday is a holiday; this phase therefore uses the actual expiry files present in the pinned dataset rather than assuming a weekday.

## Phase closure — 2026-09-26
Authoritative workflow run: **36248538306** (Base + Stress + 12-cell validation + persistence succeeded).

Result:
- Base: 0/12 cells met the ₹5,000/week mean + median + ≥70% positive-week gate; all 12 had negative total net P&L.
- Stress: 0/12 cells met the same gate; all 12 had negative total net P&L.
- Best cell by mean weekly net in both frictions: 6 vol-point threshold, positive IV–RV SHORT_CONDOR, nearest expiry bucket, 200-point wings.
- Best Base: 178 trades, total net **-₹23,018.38**, mean weekly **-₹166.80**, median weekly **₹50.11**, positive-week rate **50.00%**.
- Best Stress: 178 trades, total net **-₹34,324.32**, mean weekly **-₹248.73**, median weekly **-₹29.93**, positive-week rate **50.00%**.
- No WFA/OOS validation or parameter selection is authorized from this family.

Data-quality observations are retained in `reports/phase31_6/base/diagnostics.csv` and `stress/diagnostics.csv`; missing ATM-IV observations are common for the next-expiry bucket, so the observed bucket-1 sample is materially smaller than bucket 0. The study is therefore negative evidence for this exact executable definition, not a claim that all NIFTY VRP implementations are unprofitable.
