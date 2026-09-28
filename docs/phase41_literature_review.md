# Phase 41 — Literature Review

## Gamma exposure and return dynamics
Soebhag (Journal of Empirical Finance, 2023) reports that net gamma exposure negatively predicts future equity returns and argues the relation is consistent with hedge rebalancing rather than private information. This motivates a controlled test of gamma-related conditioning, but the study is cross-sectional equity evidence rather than NIFTY intraday spread evidence.

Barbon & Buraschi's *Gamma Fragility* documents a relation between dealer gamma imbalances, intraday momentum/reversal and liquidity. The mechanism is that delta-hedging under different gamma states can reinforce or dampen price moves.

Hedging-demand research likewise links short-gamma hedging to intraday momentum, while later work documents that option-exposure mechanisms can vary by horizon and market microstructure.

## Why concentration rather than dealer-sign GEX
Public option open interest does not directly identify dealer inventory sign. Recent methodological work explicitly warns that GEX sign is an inventory assumption rather than a property of Black-Scholes gamma itself. Phase 41 therefore uses an **unsigned gamma concentration ratio** based on OI × gamma, avoiding a hidden dealer-position sign assumption. The economic test is then whether the degree of near-ATM concentration conditions opening-gap continuation versus reversal.

## Falsification design
Recent preregistered GEX research in U.S. markets finds that strike-local “gamma wall” effects can be difficult to distinguish from control geometry. Phase 41 therefore uses a finite state grid, explicit data gates, and five fixed permutation nulls, and does not select the concentration threshold after observing results.

## Indian context
Recent Indian-market research on India VIX and NIFTY documents that implied-volatility measures and regime definitions can have predictive value for realized volatility and market dynamics, but those results do not establish that NIFTY gamma concentration yields a profitable intraday option-spread strategy.

## References
1. Soebhag, A. (2023). Option gamma and stock returns. Journal of Empirical Finance, 74, 101442. DOI 10.1016/j.jempfin.2023.101442.
2. Barbon, A., & Buraschi, A. (2021). Gamma Fragility. SSRN 3725454.
3. Hedging demand and market intraday momentum. Journal of Financial Economics, 142(1), 377–403. DOI 10.1016/j.jfineco.2021.04.029.
4. Popovici, R. (2026). Do Gamma-Exposure Walls Exhibit Strike-Local Effects? A Pre-Registered, Control-Matched Test of Strike-Local Dealer-Gamma Effects in SPY. SSRN 7082418.
5. Chilingarian, A. (2026). The Sign of Dealer Gamma: A Reproducible, Auditable Framework for Computing S&P 500 Gamma Exposure. SSRN 7131778.
6. Jangir, J. (2026). A Participation Calibrated Gamma Exposure Methodology for Index Options. SSRN 7295618.
7. Chakrabarti, P., & Kiran Kumar, K. (2020). High-Frequency Return-Implied Volatility Relationship: Empirical Evidence from Nifty and India VIX. Journal of Data Analysis and Information Processing, 54(3), 53–68.
8. Shaikh, I., & Padhi, P. (2014). The forecasting performance of implied volatility index: evidence from India VIX. Empirical Economics, 47, 251–274.

## Source notes
The 2026 SSRN papers are recent preprints and are used as methodological context rather than as proof of tradability. The core empirical question remains the cost-aware NIFTY backtest defined in this phase.