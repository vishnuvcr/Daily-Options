# Phase 56 — Same-Session 09:30 ATM IV Term-Structure Slope × Opening Direction

## Research question

Does the current-session 09:30 ATM implied-volatility term structure, measured as near-expiry ATM IV minus second-nearest-expiry ATM IV, condition the opening direction strongly enough to generate at least ₹5,000 net per completed trading week after realistic costs?

## Frozen feature construction

For current date t:
1. Obtain the first two NIFTY expiries strictly after the current trade date.
2. Reference spot = NIFTY 09:30 close.
3. ATM strike = nearest ₹50.
4. For each of the two expiries, obtain same-strike 09:30 CE and PE closes and invert to Black-Scholes IV.
5. Expiry-level ATM IV = (CE IV + PE IV)/2.
6. **TERM_SLOPE = FRONT_EXPIRY_ATM_IV − SECOND_EXPIRY_ATM_IV**, in volatility percentage points.
7. Standardize using the last 60 valid same-session TERM_SLOPE observations strictly before current date.
8. State:
   - LOW_TERM_SLOPE: below empirical 33.333rd percentile
   - MID_TERM_SLOPE: 33.333rd to below 66.667th percentile
   - HIGH_TERM_SLOPE: at or above 66.667th percentile.
9. Opening direction = sign(09:15 open / prior 15:10 close − 1); zero = no trade.

The feature is current-session and is deliberately distinct from Phase 51's prior-session term-structure coverage test and Phase 52–55 same-expiry smile/state features.

## Literature rationale

Research on equity-index option term structures finds that the slope of ATM implied volatility across maturities has some predictive content for future short-dated implied volatility, while risk premia can materially affect interpretation. citeturn528249search1

Indian NIFTY research has directly studied the term structure of implied volatility and reports mean reversion plus deviations from rational-expectations behavior in long-dated versus short-dated options. citeturn528249search0turn528249search4

Current Indian empirical work also documents that NIFTY implied volatility varies systematically across maturity and moneyness, making term structure a distinct dimension from smile/skew shape. citeturn528249search2turn528249search10

These sources motivate the test but do not establish profitability after the project's transaction-cost and execution assumptions.

## Frozen execution

- FOLLOW_OPEN and FADE_OPEN.
- 09:31 option-open entry.
- 10:30 and 15:10 exits.
- One-lot 200-point ATM directional debit spread.
- Execution expiry = nearest NIFTY expiry on/after current date.
- Historical NIFTY lot sizes.
- Existing Paytm Money/NSE/statutory charges.
- Base slippage ₹0.20, Stress ₹0.40 per option-price unit/order.

## Discovery matrix and nulls

3 term-slope states × 2 direction mappings × 2 exits = 12 true cells.

Five fixed state-permutation null seeds 101/202/303/404/505. Only the prior-information term-slope states are permuted across eligible dates; same-day opening direction and execution prices remain unchanged.

## Data gates

- ≥95% post-warm-up feature eligibility.
- ≥95% front-expiry ATM IV completeness.
- ≥95% second-expiry ATM IV completeness.
- ≥95% two-expiry feature mapping.
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

No WFA/OOS unless at least one frozen cell clears the full gate in both friction regimes.

## Stop rule

No post-result changes to expiry selection, term-slope definition, lookback, percentile boundaries, direction mapping, entry, exits, spread width or cost model.
