# Phase 53 Literature Review

## Volatility skew

Index-option implied-volatility skew is widely used as a state description of relative downside/upside tail pricing. Volatility-risk-premium research also documents time variation in option-implied state variables and their relation to future returns.

Sources:
- https://www.sciencedirect.com/science/article/pii/S0304405X16000052
- https://www.sciencedirect.com/science/article/pii/S0304407610000758
- https://www.sciencedirect.com/science/article/pii/S0165188917301434

## Gap context

Post-gap behavior can include both continuation and reversal, and the response depends on information context and event size. Phase 53 does not assume a directional effect; it tests both FOLLOW and FADE under the same fixed execution model.

Source:
https://www.sciencedirect.com/science/article/pii/S1062940820300747

## Distinction from earlier work

Phase 32 tested a broader 09:30 skew/smile-dislocation surface family with multiple surface statistics and extreme z-score thresholds. Phase 53 is a narrower preregistered interaction: a single near-ATM put-minus-call IV measure crossed with current opening-gap direction.

The Phase 53 experiment will be considered a new hypothesis only because the main research ledger explicitly defines it as the next frontier; no parameter is imported from the previous skew/smile experiment.
