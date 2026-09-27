# Phase 33 — Literature Review

## Scope
This review covers the economic mechanism behind option gamma exposure, dealer hedging, intraday momentum/volatility, and the measurement problem created by unknown option inventory ownership.

### 1. Gamma hedging and intraday price dynamics
A key empirical result is that hedging demand associated with short gamma can generate trades in the direction of price movements, producing intraday momentum. The Journal of Financial Economics paper **Hedging demand and market intraday momentum** studies more than 60 futures markets over 1974–2020 and links the final-30-minute return to earlier intraday returns through gamma-hedging demand. This supports testing a time-aligned gamma regime rather than treating GEX as a generic sentiment score. [Web source](https://www.sciencedirect.com/science/article/pii/S0304405X21001598)

### 2. Net gamma exposure and returns
Soebhag (2023), *Option gamma and stock returns*, reports that net gamma exposure predicts subsequent equity returns in the cross-section and argues that the mechanism is consistent with hedge rebalancing rather than private information. The paper uses gamma-weighted open interest, making it directly relevant to the measurement design used here, while its cross-sectional stock setting means the result cannot be assumed to hold for NIFTY intraday trading. [Web source](https://doi.org/10.1016/j.jempfin.2023.101442)

### 3. Measurement/sign problem
Recent 2026 methodological work emphasizes that the sign of aggregate dealer GEX is not implied by Black-Scholes gamma: gamma itself is positive for both calls and puts. The call/put sign is an inventory-position assumption. This is a central methodological risk for NIFTY, where customer/dealer ownership is not directly observable from public OI. Phase 33 therefore freezes one explicit conventional sign proxy before computation and records the sign-reversed diagnostic without allowing post-result switching. [Chilingarian, 2026](https://ssrn.com/abstract=7131778)

### 4. India-specific relevance
NSE's official NIFTY derivatives specification identifies OPTIDX contracts, CE/PE option types, expiry dates and strike structure. The exchange's option-chain interface exposes OI, change in OI, volume, IV and LTP by strike, confirming that the raw ingredients needed for a gamma/OI proxy are observable in the Indian market. The phase uses the project's pinned historical cache rather than current live-chain values. [NSE contract specifications](https://www.nseindia.com/static/products-services/equity-derivatives-nifty50) [NSE option chain](https://www.nseindia.com/option-chain)

### 5. Gamma concentration and regime boundaries
Public practitioner implementations commonly aggregate gamma-weighted OI by strike and use zero-GEX or gamma-flip levels to distinguish dampening versus amplifying regimes. These are useful as hypotheses but are not treated as established causal facts. The sign ambiguity and the dependence on the chosen inventory proxy are retained as explicit limitations. [NIFTY GEX practitioner example](https://stockmojo.in/gamma-exposure)

### 6. Recent regime-specific evidence
A 2026 SSRN study reports that dealer gamma exposure contained incremental information for overnight gap magnitude primarily in low-VIX regimes in an S&P 500 sample, while the effect weakened in stressed regimes. This motivates recording volatility-regime breakdowns in Phase 33, but the finding is not imported as a NIFTY trading rule. [Maurer, 2026](https://papers.ssrn.com/sol3/Delivery.cfm/6650858.pdf?abstractid=6650858)

### 7. Countervailing evidence and caution
Systematic option-writing studies using 1-minute data show that hedging frequency, transaction costs and model choice materially affect results. This reinforces the project's requirement for explicit execution costs and stress friction rather than relying on pre-cost gamma-regime performance. [Wysocki & Ślepaczuk, 2025](https://doi.org/10.1016/j.econmod.2025.107234)

## Research gap
The relevant literature supports a plausible mechanism but does not establish that a simple public-OI GEX proxy can generate a robust, cost-adjusted NIFTY intraday trading strategy. In particular, public OI does not identify which side of the customer/dealer transaction holds each option. Phase 33 therefore tests the mechanism as a bounded empirical hypothesis rather than assuming that the conventional dealer-sign mapping is true.

## Methodological implications
1. Signal timing must use prior-session information only.
2. The GEX sign convention must be explicit and frozen.
3. Gamma magnitude, gamma-flip distance and ATM concentration should be separated.
4. Null permutations are required to distinguish a real timing effect from generic conditioning.
5. Base and Stress costs are essential because the proposed strategy uses multi-leg option execution.
6. The result should not be generalized from U.S. index literature to NIFTY without direct validation.

## Sources
- Soebhag, A. (2023), *Option gamma and stock returns*, Journal of Empirical Finance 74, 101442. DOI 10.1016/j.jempfin.2023.101442.
- Da et al. (2021), *Hedging demand and market intraday momentum*, Journal of Financial Economics 142(1), 377–403. DOI 10.1016/j.jfineco.2021.04.029.
- Chilingarian, A. (2026), *The Sign of Dealer Gamma: A Reproducible, Auditable Framework for Computing S&P 500 Gamma Exposure (GEX)*, SSRN 7131778.
- Maurer, M. (2026), *Dealer Gamma Exposure and Overnight Gap Risk: Incremental Information in Low-Volatility Regimes*, SSRN.
- Wysocki, M. & Ślepaczuk, R. (2025), *Systematic index option-writing strategies with Black-Scholes-Merton and Variance-Gamma Models*, Economic Modelling 152, 107234.
- NSE India, NIFTY 50 F&O and option-chain documentation.
