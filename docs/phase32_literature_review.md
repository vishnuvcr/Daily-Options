# Phase 32 — Literature & Evidence Review

## 1. Why an option-surface hypothesis is testable

NSE's option chain exposes strike-level option prices, open interest, volume, bid/ask and implied volatility for equity-derivatives contracts. NSE also maintains historical derivatives reports and contract-wise price/volume archives. This makes option-surface state a directly observable market object rather than a proxy reconstructed only from underlying returns.

Primary references:
- NSE Option Chain: https://www.nseindia.com/option-chain
- NSE All Reports / derivatives archives: https://www.nseindia.com/all-reports-derivatives
- NSE Historical Reports: https://www.nseindia.com/static/resources/historical-reports-capital-market-daily-monthly-archives
- NSE Contract Information / permitted lot-size files: https://www.nseindia.com/static/products-services/equity-derivatives-contract-information

## 2. Skew and smile are economically meaningful state variables

Cboe describes volatility skew as the relationship between implied volatilities of out-of-the-money options at comparable maturities; for equity indices, OTM puts commonly carry higher implied volatility than equidistant OTM calls. This is consistent with interpreting a put-call IV difference as a market-priced asymmetry measure rather than a purely technical indicator.

Reference:
- Cboe discussion of SKEW and volatility skew: https://www.cboe.com/insights/posts/inside-volatility-trading-the-adventures-of-volatility-markets

The Phase 32 implementation uses the same economic idea but does not import the Cboe SKEW formula. It uses directly observed NIFTY option prices and a finite, strike-local IV construction.

## 3. Research on option-implied skewness / option returns

Jha & Kalimipalli (2010) study conditional skewness in index option markets and report that skewness-based option trades can improve pricing/trading performance, while also finding that trading costs materially weaken profitability.

Reference:
- Jha, R. & Kalimipalli, M. (2010), The economic significance of conditional skewness in index option markets, Journal of Futures Markets. https://doi.org/10.1002/fut.20414

A 2021 study of option-implied skewness and delta-/vega-hedged option returns finds a negative relation for call samples and emphasizes that hedging error, holding period and moneyness matter.

Reference:
- The effect of option-implied skewness on delta- and vega-hedged option returns (2021). https://doi.org/10.1016/j.intfin.2021.101408

Kim & Park (2018) report that option-implied skewness can have return-predictive content that depends on market state. This supports conditioning interpretation on a frozen, explicit surface signal rather than assuming a universal sign.

Reference:
- Kim, T.S. & Park, H. (2018), Is stock return predictability of option-implied skewness affected by the market state? https://doi.org/10.1002/fut.21921

A 2025 JFE article revisits implied-volatility spread/skew predictability and argues that part of the apparent predictability can proxy stock-borrow fees; the broader lesson is that apparent option-surface signals may be difficult to monetize once real frictions are included.

Reference:
- Why does options market information predict stock returns? (2025). https://doi.org/10.1016/j.jfineco.2025.104153

## 4. Volatility-surface construction can itself create measurement error

Ulrich & Walther (2020) show that forward-looking variance, skewness and variance-risk-premium estimates can be sensitive to the way a volatility surface is constructed, with economically meaningful differences across surface estimators.

Reference:
- Ulrich, M. & Walther, S. (2020), Option-implied information: What's the vol surface got to do with it? https://doi.org/10.1007/s11147-020-09166-0

This is directly relevant to Phase 32. The experiment therefore freezes a simple local, strike-based construction and avoids post-result model selection between splines, SABR, SVI and alternative interpolation families.

## 5. India-specific evidence and volatility context

NSE describes India VIX as a NIFTY-option-implied expected-volatility measure derived from the option order book and based on the Cboe methodology with adaptations for NIFTY. India VIX is not a Phase 32 feature; it is documented here only as evidence that the Indian market already embeds information in option-implied risk-neutral pricing.

References:
- NSE India VIX methodology/description: https://www.nseindia.com/static/products-services/indices-indiavix-index
- NSE India VIX white paper: https://nsearchives.nseindia.com/web/sites/default/files/inline-files/white_paper_IndiaVIX.pdf

The project's earlier Phase 31.6 IV–RV family is explicitly kept separate. Phase 32 asks whether the *shape* of the option surface contains a signal even when a simple ATM IV-minus-RV signal did not.

## 6. Data sources and independent corroboration

### Pinned one-minute NIFTY/options cache
The project uses `thetrademarkk/india-index-options-1m`, revision `51ca58c`. The dataset card describes 1-minute OHLCV(+OI) bars for NIFTY, BANKNIFTY and SENSEX, with option files organized by expiry and fields for strike, option type and expiry. The documentation also warns that option coverage is partial for illiquid/far strikes.

Reference:
- Hugging Face dataset card: https://huggingface.co/datasets/thetrademarkk/india-index-options-1m

### Older independent one-minute archive
Zenodo hosts NIFTY spot, futures and options one-minute data from 2017–2020, with per-strike option OHLCV files. It is used only for source triangulation and future robustness extension, not mixed into the current sample without a separate preregistration.

Reference:
- Bhat, A., Nifty spot, futures and options one-minute data from 2017 to 2020, Zenodo (2024): https://zenodo.org/records/10899828

### Public implementation reconnaissance
An open-source NIFTY volatility-analysis repository demonstrates the same broad building blocks — Black-Scholes IV inversion, smile construction, put-call skew/risk-reversal and butterfly-style metrics — but its results are not used as evidence for Phase 32.

Reference:
- https://github.com/anujpanwarma2024/nifty-options-volatility-analysis

## 7. Data-quality implications

The main threats are:
- stale/zero option prices causing invalid IV inversions;
- sparse far-strike coverage;
- model sensitivity from using spot rather than a forward;
- the 09:30 signal-to-09:31 execution boundary;
- historical changes in NIFTY expiry/lot-size conventions;
- missing bid/ask and queue data in OHLC-only archives.

Phase 32 addresses these with deterministic price-validity checks, strict next-expiry selection, exact timestamp barriers, historical lot sizes, fixed slippage and a 95% execution-coverage gate.

## 8. Evidence hierarchy

1. Official NSE pages and methodology for exchange definitions, option-chain fields, contract/lot-size information and historical reports.
2. Pinned dataset revision used by the repository for numerical backtesting.
3. Published peer-reviewed research on option-implied skewness, surface construction and index-option economics.
4. Zenodo and public code as independent data/schema cross-checks only.

## 9. Preregistration implication

No source listed above is allowed to set the Phase 32 threshold, exit, strike offsets, surface definition, or promotion gate after numerical results are observed. Those elements are frozen in `docs/phase32_plan.md`.
