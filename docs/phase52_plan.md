# Phase 52 — Same-Session 09:30 ATM IV Level Regime × Opening Direction

## Research question

Does the absolute ATM implied-volatility level observable at 09:30 condition the direction of the opening move strongly enough to generate at least ₹5,000 net per completed trading week after realistic costs?

## Literature rationale

Published volatility-risk-premium research shows that option-implied volatility contains state information with predictive content for subsequent asset and option returns. Index-option IV dynamics and time-varying volatility risk premia therefore motivate testing the level of implied volatility as a regime variable.

Phase 52 is deliberately different from Phase 39 and Phase 40:
- it does not compare IV with realized volatility;
- it does not use an IV/GAP dislocation ratio;
- it does not use skew, smile, term structure, or prior-session IV;
- it uses the absolute 09:30 ATM IV level available immediately before the 09:31 trade.

Sources:
- https://www.sciencedirect.com/science/article/pii/S0304405X16000052
- https://www.sciencedirect.com/science/article/pii/S0304407610000758
- https://www.sciencedirect.com/science/article/pii/S0927539806000715
- https://www.sciencedirect.com/science/article/pii/S0165188917301434

## Frozen feature construction

For current trading date t:
1. Reference spot = NIFTY 09:30 close.
2. ATM strike = nearest ₹50 strike using deterministic half-up rounding.
3. Feature expiry = nearest NIFTY expiry strictly after the current trading date.
4. Obtain 09:30 ATM CE and ATM PE closes.
5. Invert both premiums to Black-Scholes IV using 09:30 spot, ATM strike, and time to the feature expiry.
6. Current ATM IV = simple mean of CE and PE IV in volatility percentage points.
7. State thresholds are computed from the last 60 valid current-session 09:30 ATM-IV observations strictly before the current date:
   - LOW_IV: below empirical 33.333rd percentile
   - MID_IV: 33.333rd to below 66.667th percentile
   - HIGH_IV: at or above 66.667th percentile.
8. Opening direction = sign(NIFTY 09:15 open / previous completed 15:10 close − 1).
9. Zero opening direction = NO_TRADE.

All feature information is available by 09:30; entry remains 09:31.

## Frozen execution

- FOLLOW_OPEN and FADE_OPEN.
- Entry 09:31 IST option open.
- Exits 10:30 and 15:10 IST option close.
- One-lot 200-point ATM directional debit spread.
- Execution expiry = nearest NIFTY expiry on/after current trade date.
- Historical NIFTY lot sizes.
- Existing Paytm Money/NSE/statutory charges.
- Base slippage ₹0.20; Stress ₹0.40 per option-price unit/order.

## Discovery matrix and controls

3 IV states × 2 direction mappings × 2 exits = 12 true cells.

Five fixed state-permutation null seeds: 101/202/303/404/505. Nulls permute only the prior-information IV-regime labels across eligible dates while preserving same-day opening direction and execution prices.

## Data gates

- ≥95% post-warm-up feature eligibility.
- ≥95% current 09:30 ATM IV CE/PE completeness.
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

No post-result changes to the 60-session history length, percentile boundaries, IV inversion, feature expiry rule, direction mapping, execution expiry rule, entry, exits, spread width, or cost model.
