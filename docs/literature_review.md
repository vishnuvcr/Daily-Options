# Literature and Data Review

Last updated: 2026-09-23.

## Core academic evidence

1. Chakrabarti & Kotha (2017), *Options Order Flow, Volatility Demand and Variance Risk Premium*. The study reports that vega-weighted NIFTY option order imbalance is associated with changes in variance risk premium and that the sign of VRP changes contains information about realized-volatility innovations. This motivates order-flow and IV-versus-RV regime features, but the study's proprietary 2015 data are not the same as the present sample.
Source: https://ideas.repec.org/a/mfj/journl/v21y2017i2p49-90.html

2. Pillai (2026), *Trading the Volatility Risk Premium on Nifty 50: Strategy Backtest with Realistic Frictions*. The paper tests four short-volatility strategies over 119 monthly expiry cycles from 2015-2025 and explicitly models STT, brokerage and slippage. Its abstract reports negative net annualized results for all four strategies under its assumptions, with tail risk the main loss driver. This is an important counterweight to simple VRP narratives.
Source: https://papers.ssrn.com/sol3/Delivery.cfm/6876580.pdf?abstractid=6876580&mirid=1

3. John (2026 preprint), *Harvesting the Volatility Risk Premium in Nifty Index Options: Out-of-Sample Evidence and the Post-2024 Regulatory Regime Break*. The preprint describes a delta-hedged, VRP-percentile-conditioned short-volatility strategy evaluated with walk-forward OOS testing and separate transaction-cost models, and reports evidence of a post-2024 regime change. It is a preprint and therefore treated as a hypothesis/data-design source, not as definitive validation.
Source: https://www.researchgate.net/publication/411779323_Harvesting_the_Volatility_Risk_Premium_in_Nifty_Index_Options_Out-_of-Sample_Evidence_and_the_Post-2024_Regulatory_Regime_Break

## Primary market data sources

- NSE derivatives reports expose daily market activity, premium turnover for options, open interest, participant-wise open interest/trading volume and FII derivatives statistics. These are candidate context variables for later phases.
  Source: https://www.nseindia.com/all-reports-derivatives
- NSE contract-information pages provide current contract and market-lot reference files; lot-size history must be date-versioned.
  Source: https://www.nseindia.com/static/products-services/equity-derivatives-contract-information
- NSE option chain provides current option-chain fields including OI, volume, IV and bid/ask; it is useful for live diagnostics but cannot be substituted for historical contract data.
  Source: https://www.nseindia.com/option-chain

## Historical intraday datasets

- Zenodo NIFTY spot/futures/options 1-minute data, 2017-2020, with a large options archive. Source: https://zenodo.org/records/10899828
- Hugging Face `artist-23/nifty-options-data`: about 34M rows, 2020-12-29 through 2025-12-26, including OHLC, IV, volume, OI, strike, spot, expiry type and option type. Source: https://huggingface.co/datasets/artist-23/nifty-options-data
- Hugging Face `rissin/nse-options-intraday`: 1-minute NIFTY/BANKNIFTY/SENSEX intraday options from Oct 2024 onward, plus longer daily history; redistribution follows source-provider terms. Source: https://huggingface.co/datasets/rissin/nse-options-intraday
- GitHub `rajmaurya0904/bhav`: a public one-year NIFTY 1-minute spot/options sample (Jul 2025-Jun 2026) used only as an engineering benchmark in this project. Source: https://github.com/rajmaurya0904/bhav

## Research implication

The evidence base is mixed. It supports testing VRP/order-flow conditioning, but recent realistic-friction work also shows that apparently attractive short-volatility premia can disappear after tail losses and execution costs. That is why this project requires both positive net OOS performance and adverse-cost/robustness stress tests.


## Phase 3H lead-lag literature

4. Ren, Cai, Li, Xiong & Chen (2023), *A Multi-market Comparison of the Intraday Lead–Lag Relations Among Stock Index-Based Spot, Futures and Options*. The study uses one-minute data and reports intraday derivative price leadership over the underlying in the sampled markets, while also documenting reversals under strong index moves. This motivates testing the lead-lag relation directly rather than assuming it is constant.
Source: https://ideas.repec.org/a/kap/compec/v62y2023i1d10.1007_s10614-022-10268-0.html

5. Kang, Lee & Lee (2006), *An Empirical Investigation of the Lead-Lag Relations of Returns and Volatilities among the KOSPI200 Spot, Futures and Options Markets and their Explanations*. The paper reports short-horizon options/futures leadership over spot and examines explanations including transaction-cost effects. It is a different market, so it is used only as methodological motivation.
Source: https://ideas.repec.org/a/sae/emffin/v5y2006i3p235-261.html

6. Sundararajan & Balasubramanian (2023), *Intraday price discovery and volatility transmission between the dual-listed stock index futures and spot markets – new evidence from India*. Using high-frequency Indian Nifty data, the study finds asymmetric price-discovery contributions across derivative and spot venues. It supports testing information transmission empirically rather than treating derivative leadership as universal.
Source: https://www.sciencedirect.com/science/article/pii/S1746880923000554
