# Phase 34 — Literature Review and Evidence Map

## 1. Volatility term structure is an economically distinct option-surface dimension

Volatility term structure describes implied volatility across expiries at fixed moneyness. It complements strike-based skew/smile analysis by changing the maturity dimension rather than the strike dimension. This distinction is central to Phase 34 because Phase 32 already tested a single-expiry strike-shape hypothesis.

Li & Zakamulin (2020) study the term structure of volatility predictability and show that volatility predictability varies with horizon rather than being a single-maturity phenomenon. This provides a general empirical motivation for treating maturity structure as information rather than merely a pricing convention.

Source: https://doi.org/10.1016/j.ijforecast.2019.08.010

## 2. Variance-risk pricing varies with maturity

Andries, Eisenbach, Kahn & Schmalz study the term structure of the price of variance risk and report maturity-dependent variance-risk compensation. The work finds that the variance-risk term structure changes through time and steepens under stress, motivating a test that conditions on front-versus-back option-implied volatility rather than only ATM IV level.

Source: https://www.newyorkfed.org/research/staff_reports/sr736.html
Revised version: https://doi.org/10.1093/rof/rfaf029

## 3. Forward variance information from option portfolios

Bollerslev et al. (2011) construct forward variances from option portfolios across maturities and find predictive relationships with economic and financial variables. Although their setting is broader and not an intraday NIFTY trading study, it supports the idea that cross-maturity option prices contain information beyond a single maturity.

Source: https://doi.org/10.1016/j.jfineco.2011.01.002

## 4. Term spreads in implied volatility and variance risk premium

Guo, Ruan, Gehricke & Zhang (2023) study term spreads in the implied-volatility smirk and their relation to variance-risk-premium measures. They report significant predictive content of the term-spread level factor for variance-risk-premium proxies, with effects visible both in-sample and out-of-sample in S&P 500 data.

Source: https://doi.org/10.1002/fut.22409

This is evidence supporting a measurable maturity-spread hypothesis, not evidence that the same signal is profitable in NIFTY.

## 5. Volatility-surface construction remains a major measurement issue

Ulrich & Walther (2020) show that option-implied variance, skewness and variance-risk-premium estimates can change materially with the volatility-surface construction method. Phase 34 therefore deliberately uses a simple local, fixed-strike, directly observed IV construction and refuses post-result surface-model selection.

Source: https://link.springer.com/article/10.1007/s11147-020-09166-0

## 6. Calendar spreads are economically tied to maturity structure

Calendar spreads directly trade the relative value of different expiries. The calendar-spread literature shows that maturity, strike and volatility dynamics can matter separately from the outright level of volatility.

Hou (2018) examines VIX futures calendar spreads and reports that speculative trading rather than changes in volatility-term-structure information can be a major component of calendar-spread activity. The implication for Phase 34 is methodological: an observed term-structure signal must be tested net of execution costs rather than assumed to represent arbitrage.

Source: https://doi.org/10.1002/fut.21886

## 7. Recent NIFTY-specific calendar evidence

A March 2026 paper titled *The Vega Paradox in Double Calendar Spreads: Evidence from Nifty 50 Weekly Options and the Volatility Term Structure* directly studies double-calendar spreads in NIFTY 50 weekly options. The work reports a stress-regime departure from the conventional expectation that calendars always benefit from rising implied volatility and describes a "Vega Disconnect" between weekly and monthly volatility.

This is highly relevant contextual evidence, but the source currently appears as a ResearchGate author-uploaded paper rather than an established peer-reviewed journal publication. It should therefore be treated as preliminary evidence, not as a validated trading rule.

Source: https://www.researchgate.net/publication/402165746_The_Vega_Paradox_in_Double_Calendar_Spreads_Evidence_from_Nifty_50_Weekly_Options_and_the_Volatility_Term_Structure

## 8. India exchange mechanics

NSE publishes official derivatives specifications and option-chain fields including strike, expiry, option type, implied volatility and open interest. NSE Clearing also documents calendar-spread margin treatment for index derivatives. Phase 34 uses the project's historical option cache for numerical testing but retains historical NIFTY lot sizes and the audited brokerage/statutory cost model.

Official references:
- NSE NIFTY derivatives: https://www.nseindia.com/static/products-services/equity-derivatives-nifty50
- NSE option chain: https://www.nseindia.com/option-chain
- NSE Clearing SPAN/calendar-spread parameters: https://www.nseindia.com/static/products-services/equity-derivatives-span-risk-parameter-files

## 9. Research gap

The literature supports the existence of maturity-dependent volatility and variance-risk information, but it does not establish that a simple two-expiry NIFTY term-spread extreme can be monetized at intraday frequency after brokerage, statutory charges and slippage.

Phase 34 therefore asks a narrower question:
- Does an unusually rich near-term NIFTY IV structure mean-revert over the next trading session?
- Can that reversion be captured with a fixed debit double-calendar?
- Does the effect survive realistic Indian trading costs and five full-panel null permutations?

## 10. Preregistration implications

The literature is not permitted to change:
- the two expiry selection rule;
- the ATM/±100 strike definitions;
- thresholds 0.75/1.25;
- exits 10:30/15:10;
- the long-back/short-front calendar direction;
- the debit-only admissibility rule;
- the Base/Stress slippage;
- the ₹5,000/week economic promotion gate.

All numerical choices are frozen in `docs/phase34_plan.md`.
