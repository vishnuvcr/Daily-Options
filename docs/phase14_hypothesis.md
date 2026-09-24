# Phase 14 — Global Cross-Market Opening-Gap Regime

## Research question

Can information that is unambiguously known before the NSE open—global index overnight returns plus the NIFTY opening gap—identify a directional continuation/reversion regime that can be expressed through a cost-aware NIFTY option or debit-spread trade?

## Why this is distinct

Phase 11 used intraday structure + OI confirmation; Phase 12 used futures/spot lead-lag; Phase 13 used late-day realized-volatility acceleration. Phase 14 instead tests a **cross-market opening information barrier**: U.S./Japan daily closes observed before India opens, combined with the NIFTY open-to-prior-close gap.

Recent global-index research finds opening-gap predictability is market-sequence dependent and not universal, which makes the India-specific test falsifiable rather than assuming a global edge. Source: https://doi.org/10.1016/j.bir.2026.100871

## Preregistration

768 fixed simulation cells:

- global signal: S&P 500 only or equal-weight standardized S&P 500 + Nasdaq Composite + Nikkei 225;
- global standardized-return threshold: 0.5 or 1.0;
- NIFTY gap threshold: 0.25%, 0.50%, or 0.75%;
- relation: continuation when global and NIFTY gap agree, or fade when they disagree;
- signal time: 09:20 or 09:30 IST;
- execution: next minute;
- structure: long ATM option or one-step ATM debit spread;
- expiry: next weekly or next monthly;
- hold: 10 or 20 minutes;
- risk profile: stop 30% / target 60%, or stop 50% / target 100%.

No grid expansion or post-result parameter narrowing is allowed.

## Information barrier

For an India trade date D:
- NIFTY prior close and D open determine the gap.
- Global returns are taken from the latest close strictly before D's India session.
- No same-day U.S. close or later Asian information is used.
- Option expiry/strike selection uses only source coverage and information available at the signal time.

## Promotion gate

A family requires:
1. at least one cost-adjusted cell >= ₹1,000/lot/day;
2. positive overall OOS walk-forward behavior;
3. positive under doubled slippage;
4. no single test window carrying the entire result.
