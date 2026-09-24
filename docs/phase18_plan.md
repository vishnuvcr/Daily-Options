# Phase 18 — NIFTY Iron Condor Regime

Research question: can a late-day, low-jump, low-realized-volatility NIFTY iron condor with exact-expiry execution produce ≥₹1,000 net per active lot/day after realistic costs?

Frozen grid: 3 entry times × 2 short offsets × 2 wing widths × 2 absolute-return brakes × 2 RV-ratio ceilings × 2 holds × 2 stops = 192 cells.

Entry feasibility: earliest common short/wing quote minute within 3 minutes after the frozen signal. No signal/risk parameter is re-tuned based on test results.

Base/stress slippage: ₹0.20/leg and ₹0.40/leg. Paytm Money/NSE cost model and date-aware NIFTY lot sizes are mandatory.

Promotion requires positive stress performance, sufficient coverage, and untouched walk-forward validation with at least one ≥₹1,000/active-lot/day test window.
