# Phase 53 — Same-Session 09:30 ATM IV Skew Regime × Opening Direction

## Research question

Does the asymmetry between 09:30 ATM put and call implied volatility condition the direction of the opening move strongly enough to generate at least ₹5,000 net per completed trading week after realistic costs?

## Literature rationale

Option-implied skewness and IV asymmetry have documented relationships with subsequent asset and option returns, although the economic interpretation and exploitability depend on the exact skew construction and transaction costs.

- Yu, Huang and Zhou (2025) find option-implied skewness has predictive content for aggregate equity returns, including out-of-sample evidence; this is a US-market result and not treated as NIFTY proof. citeturn187834search0turn187834search4
- Jha and Kalimipalli (2010) study conditional skewness in index-option markets and explicitly find that trading costs materially weaken profitability, reinforcing the need for the repository's Base/Stress friction gate. citeturn187834search1
- A 2025 Journal of Financial Economics paper documents predictive information in implied-volatility spreads and skew, but also finds that much of the apparent return predictability is tied to stock-borrow economics and becomes less exploitable after costs; this is a warning against treating skew as a free alpha signal. citeturn187834search2
- Ulrich and Walther (2020) show that skewness and other option-implied quantities are sensitive to volatility-surface construction, motivating a simple, fully specified CE-minus-PE ATM construction rather than an unspecified surface model. citeturn187834search3
- NIFTY-specific research documents persistent implied-volatility smile/skew structure in NSE Nifty options across moneyness and maturity. citeturn187834search10

## Frozen feature construction

For current trading date t:
1. Reference spot = NIFTY 09:30 close.
2. ATM strike = nearest ₹50 strike using deterministic half-up rounding.
3. Feature expiry = nearest NIFTY expiry strictly after the current trading date.
4. Obtain 09:30 ATM CE and ATM PE closes.
5. Invert both premiums to Black-Scholes IV using 09:30 spot, ATM strike, and time to feature expiry.
6. Define **ATM_IV_SKEW = IV_PE − IV_CE**, in volatility percentage points.
7. Compute empirical 33.333rd and 66.667th percentiles from the last 60 valid skew observations strictly before the current date.
8. LOW_SKEW: below q33.
9. MID_SKEW: q33 to below q67.
10. HIGH_SKEW: at or above q67.
11. Opening direction = sign(NIFTY 09:15 open / previous completed 15:10 close − 1). Zero gap = NO_TRADE.

The skew feature is observable by 09:30; entry remains 09:31.

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

Five fixed state-permutation null seeds: 101, 202, 303, 404, 505. Nulls permute only the prior-information skew-regime labels across eligible dates while preserving same-day opening direction and execution prices.

## Data gates

- ≥95% post-warm-up skew feature eligibility.
- ≥95% same-session ATM CE/PE IV completeness.
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

No post-result changes to the skew definition, 60-session history, percentile boundaries, IV inversion, feature expiry, direction mapping, execution expiry, entry, exits, spread width, or cost model.
