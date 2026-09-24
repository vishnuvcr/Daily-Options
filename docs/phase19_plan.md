# Phase 19 — NIFTY Short Strangle Regime

Research question: can a late-day, low-jump, low-realized-volatility NIFTY short strangle generate at least ₹1,000 net per active lot/day after realistic brokerage, statutory charges, exchange fees and stressed slippage?

Frozen grid: 3 entry times × 3 symmetric short offsets (ATM±1/2/3) × 2 absolute-return brakes × 2 RV-ratio ceilings × 2 holds × 2 stops = 144 cells.

Entry feasibility: earliest common PE/CE quote minute within 3 minutes after the frozen signal. No result-driven parameter retuning.

Exit: stop when combined option debit reaches 1.25× or 1.50× entry credit; target at 50% of entry credit; otherwise time exit at 15 or 30 minutes.

Base/stress slippage: ₹0.20 and ₹0.40 per option leg. Exact-expiry TradeMarkk source, date-aware NIFTY lot sizes, Paytm Money/NSE cost model.

Promotion: stress-positive, adequate coverage, and untouched walk-forward performance with at least one ₹1,000/active-lot/day test window. A positive in-sample cell is not a strategy promotion by itself.
