# Phase 54 — Same-Session 09:30 Matched-ATM IV Call-Put Spread × Opening Direction

## Research question

Does the matched-strike 09:30 implied-volatility difference between the NIFTY ATM call and ATM put condition the opening direction strongly enough to generate at least ₹5,000 net per completed trading week after realistic costs?

## Literature rationale

Option-implied volatility spreads and skews have been studied as information variables for subsequent returns. A recent Journal of Financial Economics paper shows that implied-volatility spread and skew can contain return information, but also cautions that some apparent predictive content can arise from market-friction channels. Phase 54 tests the matched-ATM spread directly in NIFTY index options rather than importing stock-level results.

Source: https://www.sciencedirect.com/science/article/pii/S0304405X25001618

A broader forecasting literature surveys option-implied information as a source of return prediction, including volatility, skewness and higher moments.

Source: https://www.sciencedirect.com/science/chapter/handbook/abs/pii/B9780444536839000104

## Frozen feature construction

For current trading date t:
1. Reference spot = NIFTY 09:30 close.
2. ATM strike = nearest ₹50 strike using deterministic half-up rounding.
3. Feature expiry = nearest NIFTY expiry strictly after the current trade date.
4. Obtain 09:30 ATM CE and ATM PE closes at the same strike and expiry.
5. Invert both premiums to Black-Scholes IV using 09:30 spot, common ATM strike and time to feature expiry.
6. **IV_SPREAD = ATM CE IV − ATM PE IV**, in volatility percentage points.
7. State thresholds use the last 60 valid same-session IV_SPREAD observations strictly before the current date:
   - LOW_SPREAD: below empirical 33.333rd percentile
   - MID_SPREAD: 33.333rd to below 66.667th percentile
   - HIGH_SPREAD: at or above 66.667th percentile.
8. Opening direction = sign(current 09:15 open / previous completed 15:10 close − 1).
9. Zero opening direction = NO_TRADE.

All feature information is available by 09:30; entry remains 09:31.

## Frozen execution

- FOLLOW_OPEN and FADE_OPEN.
- Entry 09:31 IST option open.
- Exits 10:30 and 15:10 IST option close.
- One-lot 200-point ATM directional debit spread.
- Execution expiry = nearest NIFTY expiry on/after current trading date.
- Historical NIFTY lot sizes.
- Existing Paytm Money/NSE/statutory charges.
- Base slippage ₹0.20; Stress ₹0.40 per option-price unit/order.

## Discovery matrix and controls

3 spread states × 2 direction mappings × 2 exits = 12 true cells.

Five fixed state-permutation null seeds: 101/202/303/404/505. Nulls permute only the prior-information spread-regime labels across eligible dates while preserving same-day opening direction and execution prices.

## Data gates

- ≥95% post-warm-up feature eligibility.
- ≥95% same-session 09:30 ATM CE/PE IV completeness.
- ≥95% feature-expiry mapping.
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

No WFA/OOS unless at least one frozen true cell clears the full gate in both friction regimes.

## Stop rule

No post-result changes to the 60-session history length, spread definition, strike/moneyness, percentile boundaries, IV inversion, feature expiry rule, direction mapping, execution expiry rule, entry, exits, spread width, or cost model.
