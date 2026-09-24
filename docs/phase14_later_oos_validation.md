# Phase 14b — Independent Later-Period Validation

The exact Phase 14 nested-walk-forward-selected rule is frozen. No parameter is re-selected on the later sample.

Frozen rule: GLOBAL3 standardized overnight score >= 0.5; NIFTY opening gap >= 0.75%; FADE the gap when global and gap signs disagree; signal 09:30 IST; enter 09:31; long ATM monthly option; hold 20 minutes; stop 30% / target 60%; one lot.

Validation sample: 2021-08-01 through 2024-03-31 from artist-23/nifty-options-data revision 45e0a04, NIFTY/MONTH partition. This period is selected to stay inside the fixed 50-lot-size regime and avoid later lot-size revision boundaries.

Promotion requires mean active-day net >= ₹1,000/lot/day at base, at least two positive calendar years, >=100 trades, and survival under doubled slippage.