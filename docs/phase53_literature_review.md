# Phase 53 Literature Review

## Option-implied skew as information

Recent research continues to document predictive information in option-implied skewness. Yu, Huang and Zhou (2025) report that option-implied idiosyncratic skewness predicts aggregate stock-market excess returns both in- and out-of-sample, although their horizon is much longer than the intraday horizon tested here.

Source: https://www.sciencedirect.com/science/article/abs/pii/S0927539825000647

Muravyev, Pearson and Pollet (2025) analyze why options-market information can predict stock returns and show that implied-volatility spreads and skew can contain return information, while also showing that some predictability can reflect stock-borrow fees and market frictions. This cautions against treating skew as pure information flow.

Source: https://www.sciencedirect.com/science/article/pii/S0304405X25001618

A study linking options trading information to analyst news uses IV skew as an information proxy and reports a negative relationship between skew and subsequent excess returns in its sample. Its skew construction is based on OTM put versus ATM call IV rather than the exact NIFTY construction used here, so it is motivation only.

Source: https://www.sciencedirect.com/science/article/abs/pii/S0378426614003616

A 2021 study on implied skewness and option returns finds that apparent relationships depend on moneyness, holding period and hedging error. This reinforces the need for a direct, after-cost test of the exact 09:30 NIFTY feature.

Source: https://www.sciencedirect.com/science/article/abs/pii/S1042443121001244

Andersen, Bondarenko, Todorov and Tauchen (2015) document that high-frequency index-option implied-volatility measures vary across moneyness and reflect multiple latent volatility states. This supports using an adjacent-strike cross-sectional measure rather than duplicating Phase 52's ATM-level feature.

Source: https://www.sciencedirect.com/science/article/pii/S0304407615000627

## Research implication

The literature supports skew as a plausible information-bearing option-state variable, but does not establish a profitable short-horizon NIFTY strategy after brokerage, statutory charges, spread and slippage. Phase 53 therefore uses a fixed adjacent-strike definition, finite tercile states, permutation nulls and the project's dual-friction economic gate.
