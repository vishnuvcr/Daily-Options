# Phase 54 Literature Review

## Implied-volatility spread

Muravyev, Pearson and Pollet (2025) analyze why options-market information can predict stock returns and report that implied-volatility spread and skew can contain return information, while also finding that part of the predictability can reflect stock-borrow fees. This motivates a direct test of the spread but also argues against assuming that a positive relation automatically transfers to index options.

Source: https://www.sciencedirect.com/science/article/pii/S0304405X25001618

A Handbook of Economic Forecasting chapter surveys predictive information extracted from option prices, including implied volatility and higher moments, and discusses risk-premium adjustments.

Source: https://www.sciencedirect.com/science/chapter/handbook/abs/pii/B9780444536839000104

## Relation to previous phases

Phase 52 tested the **level** of matched ATM IV using the CE/PE average.
Phase 53 tested **cross-strike adjacent skew**: OTM put IV at ATM−₹50 minus OTM call IV at ATM+₹50.
Phase 54 instead tests the **matched ATM call-minus-put IV spread** at the same strike and expiry.

The three features are intentionally distinct.

## Research implication

There is literature support for testing implied-volatility spreads as information variables, but not for assuming a profitable 09:31 NIFTY directional debit-spread strategy after realistic Indian option costs. Phase 54 therefore uses the same finite tercile/null/dual-friction discovery protocol and will close negative if no frozen cell clears the gate.
