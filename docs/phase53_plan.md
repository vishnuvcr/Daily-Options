# Phase 53 — Same-Session 09:30 ATM-Adjacent IV Skew × Opening Direction

## Research question

Does the cross-strike shape of the NIFTY option-implied volatility surface at 09:30—measured as 1-strike OTM put IV minus 1-strike OTM call IV—condition the opening direction strongly enough to produce at least ₹5,000 net per completed trading week after realistic costs?

## Literature rationale

Research using option-implied skewness finds that skew-related variables can contain information about subsequent returns and investor sentiment. The literature does not establish that such information survives short-horizon Indian index-option transaction costs, which is why this phase uses a finite preregistered grid and a strict after-cost promotion gate.

- A 2025 study reports option-implied skewness as a predictor of market excess returns in- and out-of-sample at longer horizons. https://www.sciencedirect.com/science/article/abs/pii/S0927539825000647
- A 2025 Journal of Financial Economics paper finds that implied-volatility spreads and skew can contain return information, while emphasizing that interpretation can depend on borrow-fee and market-friction channels. https://www.sciencedirect.com/science/article/pii/S0304405X25001618
- A 2014 study reports predictive information in IV skew and connects larger OTM-put relative IV to lower subsequent equity returns in its sample. https://www.sciencedirect.com/science/article/abs/pii/S0378426614003616
- A 2021 study finds the relationship between implied skewness and option returns depends on hedging error, holding period and moneyness, reinforcing the need to test the exact implementation rather than import published returns. https://www.sciencedirect.com/science/article/abs/pii/S1042443121001244
- A 2015 study of high-frequency equity-index options documents that implied-volatility measures vary materially with moneyness, motivating a cross-strike rather than level-only feature. https://www.sciencedirect.com/science/article/pii/S0304407615000627

## Frozen feature construction

For current trading date t:
1. Reference spot = NIFTY 09:30 close.
2. ATM strike = nearest ₹50 strike using deterministic half-up rounding.
3. Feature expiry = nearest NIFTY expiry strictly after the current trade date.
4. OTM-put strike = ATM − ₹50.
5. OTM-call strike = ATM + ₹50.
6. Obtain 09:30 OTM-put and OTM-call closes.
7. Invert each premium to Black-Scholes IV using 09:30 spot, its strike and time to the feature expiry.
8. **SKEW = OTM-put IV − OTM-call IV**, in volatility percentage points.
9. State thresholds use the last 60 valid same-session SKEW observations strictly before the current date:
   - LOW_SKEW: below empirical 33.333rd percentile
   - MID_SKEW: 33.333rd to below 66.667th percentile
   - HIGH_SKEW: at or above 66.667th percentile.
10. Opening direction = sign(current 09:15 open / previous completed 15:10 close − 1).
11. Zero opening direction = NO_TRADE.

All feature information is available by 09:30; entry remains 09:31.

## Frozen execution

- FOLLOW_OPEN and FADE_OPEN.
- Entry 09:31 IST option open.
- Exits 10:30 and 15:10 IST option close.
- One-lot 200-point ATM directional debit spread.
- Execution expiry = nearest NIFTY expiry on/after the current trading date.
- Historical NIFTY lot sizes.
- Existing Paytm Money/NSE/statutory charges.
- Base slippage ₹0.20; Stress ₹0.40 per option-price unit/order.

## Discovery matrix and controls

3 skew states × 2 direction mappings × 2 exits = 12 true cells.

Five fixed state-permutation null seeds: 101/202/303/404/505. Nulls permute only the prior-information skew-regime labels across eligible dates while preserving same-day opening direction and execution prices.

## Data gates

- ≥95% post-warm-up feature eligibility.
- ≥95% same-session 09:30 OTM-put/OTM-call IV completeness.
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

No post-result changes to the 60-session history length, skew definition, moneyness, percentile boundaries, IV inversion, feature expiry rule, direction mapping, execution expiry rule, entry, exits, spread width, or cost model.
