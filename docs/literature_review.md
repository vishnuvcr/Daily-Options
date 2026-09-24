# Literature and Data Review

Last updated: 2026-09-24.

## Scope

The research program focuses on reproducible intraday NSE index-options strategies. The review therefore prioritizes (1) Indian index-option microstructure, volatility and price discovery; (2) realistic-friction evidence; (3) high-frequency data availability; and (4) external implementations that can be audited for methodology rather than copied as claims of profitability.

## Core academic and market evidence

### Volatility risk premium

Chakrabarti & Kotha (2017), *Options Order Flow, Volatility Demand and Variance Risk Premium*, reports that vega-weighted NIFTY option order imbalance is associated with changes in variance risk premium and that the sign of VRP changes contains information about realized-volatility innovations. This supports testing order-flow/IV-RV conditioning, but the study uses proprietary historical data and is not a validation of the present sample.

Source: https://ideas.repec.org/a/mfj/journl/v21y2017i2p49-90.html

Pillai (2026), *Trading the Volatility Risk Premium on Nifty 50: Strategy Backtest with Realistic Frictions*, evaluates short-volatility strategies with explicit STT, brokerage and slippage and reports that all four tested strategies had negative net annualized results under its assumptions. This is a useful counterweight to assuming that VRP is automatically monetizable after costs.

Source: https://papers.ssrn.com/sol3/Delivery.cfm/6876580.pdf?abstractid=6876580&mirid=1

John (2026 preprint), *Harvesting the Volatility Risk Premium in Nifty Index Options: Out-of-Sample Evidence and the Post-2024 Regulatory Regime Break*, describes walk-forward OOS testing and explicit transaction-cost models and reports a post-2024 regime change. It is a preprint and is used here as a hypothesis/data-design source, not definitive evidence.

Source: https://www.researchgate.net/publication/411779323_Harvesting_the_Volatility_Risk_Premium_in_Nifty_Index_Options_Out-_of-Sample_Evidence_and_the_Post-2024_Regulatory_Regime_Break

A separate 2026 preprint, *The Variance Risk Premium in Nifty 50: Structural Anatomy Across Nine Empirical Filters*, analyzes more than 43 million one-minute option observations from August 2022 to March 2026 and reports positive VRP on most days but substantial tail asymmetry. This is relevant for regime conditioning and cost-aware short-volatility tests; it remains preprint evidence.

Source: https://papers.ssrn.com/

### Open interest and intraday price discovery

A September 2026 SSRN working paper, *Open Interest Repositioning around Intraday Price-structure Breaks: Evidence from NIFTY 50 Index Options*, finds that PE-minus-CE OI differentials are associated with break direction around intraday structure breaks after multiple-testing correction. Importantly, its explicit real-time predictive OOS signal for January-April 2026 did not hold. The paper therefore supports treating OI as a state/confirmation variable rather than assuming that OI alone is a reliable forward predictor.

Source: https://papers.ssrn.com/sol3/Delivery.cfm/7394780.pdf?abstractid=7394780&mirid=1

A 2026 high-frequency pilot using five-second NIFTY option observations reports no significant very-short-horizon predictive relation from PCR to returns, while returns Granger-cause subsequent PCR at one- and five-minute horizons. The pilot is small and non-contiguous, so it is evidence for caution, not a final rejection of option-flow features.

Source: public working-paper preprint; see repository source manifest.

### Futures versus spot price discovery

A 2022 open-access study of one-minute NIFTY spot and futures finds bidirectional Granger relationships and a larger Hasbrouck information share for futures. This gives a stronger empirical basis for testing derivative-versus-spot lead/lag than assuming that an option-implied or OI signal must lead the underlying.

Source: https://onlinelibrary.wiley.com/doi/10.1111/ajfs.12374

Related high-frequency work on dual-listed Nifty futures (NSE/SGX) and spot uses VECM, information share and component-share methods to study cross-market price discovery.

Source: https://www.emerald.com/insight/publication/issn/1746-8809

### Intraday options and gamma regimes

Recent 0DTE research indicates that option-market-maker gamma exposure can alter intraday volatility and reversal/momentum behavior. These results motivate a future regime filter based on gamma/liquidity conditions, but they do not by themselves establish a profitable NSE strategy.

Sources:
- https://papers.ssrn.com/
- https://knowledge.wharton.upenn.edu/

## Official market, cost and contract references

NSE derivatives reports expose daily market activity, option premium turnover, open interest, participant-wise open interest/trading volume and FII derivatives statistics. These remain candidate context variables for later phases.

Source: https://www.nseindia.com/all-reports-derivatives

NSE contract-information pages provide current derivative contract and lot-size reference material. Current index-option expiry rules must be date-versioned because exchange schedules have changed historically.

Source: https://www.nseindia.com/static/products-services/equity-derivatives-contract-information

NSE's current STT schedule applies 0.15% on option sale value from 2026-04-01; the research cost model therefore keeps the brokerage, statutory and exchange components separately versioned by date.

Source: https://www.nseindia.com/static/charges/transaction-charges-on-trading

Paytm Money announced flat ₹20 brokerage across segments effective 2025-01-15. The repository uses this as the broker baseline while retaining statutory/exchange charges separately.

Source: https://www.paytmmoney.com/blog/flat-rs-20-brokerage-across-all-segments

## Primary intraday datasets and engineering sources

- Zenodo NIFTY spot/futures/options one-minute data, 2017-2020.
  https://zenodo.org/records/10899828
- Hugging Face `artist-23/nifty-options-data`: NIFTY options with OHLC, IV, volume, OI, strike, spot and expiry metadata across 2020-2025.
  https://huggingface.co/datasets/artist-23/nifty-options-data
- Hugging Face `rissin/nse-options-intraday`: one-minute NIFTY/BANKNIFTY/SENSEX options from October 2024 onward.
  https://huggingface.co/datasets/rissin/nse-options-intraday
- Hugging Face `thetrademarkk/india-index-options-1m`: large one-minute NIFTY/BANKNIFTY/SENSEX option and index dataset used by the current Phase 11 execution; coverage is broad but option completeness varies by contract.
  https://huggingface.co/datasets/thetrademarkk/india-index-options-1m
- GitHub `aeron7/nifty-banknifty-intraday-data`: public one-minute NIFTY/BANKNIFTY history with OI, useful for reconciliation and data-quality checks.
  https://github.com/aeron7/nifty-banknifty-intraday-data
- GitHub `rajmaurya0904/bhav`: one-minute index/option/futures engineering sample using broker-style data flows and historical contract selection.
  https://github.com/rajmaurya0904/bhav

## External strategy implementations reviewed

### systematic-options-research

The public `PavanTeja2005/systematic-options-research` repository describes a Jun-2021 to Jul-2026 short-premium research program with explicit costs, slippage stress, anchored walk-forward testing, an untouched Sep-2025 OOS split, and multiple bug-audit corrections. Its published headline portfolio is not directly comparable to the present target because the average holding period is roughly 2.2 trading days and the signal parameters are not public. It is therefore an engineering and validation-process reference, not a promoted trading result.

Source: https://github.com/PavanTeja2005/systematic-options-research

### AI-trader

The public `dhruvYadavjii/AI-trader` repository describes tick-level NIFTY option replay, XGBoost features, microstructure confirmation, and an RL exit layer. Its README reports a very small March-April 2026 evaluation sample (18 trading days) with positive simulated P&L under several risk profiles. This is useful for hypothesis generation around premium-confirmation and microstructure gates, but sample length is inadequate for promotion and the repository's results are not treated as independent validation.

Source: https://github.com/dhruvYadavjii/AI-trader

## Research implications

1. OI should be treated as a conditional state/confirmation variable, not as a stand-alone predictive oracle. This directly affects how Phase 11 is interpreted.
2. Futures-versus-spot price discovery has stronger empirical support than assuming option-OI leadership. Phase 12 therefore remains scientifically distinct and data-gated.
3. VRP and gamma effects appear highly regime-dependent, so any short-volatility or 0DTE-style family must include adverse-cost and regime robustness rather than raw backtest returns.
4. Realistic friction and expiry-aware contract identity are first-order research requirements, not post-processing.
5. External open-source results are useful as engineering leads but cannot substitute for untouched out-of-sample testing on this project's data and cost model.

## Current repository decision

Phase 11 remains the live frontier. Phase 12 is parked until Phase 11 resolves and its futures adapter is corrected to preserve exact expiry metadata and sufficient history. No external result is being promoted into this project merely because it reports high headline returns.
