# Phase 55 — Same-Session 09:30 IV Smile Curvature × Opening Direction

## Research question

Does the curvature of the NIFTY 09:30 implied-volatility smile around ATM condition the next opening direction strongly enough to produce at least ₹5,000 net per completed trading week after realistic costs?

## Frozen feature construction

For current date t:
1. Reference spot = NIFTY 09:30 close.
2. ATM strike = nearest ₹50.
3. Feature expiry = nearest NIFTY expiry strictly after current trade date.
4. Compute IV at:
   - ATM put: ATM strike, PE
   - ATM call: ATM strike, CE
   - one-strike OTM put: ATM − ₹50, PE
   - one-strike OTM call: ATM + ₹50, CE
5. Define ATM IV = (ATM CE IV + ATM PE IV)/2.
6. Define adjacent-wing IV = (OTM +₹50 call IV + OTM −₹50 put IV)/2.
7. **SMILE_CURVATURE = adjacent-wing IV − ATM IV**, measured in volatility percentage points.
8. Standardize using the last 60 valid same-session curvature observations strictly before the current date.
9. State:
   - LOW_CURVATURE: below empirical 33.333rd percentile
   - MID_CURVATURE: 33.333rd to below 66.667th percentile
   - HIGH_CURVATURE: at or above 66.667th percentile.
10. Opening direction = sign(09:15 open / prior 15:10 close − 1); zero = no trade.

All state information is observable by 09:30; entry remains 09:31.

## Literature rationale

Research documents information in the shape of the implied-volatility smile. Yan (2011) relates smile slope to jump risk and subsequent stock returns. Zhang and Xiang (2008) provide an industry-standard approach to quantifying volatility-smile shape in index options. Reus et al. (2020) find smile curvature/symmetry measures improve volatility forecasts in currency options. Indian evidence also specifically models the parabolic smile/skew shape and its information content. These sources motivate the feature, not its profitability in NIFTY intraday options.

Sources:
- https://www.sciencedirect.com/science/article/pii/S0304405X1000187X
- https://www.tandfonline.com/doi/abs/10.1080/14697680601173444
- https://ideas.repec.org/a/eee/finlet/v34y2020ics1544612319302831.html
- https://doi.org/10.1057/jdhf.2013.14

## Frozen execution

- FOLLOW_OPEN and FADE_OPEN.
- 09:31 option-open entry.
- 10:30 and 15:10 exits.
- One-lot 200-point ATM directional debit spread.
- Nearest expiry on/after current date for execution.
- Historical NIFTY lot sizes.
- Existing Paytm Money/NSE/statutory cost model.
- Base slippage ₹0.20, Stress ₹0.40 per option-price unit/order.

## Discovery matrix and nulls

3 curvature states × 2 direction mappings × 2 exits = 12 true cells.

Five fixed state-permutation null seeds 101/202/303/404/505. Only the prior-information curvature state labels are permuted across eligible dates; same-day opening direction and all execution prices remain unchanged.

## Data gates

- ≥95% post-warm-up feature eligibility.
- ≥95% 09:30 IV completeness for all four required option legs.
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

No WFA/OOS unless at least one frozen cell clears the complete gate in both friction regimes.

## Stop rule

No post-result changes to curvature definition, strike distances, lookback, percentile boundaries, feature expiry, execution expiry, direction mapping, entry, exits, spread width or cost model.
