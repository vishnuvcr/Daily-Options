# Phase 3H — Short-Horizon ATM Option Lead-Lag / Derivative Price Discovery

## Rationale

Several high-frequency studies find that index derivatives can exhibit intraday lead-lag relationships with their underlying. A 2023 cross-market study using one-minute data reports price leadership by futures/options over spot in the sampled markets, while older KOSPI200 evidence found options could lead spot and futures over short horizons. Indian NIFTY literature is more mixed for spot-versus-futures price discovery, which makes an explicit option-to-spot test preferable to assuming a universal lead.

This phase asks a narrow question: does a short-horizon ATM option-price pressure signal forecast the next few minutes of NIFTY spot strongly enough to survive realistic option execution costs?

## Pre-registered information feature

For each minute t and expiry class:
- ATM call return over k minutes = log(C_t / C_{t-k}).
- ATM put return over k minutes = log(P_t / P_{t-k}).
- Directional option pressure = ATM-call return - ATM-put return.
- k is 1, 3 or 5 minutes.

All feature inputs are timestamped at or before t. No forward spot or future option information is allowed to construct a signal.

## Signal

- Bullish signal when option pressure >= 1%, 2% or 3%.
- Bearish signal when option pressure <= -1%, -2% or -3%.
- One first signal per trading day per parameter variant.
- Entry is the next executable minute after signal time.
- The forward spot-return diagnostic uses the next 1, 3 and 5 minutes but is never used to construct the signal.

## Trade expression

- Bullish: buy an ATM call and sell a 1-step or 2-step higher call as a defined-risk debit spread.
- Bearish: buy an ATM put and sell a 1-step or 2-step lower put as a defined-risk debit spread.
- Expiry class: WEEK or MONTH.
- Hold limit: 5, 10 or 15 minutes.
- Same 50% initial-debit stop and 175% initial-debit target logic as Phase 3G.
- One lot basis with date-aware NIFTY lot size.

## Pre-registered grid

| Parameter | Values |
|---|---|
| option-pressure lookback | 1, 3, 5 minutes |
| absolute pressure threshold | 1%, 2%, 3% |
| expiry class | WEEK, MONTH |
| spread width | 1, 2 strikes |
| maximum hold | 5, 10, 15 minutes |

Total variants: 108.

No post-hoc threshold expansion, extra filter, or feature addition is permitted within this family.

## Costs and validation

Use the repository cost model, Rs 20/order research brokerage default, applicable NSE statutory components, date-aware lot size, 0.20-point per-leg round-trip slippage, and a 0.40-point stress rerun.

Validation is leakage-safe train -> validation -> 5-day embargo -> untouched test. Parameters are never selected from the test window.

## Promotion gate

The family is promoted only if the bounded grid produces positive net OOS expectancy after costs and at least one untouched test window reaches Rs 1,000/lot/day, while the stress run remains informative. A negative bounded family is retired without grid expansion.

## Literature anchors

- Ren et al. (2023), *A Multi-market Comparison of the Intraday Lead–Lag Relations Among Stock Index-Based Spot, Futures and Options*. One-minute data; reports derivative price leadership over spot in sampled markets.
  https://ideas.repec.org/a/kap/compec/v62y2023i1d10.1007_s10614-022-10268-0.html
- Kang, Lee & Lee (2006), *An Empirical Investigation of the Lead-Lag Relations of Returns and Volatilities among the KOSPI200 Spot, Futures and Options Markets and their Explanations*. Reports short-horizon option/spot lead-lag patterns after accounting for infrequent trading and spread effects.
  https://ideas.repec.org/a/sae/emffin/v5y2006i3p235-261.html
- Sundararajan & Balasubramanian (2023), *Intraday price discovery and volatility transmission between the dual-listed stock index futures and spot markets – new evidence from India*. Shows that Indian Nifty derivative price discovery can be asymmetric across derivative and spot venues, motivating direct lead-lag testing rather than assuming direction.
  https://www.sciencedirect.com/science/article/pii/S1746880923000554
