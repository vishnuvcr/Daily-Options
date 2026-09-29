# Phase 53 Literature Review

## Option-implied skew as predictive information

Yu, Huang and Zhou (2025) study option-implied idiosyncratic skewness and report predictive content for aggregate stock-market excess returns, including out-of-sample tests. Their horizons are much longer than this intraday experiment, so the paper motivates the existence of information in skew rather than proving an intraday edge.

Source: https://www.sciencedirect.com/science/article/abs/pii/S0927539825000647

Jha and Kalimipalli (2010) examine conditional skewness in index option markets and report that forward-looking skew information can improve option-trading performance, while emphasizing that trading costs materially weaken profitability. That friction warning is directly relevant to this phase.

Source: https://doi.org/10.1002/fut.20414

A 2025 Journal of Financial Economics paper finds implied-volatility spreads and skew predict stock returns in US equities, but shows that much of the apparent predictive content is related to omitted borrow fees and that fee adjustment sharply reduces economic significance. This is a caution against interpreting skew as standalone alpha.

Source: https://doi.org/10.1016/j.jfineco.2025.104153

Ulrich and Walther (2020) show that option-implied variance, skewness and VRP estimates are sensitive to volatility-surface construction, with especially important differences for OTM puts. Phase 53 therefore avoids a flexible surface fit and uses a simple ATM CE/PE IV difference with deterministic Black-Scholes inversion.

Source: https://link.springer.com/article/10.1007/s11147-020-09166-0

## NIFTY-specific skew context

Shaikh and Padhi (2014) document the volatility smile/skew, term structure and moneyness effects in NSE Nifty options, confirming that skew is a persistent characteristic of the Indian index-option surface.

Source: https://www.researchgate.net/publication/265969341_Stylized_patterns_of_implied_volatility_in_India_A_case_study_of_NSE_Nifty_options

## Research implication

The literature supports treating option-implied skew as an information variable while also warning that its apparent predictive value can be model-dependent and friction-sensitive. Phase 53 therefore uses a fixed finite skew-state grid, permutation nulls and the project's unchanged dual-friction economic gate.
