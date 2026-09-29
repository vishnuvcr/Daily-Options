# Phase 54 — Same-Session 09:30 ATM Put–Call IV Spread × Opening Direction

## Research question

Does the contemporaneous 09:30 ATM put-minus-call implied-volatility spread condition the opening direction strongly enough to generate at least ₹5,000 net per completed trading week after realistic costs?

## Literature rationale

Option-implied volatility spread and skew are documented as predictors of subsequent returns, but their apparent economic value can be reduced by frictions. Phase 54 isolates the **ATM put-call IV spread** itself, rather than absolute IV level or fixed OTM skew.

Sources:
- https://doi.org/10.1016/j.jfineco.2025.104153
- https://doi.org/10.2469/faj.v66.n1.9
- https://eprints.lancs.ac.uk/id/eprint/80351/

## Frozen feature construction

For current trading date t:
1. Reference spot = NIFTY 09:30 close.
2. ATM strike = nearest ₹50 using deterministic half-up rounding.
3. Feature expiry = nearest NIFTY expiry strictly after the current trading date.
4. Obtain 09:30 ATM CE and ATM PE closes.
5. Invert both premiums to Black-Scholes IV.
6. ATM_IV_SPREAD = PE IV − CE IV, in volatility percentage points.
7. Classify using the last 60 valid spread observations strictly before the current date:
   - LOW_SPREAD: below empirical 33.333rd percentile
   - MID_SPREAD: 33.333rd to below 66.667th percentile
   - HIGH_SPREAD: at or above 66.667th percentile.
8. Opening direction = sign(current 09:15 open / previous completed 15:10 close − 1).
9. Zero opening direction = NO_TRADE.

The spread is available by 09:30; entry remains 09:31.

## Frozen execution

- FOLLOW_OPEN and FADE_OPEN.
- Entry 09:31.
- Exits 10:30 and 15:10.
- One-lot 200-point ATM directional debit spread.
- Execution expiry = nearest NIFTY expiry on/after current trade date.
- Historical lots.
- Existing Paytm Money/NSE/statutory costs.
- Base ₹0.20 and Stress ₹0.40 slippage per option-price unit/order.

## Discovery matrix and controls

3 spread states × 2 direction mappings × 2 exits = 12 true cells.

Five fixed state-permutation null seeds 101/202/303/404/505. Only spread-regime labels are permuted across eligible dates; same-day opening direction and execution prices are unchanged.

## Data gates

- ≥95% post-warm-up feature eligibility.
- ≥95% 09:30 ATM CE/PE completeness.
- ≥95% feature-expiry mapping.
- Zero prior-information violations.
- ≥95% execution coverage in every true cell.
- Full Base/Stress accounting reconciliation.

## Promotion gate

Both Base and Stress:
- mean weekly net ≥ ₹5,000;
- median weekly net ≥ ₹5,000;
- positive-week rate ≥70%;
- execution coverage ≥95%;
- clean accounting.

No WFA/OOS unless at least one frozen true cell clears the full gate in both frictions.

## Stop rule

No post-result change to the 60-session history, tercile boundaries, IV inversion, spread definition, expiry, direction mapping, entry, exits, spread width, or cost model.
