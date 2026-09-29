# Phase 55 — Same-Session 09:30 Front-vs-Next-Expiry ATM IV Term Structure × Opening Direction

## Research question

Does the current-session 09:30 ATM IV term slope between the nearest and next later NIFTY expiries condition opening-gap continuation/reversal strongly enough to generate at least ₹5,000 net per completed trading week after realistic costs?

## Distinction

Phase 34 explored prior-session multi-expiry term structure but was DATA-LIMITED. Phase 55 uses the current-session 09:30 information barrier, so the feature is observable before the 09:31 execution and tests a distinct timing hypothesis without tuning the old Phase-34 thresholds.

## Frozen feature

For trade date t:
1. 09:30 NIFTY close defines ATM using deterministic nearest-₹50 rounding.
2. Front expiry = nearest listed NIFTY expiry **on or after** t.
3. Back expiry = next listed NIFTY expiry strictly after the front expiry.
4. At 09:30, obtain ATM CE and PE closes for both expiries.
5. Invert each to Black-Scholes IV using the common 09:30 spot/ATM strike and expiry-specific time to expiry.
6. ATM IV for each expiry = mean(valid CE IV, PE IV).
7. TERM_SLOPE = BACK_ATM_IV − FRONT_ATM_IV, percentage points.
8. STEEP_TERM when TERM_SLOPE >= 0; INVERTED_TERM when TERM_SLOPE < 0.
9. Opening direction = sign(09:15 open / previous completed 15:10 close − 1); zero gap = no trade.

All signal information is known by 09:30.

## Frozen execution

- FOLLOW_OPEN / FADE_OPEN.
- Entry 09:31 IST option open.
- Exits 10:30 and 15:10 IST option close.
- One-lot 200-point ATM directional debit spread.
- Execution expiry = nearest NIFTY expiry on/after current trade date.
- Historical NIFTY lot sizes.
- Existing Paytm Money/NSE/statutory costs.
- Base slippage ₹0.20; Stress ₹0.40 per option-price unit/order.

## Discovery matrix and nulls

2 term states × 2 mappings × 2 exits = 8 true cells.
Five fixed state-permutation null seeds: 101, 202, 303, 404, 505.

## Data gates

- ≥95% post-warm-up feature eligibility.
- ≥95% front/back ATM CE/PE IV completeness.
- ≥95% front/back expiry mapping.
- Zero prior-information violations.
- ≥95% execution coverage in every true cell.
- Full Base/Stress accounting reconciliation.

## Promotion gate

Both Base and Stress:
- mean weekly net ≥₹5,000;
- median weekly net ≥₹5,000;
- positive-week rate ≥70%;
- execution coverage ≥95%;
- clean accounting.

No WFA/OOS unless at least one frozen cell clears all criteria in both frictions.

## Stop rule

No post-result change to expiry selection, sign boundary, IV inversion, entry/exit, mapping, spread width or cost model.
