# Phase 31.8 — Literature Review and Evidence Matrix

## Research question
Whether completed global-market information available before the NIFTY open has enough incremental information to support a defined-risk intraday NIFTY directional spread after transaction costs and slippage.

## Evidence synthesis

### NSE working paper: U.S. to India transmission
The NSE working paper on transmission between NASDAQ Composite and NIFTY reports significant effects of previous-day NASDAQ and NIFTY daytime returns on the following NIFTY overnight return. It also reports a material NASDAQ-to-NIFTY volatility spillover and finds that adding NASDAQ daytime information improves out-of-sample forecasts of the mean level of NIFTY overnight returns, while not materially improving volatility forecasts. This supports testing a strictly lagged global-input hypothesis, but does not establish tradability after option costs. Source: https://nsearchives.nseindia.com/content/research/Paper39.pdf

### NIFTY/world-index linkage literature
Hussain and Atif (2019) study NIFTY with U.S., U.K., China, Hong Kong, Korea and Japan indices using daily data. They report cointegration with some markets and Granger/volatility-spillover relationships, while also finding that some return-direction relationships are absent. This mixed evidence supports testing multiple regional composites rather than assuming a single market universally leads NIFTY. Source: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3452016

Mukherjee and Mishra study information leadership and volatility spillovers among Indian and Asian markets. Their abstract reports that foreign-market return spillovers can affect Indian open-to-close returns materially, while volatility information is also reflected at the Indian open. This is consistent with using only completed foreign sessions available before the NIFTY signal time. Source: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=874916

A 2024 TVP-VAR connectedness study covering NIFTY50, Nikkei225, KOSPI, Hang Seng and NASDAQ reports time-varying cross-market spillovers and stronger interconnectedness in crisis periods. This motivates a global composite rather than a single-index predictor, but again does not imply a profitable option strategy after costs. Source: https://www.sciencedirect.com/org/science/article/pii/S0144358523000470

A 2025 SSRN cross-market NIFTY study evaluates OLS, robust/HSC, GARCH and VAR specifications across major global indices and reports stronger predictive performance when more international markets are incorporated. It is treated as supporting context rather than confirmation because it is a working-paper result and its objective is index forecasting rather than executable, costed option P&L. Source: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5884902

A 2026 S&P 500/NIFTY study reports regime-specific volatility persistence and asymmetric effects using GARCH/GJR-GARCH over 2007–2024. It provides additional motivation to inspect global information under changing volatility conditions, while Phase 31.8 intentionally keeps the preregistered signal grid fixed instead of conditioning on observed results. Source: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7109738

## Methodological implications
1. Use only the latest completed foreign session strictly before the NIFTY trade date.
2. Standardize each global return using only strictly prior observations.
3. Test regional and global composites rather than optimizing individual countries after observing P&L.
4. Keep null permutations and realistic option execution costs.
5. Treat forecastability/spillover evidence as hypothesis support, not as evidence of an executable trading edge.

## Data sources
Primary global acquisition: Yahoo Finance through a pinned yfinance workflow, with files and a manifest persisted in the phase branch.
NIFTY option/index source: the project's pinned TradeMarkk dataset cache.
