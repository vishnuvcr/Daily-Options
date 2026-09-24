# Phase 14d — Frozen Rule Validation on Rissin 1-Minute NIFTY Options

The Phase 14 rule is frozen exactly as selected by the original 2019–2020 nested walk-forward. No parameter search is performed.

Frozen rule: GLOBAL3 >= 0.5; opening gap >= 0.75%; FADE when the global and gap signs disagree; 09:30 IST signal; next-minute entry; long ATM NIFTY option; monthly expiry; 20-minute hold; stop 30% / target 60%; historical lot size by expiry.

Validation source: rissin/nse-options-intraday, pinned to commit 78b1c5468255d18cf492984bfe6fe4e3ac874d7c. Its dataset card documents NIFTY 1-minute intraday coverage from Oct 2024 onward, with expiry, strike and option_type fields. citeturn597354search0turn597354search1turn597354search2

Spot source: thetrademarkk/india-index-options-1m NIFTY index 1-minute file, pinned to revision 0f4800e. Its dataset card describes ~2021–2026 NIFTY 1-minute index coverage and the NIFTY index file. citeturn601520search0turn601520search1

Validation window: 2024-10-01 through 2026-06-30.

Promotion requires >=100 executable trades, mean active-day net >=₹1,000 at base friction, at least two positive years, and survival under doubled slippage.