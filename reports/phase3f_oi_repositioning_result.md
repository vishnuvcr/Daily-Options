# Phase 3F OI Repositioning Around Breaks — Result

Run: GitHub Actions `35908269271`
Dataset: `artist-23/nifty-options-data`, revision `45e0a04`

## Screen

The screen used fixed daily reference strikes selected around 09:29–09:31 IST, then measured normalized 15-minute call-vs-put OI changes on the same absolute strikes. It paired the OI-repositioning signal with the first prior-15-minute spot high/low break after 09:45 and entered one minute later into a defined-risk debit spread.

The grid contained 216 variants:
- OI repositioning threshold: 5%, 10%, 20%;
- break buffer: 0%, 0.05%, 0.10%;
- same-sign vs inverted OI polarity;
- 1- or 2-strike debit spread;
- 30/60/90-minute hold.

## Result

Zero of 216 variants reached ₹1,000 net per calendar day. More importantly, **zero variants had positive mean all-day net**.

The least-negative raw rank had only 2 trades and is not treated as a meaningful candidate. Among configurations with at least 30 trades, the least-negative result had:
- MONTH expiry;
- 5% OI threshold;
- 0.10% break buffer;
- same-sign polarity;
- 2-strike debit spread;
- 30-minute hold;
- 45 trades;
- mean all-calendar-day net: -₹7.14;
- win rate: 31.11%;
- profit factor: 0.288;
- max drawdown: -₹8,843.64.

Among configurations with at least 75 trades, the least-negative result still had mean all-day net -₹11.20, win rate 23.62%, profit factor 0.608 and max drawdown -₹15,192.02.

## Decision

**FAIL_PRELIMINARY.**

The tested fixed-strike OI-repositioning + intraday-break family is retired from further parameter tuning. The event is also too sparse at the stricter thresholds, so additional threshold refinement would not be a high-value use of the research budget.

Next Phase 3F hypothesis: IV-skew shock and skew-reversion/relative-value structures, which add information not used by the failed OI-price-break family.
