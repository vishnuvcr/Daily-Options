# Phase 14c — Independent Contract-Level Validation

The exact Phase 14 walk-forward-selected rule is frozen. No parameter search is performed in this phase.

Frozen rule: GLOBAL3 >= 0.5; NIFTY gap >= 0.75%; FADE when global and gap signs disagree; signal 09:30 IST; next-minute entry; long ATM option; monthly-contract selection; 20-minute hold; stop 30% / target 60%; one lot.

Validation source: thetrademarkk/india-index-options-1m, pinned to revision 0f4800e from the dataset's verified current tree. The dataset describes `index/NIFTY.parquet` and expiry-level `options/NIFTY/{EXPIRY}.parquet` files, with option expiry and strike fields, and coverage roughly 2021–2026. citeturn601520search0turn554040view0

Validation period: 2021-08-01 through 2024-03-31, fixed 50-lot regime.

Promotion requires >=₹1,000 mean active-day net, >=100 trades, at least two positive calendar years, and survival under doubled slippage.