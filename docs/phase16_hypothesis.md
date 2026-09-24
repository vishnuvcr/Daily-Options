# Phase 16 — IV-Skew Tail Credit Vertical

Research question: can extreme intraday NIFTY IV skew, standardized using only prior observations and filtered by a short-horizon jump brake, identify a rich option wing that can be sold through a defined-risk credit vertical?

Fixed grid: 3 entry times × 3 skew-z thresholds × 2 jump brakes × 2 hedge widths × 2 holds × 2 stop ratios × 2 directions × 2 expiry types = 288 cells per expiry shard.

Positive skew sells a put vertical: short ATM-2 put, long ATM-(2+width) put. Negative skew sells a call vertical: short ATM+2 call, long ATM+(2+width) call.

Entry at next minute; target 50% of entry credit; stop 1.50x or 2.00x credit; hold 30 or 60 minutes; base/stress slippage 0.20/0.40 points per leg.

Motivation: NIFTY options exhibit systematic smile/skew structure across moneyness and expiry, and Indian options research finds skew can contain forward information around information events. citeturn597354search3turn597354search5turn597354search10

Promotion requires at least one untouched walk-forward test window >= ₹1,000/lot/day, positive stress performance, sufficient trades, and no single-window concentration.