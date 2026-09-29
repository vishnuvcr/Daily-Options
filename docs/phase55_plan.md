# Phase 55 — Same-Session 09:30 IV Smile Curvature / Wing Richness × Opening Direction

## Research question

Does the curvature/richness of the 09:30 NIFTY implied-volatility smile around ATM condition the opening direction strongly enough to generate at least ₹5,000 net per completed trading week after realistic costs?

## Literature rationale

Empirical work finds that features of the implied-volatility smile beyond level and simple slope can contain information about future volatility and returns. Curvature and symmetry improve volatility forecasts in option markets, while the determinants of smile curvature include market uncertainty, time to expiry and transaction costs. Research on the smile also distinguishes level, slope and curvature as separate surface factors.

Sources:
- https://www.sciencedirect.com/science/article/pii/S1544612319302831
- https://www.sciencedirect.com/science/article/pii/S0378426698001344
- https://doi.org/10.1023/A:1009642705121
- https://www.sciencedirect.com/science/article/pii/S1057521914000982

These findings motivate a bounded NIFTY intraday test only; no external profitability result is imported.

## Frozen feature construction

For current trading date t:
1. Reference spot = NIFTY 09:30 close.
2. ATM strike = nearest ₹50 using deterministic half-up rounding.
3. Feature expiry = nearest NIFTY expiry strictly after the current trading date.
4. ATM IV = Black-Scholes IV from the 09:30 ATM CE and ATM PE average.
5. OTM put IV = IV of the 09:30 put at ATM-₹100.
6. OTM call IV = IV of the 09:30 call at ATM+₹100.
7. WING_AVG_IV = (OTM put IV + OTM call IV) / 2.
8. IV_CURVATURE = WING_AVG_IV − ATM_IV.
9. Classify IV_CURVATURE using the last 60 valid curvature observations strictly before the current date:
   - LOW_CURVATURE: below empirical 33.333rd percentile
   - MID_CURVATURE: 33.333rd to below 66.667th percentile
   - HIGH_CURVATURE: at or above 66.667th percentile.
10. Opening direction = sign(current 09:15 open / previous completed 15:10 close − 1).
11. Zero opening direction = NO_TRADE.

All feature information is available by 09:30; entry remains 09:31.

## Frozen execution

- FOLLOW_OPEN and FADE_OPEN.
- Entry 09:31.
- Exits 10:30 and 15:10.
- One-lot 200-point ATM directional debit spread.
- Execution expiry = nearest NIFTY expiry on/after current trade date.
- Historical NIFTY lot sizes.
- Existing Paytm Money/NSE/statutory charges.
- Base slippage ₹0.20; Stress ₹0.40 per option-price unit/order.

## Discovery matrix and controls

3 curvature states × 2 direction mappings × 2 exits = 12 true cells.

Five fixed state-permutation null seeds 101/202/303/404/505. Only curvature-regime labels are permuted across feature-eligible dates; same-day opening direction and execution prices remain unchanged.

## Data gates

- ≥95% post-warm-up feature eligibility.
- ≥95% 09:30 ATM and wing option quote/IV completeness.
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

No WFA/OOS unless at least one frozen true cell clears the complete gate in both frictions.

## Stop rule

No post-result changes to the ±₹100 wing strikes, 60-session history, tercile boundaries, IV inversion, feature expiry, execution expiry, direction mapping, entry, exits, spread width, or cost model.
