# Phase 53 — Same-Session 09:30 Near-ATM IV Skew × Opening Direction

## Research question

Does the 09:30 near-ATM implied-volatility skew, measured as OTM-put IV minus OTM-call IV around the NIFTY ATM strike, condition the direction of the opening move strongly enough to generate at least ₹5,000 net per completed trading week after realistic costs?

## Literature rationale

Option-implied volatility skew and put-call volatility spreads have documented relationships with subsequent asset returns, but published work also shows that apparent profitability can be materially reduced by trading and financing frictions. A 2025 Journal of Financial Economics paper discusses how implied-volatility spread and skew can predict returns but are partly related to omitted borrow fees and that the economic gain is much smaller after relevant frictions. An earlier index-option study finds conditional skewness can contain information useful for option strategies but that trading costs weaken profitability. These findings motivate a strict after-cost, finite NIFTY test rather than importing published signals.

Sources:
- https://doi.org/10.1016/j.jfineco.2025.104153
- https://doi.org/10.1002/fut.20414
- https://eprints.lancs.ac.uk/id/eprint/80351/
- https://doi.org/10.2469/faj.v66.n1.9

## Frozen feature construction

For current trading date t:
1. Reference spot = NIFTY 09:30 close.
2. ATM strike = nearest ₹50 using deterministic half-up rounding.
3. Feature expiry = nearest NIFTY expiry strictly after the current trading date.
4. Put-side skew leg = ₹100 below ATM (one 100-point OTM put).
5. Call-side skew leg = ₹100 above ATM (one 100-point OTM call).
6. Obtain 09:30 close prices for both option legs from the feature expiry.
7. Invert each premium to Black-Scholes IV using 09:30 spot, its strike and time to the feature expiry.
8. SKEW = OTM-put IV − OTM-call IV, in volatility percentage points.
9. Classify SKEW using the last 60 valid SKEW observations strictly before the current date:
   - LOW_SKEW: below empirical 33.333rd percentile
   - MID_SKEW: 33.333rd to below 66.667th percentile
   - HIGH_SKEW: at or above 66.667th percentile.
10. Opening direction = sign(current 09:15 open / previous completed 15:10 close − 1).
11. Zero opening direction = NO_TRADE.

All skew information is available by 09:30; entry remains 09:31.

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

3 skew states × 2 direction mappings × 2 exits = 12 true cells.

Five fixed state-permutation null seeds: 101/202/303/404/505. Only the prior-information skew-regime labels are permuted across feature-eligible dates while preserving same-day opening direction and execution prices.

## Data gates

- ≥95% post-warm-up feature eligibility.
- ≥95% 09:30 OTM-put and OTM-call quote/IV completeness.
- ≥95% feature-expiry mapping.
- Zero prior-information violations.
- ≥95% execution coverage in every true cell.
- Full Base/Stress accounting reconciliation.

## Promotion gate

In both Base and Stress:
- mean weekly net ≥ ₹5,000;
- median weekly net ≥ ₹5,000;
- positive-week rate ≥70%;
- execution coverage ≥95%;
- clean accounting.

No WFA/OOS unless at least one frozen true cell clears the full gate in both friction regimes.

## Stop rule

No post-result changes to the ±₹100 skew legs, 60-session history, percentile boundaries, IV inversion, feature expiry, execution expiry, direction mapping, entry, exits, spread width, or cost model.
