# Phase 25 — Falcon Spread Independent Rissin Replication

Purpose: independently replicate the Falcon Spread on a second intraday NIFTY source after Phase 24 exposed severe setup-date sparsity in the TradeMarkk cache. This is data validation, not result-driven retuning.

Research questions:
1. Does the exact source-derived 5:3 ratio-diagonal strangle have sufficient executable observations on an independent source?
2. Does expiry-relative timing produce Friday→Monday→Wednesday for old Thursday expiry and Wednesday→Thursday→Monday for current Tuesday expiry?
3. Does it remain positive after Paytm Money/NSE costs and doubled slippage?
4. If positive, is the sample large enough for frozen nested WFA/OOS?

Pinned independent source: Rissin nse-options-intraday, revision 78b1c5468255d18cf492984bfe6fe4e3ac874d7c. It documents NIFTY 1-minute Upstox data with expiry, strike and option_type fields; this pin contains NIFTY 2024 and 2025 intraday files.

Frozen rules:
- entry = expiry - 4 trading sessions
- adjustment = expiry - 3 trading sessions
- exit = expiry - 1 trading session
- sell 5 near-expiry CE + 5 near-expiry PE near 20/25/30 premium points
- buy 3 next-expiry CE + 3 next-expiry PE near the same target
- primary target 25; primary far mode outward diagonal; SAME_STRIKE sensitivity
- adjustment buys 5 near CE one strike above and 5 near PE one strike below original shorts
- stop 0.5/1.0/1.5× initial gross credit; close trigger, next-minute execution
- signal close, fill next-minute open

Frozen grid: 5 entry times × 3 premium targets × 2 far modes × 3 adjustment times × 3 stops = 270 cells.

Gates: both pinned files present; at least 20 distinct executable setup dates; base and stress both reported. A target-sized result with very few active dates is not promotion evidence. Positive adequately sampled replication advances unchanged to Phase 26 WFA/OOS. Negative replication retires the Falcon family.

Costs: Paytm Money ₹20/order; date-aware NSE STT and transaction charges; SEBI fee; stamp duty; GST; base slippage 0.20 premium points/order; stress 0.40.

Audit: Phase 24 undercoverage is logged as E0237; its numerical leaderboard is not accepted as strategy evidence.
