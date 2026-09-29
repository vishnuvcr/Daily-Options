# Phase 54 — Same-Session 09:30 Matched ATM IV Call-Put Spread × Opening Direction

## Research question

Does the 09:30 implied-volatility spread between matched ATM put and call options, using the same strike and same strict-next expiry, condition the opening direction strongly enough to produce at least ₹5,000 net per completed trading week after realistic costs?

## Distinction from completed phases

- Phase 52 tested the level of matched ATM IV.
- Phase 53 tested adjacent-strike IV skew (ATM−₹50 put versus ATM+₹50 call) at 09:30.
- Phase 54 tests the matched same-strike ATM put-versus-call IV spread, preserving identical strike and expiry across both options.

## Frozen feature

For trade date t:
1. NIFTY 09:30 close defines the ATM strike.
2. Feature expiry is the nearest NIFTY expiry strictly after the current trading date.
3. Obtain 09:30 ATM CE and ATM PE closes at the same strike and same expiry.
4. Invert both to Black-Scholes IV using 09:30 NIFTY spot, matched strike and feature-expiry time.
5. Feature value = IV_PE minus IV_CE, in percentage points.
6. Classify by the last 60 valid observations strictly before the current date:
   - LOW_SPREAD: below q33
   - MID_SPREAD: q33 to below q67
   - HIGH_SPREAD: at or above q67.
7. Opening direction is sign(09:15 open / previous completed 15:10 close − 1). Zero gap = no trade.

All feature information is available by 09:30; entry is 09:31.

## Frozen execution

- FOLLOW_OPEN and FADE_OPEN.
- 09:31 option-open entry.
- 10:30 and 15:10 option-close exits.
- One-lot 200-point ATM directional debit spread.
- Execution expiry: nearest NIFTY expiry on/after trade date.
- Historical NIFTY lot sizes.
- Existing Paytm Money/NSE/statutory costs.
- Base slippage ₹0.20; Stress ₹0.40 per option-price unit/order.

## Discovery matrix and nulls

3 spread states × 2 mappings × 2 exits = 12 true cells.
Five fixed state-permutation nulls: seeds 101, 202, 303, 404, 505.

## Data gates

- ≥95% post-warm-up feature eligibility.
- ≥95% matched ATM CE/PE IV completeness.
- ≥95% feature-expiry mapping.
- Zero prior-information violations.
- ≥95% execution coverage in every true cell.
- Base/Stress accounting reconciliation.

## Promotion gate

In both Base and Stress:
- mean weekly net ≥₹5,000;
- median weekly net ≥₹5,000;
- positive-week rate ≥70%;
- execution coverage ≥95%;
- clean accounting.

No WFA/OOS otherwise.

## Stop rule

No post-result changes to IV spread definition, moneyness, 60-observation history, percentile boundaries, expiry rules, direction mapping, entry/exit, spread width, or costs.
