# Phase 51 Literature Review

## Volatility risk premium and implied volatility

Carr and Wu develop a framework separating option-implied, expected and realized volatility and report that the resulting volatility-risk-premium information can predict future stock returns. This supports testing volatility state variables rather than treating implied volatility as purely contemporaneous pricing noise.

Source: https://www.sciencedirect.com/science/article/pii/S0304405X16000052

Bollerslev, Gibson and Zhou construct a time-varying volatility-risk-premium measure from option-implied and realized volatility and find significant temporal dependence and predictive information for future stock returns.

Source: https://www.sciencedirect.com/science/article/pii/S0304407610000758

Bernales, Chen and Valenzuela review and model the predictive relationship between volatility risk premium and option returns, providing theoretical support for state-dependent option-return predictability.

Source: https://www.sciencedirect.com/science/article/pii/S0165188917301434

## Index-option implied-volatility dynamics

Mixon studies ATM implied-volatility term structure for several national stock-market indexes and finds predictive information for future short-dated implied volatility, with results consistent with a time-varying volatility risk premium.

Source: https://www.sciencedirect.com/science/article/pii/S0927539806000715

## Indian/NIFTY context

NIFTY-specific public dashboards commonly display ATM IV alongside India VIX, realized volatility and volatility-risk-premium measures, indicating that ATM IV level is a standard observable state variable in the Indian options market. This practitioner context is hypothesis-generation only; it is not used as performance evidence.

Reference example:
https://www.oidata.in/

## Research implication

Phase 51 deliberately isolates **absolute prior-session ATM IV level**. It does not reuse the prior Phase 39/40 implied-vs-realized dislocation construction and does not test skew/smile or term structure. The phase is a finite 12-cell discovery with permutation nulls and the same dual-friction promotion gate.
