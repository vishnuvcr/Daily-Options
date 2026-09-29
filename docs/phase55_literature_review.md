# Phase 55 Literature Review

A 2020 Finance Research Letters paper finds that traditional smile curvature and symmetry measures improve volatility forecasts in currency options, supporting curvature as a distinct surface characteristic rather than merely a restatement of skew.

Source: https://www.sciencedirect.com/science/article/pii/S1544612319302831

A Journal of Banking & Finance paper studying the Spanish IBEX-35 options market finds that transaction costs, time to expiration, uncertainty and market momentum help explain the curvature of the implied-volatility smile. This supports maintaining an explicit after-cost gate and fixed expiry timing.

Source: https://www.sciencedirect.com/science/article/pii/S0378426698001344

Research on S&P 500 implied-volatility surfaces identifies low-dimensional factors that move the surface, motivating separating curvature from the previously tested level and put-call skew/spread factors.

Source: https://doi.org/10.1023/A:1009642705121

Research on forecasting option smile dynamics finds that smile forecasts can improve with market-volume information and that forecasting quality varies by liquidity, reinforcing the need for execution-coverage and no-WFA-without-discovery gates in this project.

Source: https://www.sciencedirect.com/science/article/pii/S1057521914000982

## Research implication

Phase 55 is a finite test of local smile curvature / wing richness around ATM. It is deliberately distinct from:
- Phase 52 absolute ATM IV level;
- Phase 53 fixed ±₹100 put-call skew;
- Phase 54 ATM PE-minus-CE IV spread.

No threshold or execution parameter is selected after observing results.
