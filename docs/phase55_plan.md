# Phase 55 — Same-Session 09:30 Front-vs-Next-Expiry ATM IV Term Structure × Opening Direction

## Research question

Does the current-session 09:30 ATM IV slope between the nearest expiry on/after the trading date and the next later listed NIFTY expiry condition opening-gap continuation/reversal strongly enough to generate at least ₹5,000 net per completed trading week after realistic costs?

## Literature rationale

The term structure of index-option implied volatility has documented information about future short-dated implied volatility and future returns, although the predictive power is imperfect and risk premia matter. Mixon (2007) finds that ATM IV slope across maturities has some predictive ability for future short-dated implied volatility and notes the role of volatility risk premia. Wang & Yen (2019) find that implied-volatility term-structure information is significant and complementary to the volatility level for future S&P 500 excess returns. Nifty-specific work documents a stochastic implied-volatility surface across time-to-expiration and moneyness, while Indian-market research on term-structure expectations reports departures from simple rational-expectations behavior.

Sources:
- https://www.sciencedirect.com/science/article/pii/S0927539806000715
- https://onlinelibrary.wiley.com/doi/abs/10.1111/eufm.12166
- https://www.researchgate.net/publication/265969341_Stylized_patterns_of_implied_volatility_in_India_A_case_study_of_NSE_Nifty_options
- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1103428

These sources motivate the hypothesis only. No external profitability result is imported, and transaction costs remain decisive.

## Frozen feature

For trade date t:
- 09:30 NIFTY close defines ATM strike.
- Front expiry = nearest listed NIFTY expiry on/after t.
- Back expiry = next listed expiry strictly after the front expiry.
- For each expiry, invert 09:30 ATM CE and PE closes to IV and average CE/PE IV.
- TERM_SLOPE = back IV − front IV in volatility percentage points.
- STEEP_TERM when TERM_SLOPE >= 0.
- INVERTED_TERM when TERM_SLOPE < 0.
- State information is complete by 09:30; 09:31 is the earliest entry.

## Frozen execution

- FOLLOW_GAP and FADE_GAP.
- Entry 09:31 option open.
- Exits 10:30 and 15:10 option close.
- One-lot 200-point ATM directional debit spread.
- Execution expiry = nearest NIFTY expiry on/after trade date.
- Historical NIFTY lot sizes.
- Existing Paytm Money/NSE/statutory costs.
- Base slippage ₹0.20; Stress ₹0.40 per option-price unit/order.

## Discovery matrix and controls

2 term states × 2 mappings × 2 exits = 8 true cells.

Five fixed state-permutation null seeds 101/202/303/404/505. Only the term-state labels are permuted across feature-eligible dates; same-day gap direction and execution prices remain unchanged.

## Data gates

- ≥95% post-warm-up feature eligibility.
- ≥95% current-session front/back ATM IV completeness.
- ≥95% front/back expiry mapping.
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

No WFA/OOS unless at least one frozen true cell clears the full gate in both frictions.

## Stop rule

No post-result change to the front/back expiry definition, slope sign boundary, IV construction, opening mapping, entry, exits, spread width or cost model.
