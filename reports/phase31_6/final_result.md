# Phase 31.6 — IV–RV Defined-Risk Discovery: Final Result

## Decision

**CLOSED — no promotion.**

The preregistered 12-cell Phase 31.6 discovery was completed on authoritative GitHub Actions run **36248538306**. Base and doubled-slippage Stress both passed unit tests, exact-data acquisition, numerical execution, 12-cell validation, persistence, and artifact upload. No cell advances to walk-forward selection or independent later-period OOS.

## Research question

Can a deterministic intraday NIFTY signal based on ATM implied volatility minus 20-session Yang–Zhang realized volatility identify a defined-risk option structure with net weekly performance that survives transaction costs and conservative slippage?

## Frozen methodology

- Study window: 2021-07-01 to 2026-08-31, subject to exact data coverage.
- Signal: completed 09:30 IST NIFTY bar.
- RV: 20-session Yang–Zhang annualized volatility using only sessions strictly before the signal date.
- IV: ATM call+put straddle implied volatility from 09:30 option opens, Black–Scholes, q=0, observed NIFTY spot.
- Entry: 09:31 option open.
- Exit: 15:10 same day.
- ATM strike: nearest ₹50.
- Expiry buckets: nearest and next available expiry on/after trade date.
- Grid: thresholds 2/4/6 vol points × positive-spread short 200-point iron condor / negative-spread long ATM straddle × nearest/next expiry.
- Base slippage: ₹0.20/order.
- Stress slippage: ₹0.40/order.
- Historical lot sizes and the frozen Phase 31.3 transaction/statutory charge model were retained.

NSE's current contract specification confirms NIFTY index-option weekly expiries are Tuesday, with the previous trading day used when Tuesday is a trading holiday. This study uses the actual expiry files in the pinned dataset rather than hard-coded weekday labels.

## Numerical result

| Threshold | Structure | Expiry bucket | Trades | Base total net | Base mean weekly | Base median weekly | Base positive weeks | Stress total net | Stress mean weekly | Stress median weekly | Stress positive weeks |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 | Short condor | 0 | 398 | -101452.61 | -569.96 | -224.31 | 48.31% | -128864.87 | -723.96 | -354.34 | 48.31% |
| 2 | Short condor | 1 | 64 | -13433.75 | -353.52 | -298.22 | 13.16% | -17951.56 | -472.41 | -418.16 | 7.89% |
| 2 | Long straddle | 0 | 442 | -235483.01 | -1559.49 | -818.32 | 33.77% | -257708.72 | -1706.68 | -859.46 | 32.45% |
| 2 | Long straddle | 1 | 380 | -228661.76 | -1621.71 | -1627.17 | 26.95% | -247088.58 | -1752.40 | -1707.13 | 26.24% |
| 4 | Short condor | 0 | 275 | -69332.13 | -415.16 | -37.19 | 49.70% | -87453.22 | -523.67 | -113.19 | 49.70% |
| 4 | Short condor | 1 | 26 | -4064.81 | -270.99 | -317.25 | 20.00% | -5743.99 | -382.93 | -395.52 | 13.33% |
| 4 | Long straddle | 0 | 361 | -232548.48 | -2325.48 | -2291.45 | 30.00% | -251625.71 | -2516.26 | -2370.49 | 28.00% |
| 4 | Long straddle | 1 | 267 | -155497.41 | -1554.97 | -1310.37 | 31.00% | -169450.43 | -1694.50 | -1453.44 | 30.00% |
| 6 | Short condor | 0 | 178 | **-23018.38** | **-166.80** | **50.11** | **50.00%** | **-34324.32** | **-248.73** | **-29.93** | **50.00%** |
| 6 | Short condor | 1 | 15 | -2091.56 | -298.79 | -410.91 | 28.57% | -3011.11 | -430.16 | -570.84 | 14.29% |
| 6 | Long straddle | 0 | 334 | -198445.91 | -2229.73 | -2757.03 | 32.58% | -216426.59 | -2431.76 | -2996.91 | 29.21% |
| 6 | Long straddle | 1 | 230 | -152892.08 | -1864.54 | -1851.13 | 26.83% | -165281.86 | -2015.63 | -1921.09 | 26.83% |

**Promotion gate:** 0/12 Base and 0/12 Stress cells passed mean weekly net ≥ ₹5,000, median weekly net ≥ ₹5,000, and ≥70% positive weeks.

### Best observed cell

The best cell by mean weekly net was the 6-vol-point positive IV–RV **SHORT_CONDOR**, nearest-expiry bucket, 200-point wing.

Base:
- 178 trades.
- Total net: **-₹23,018.38**.
- Mean weekly net: **-₹166.80**.
- Median weekly net: **₹50.11**.
- Positive-week rate: **50.00%**.
- Worst trade: **-₹7,027.41**.
- Worst week: **-₹7,027.41**.
- Slippage: **₹12,725.25**.
- Transaction/statutory costs: **₹37,215.13**.

Stress:
- Total net: **-₹34,324.32**.
- Mean weekly net: **-₹248.73**.
- Median weekly net: **-₹29.93**.
- Positive-week rate: **50.00%**.
- Worst trade: **-₹7,136.12**.
- Worst week: **-₹7,136.12**.
- Slippage: **₹24,034.75**.
- Transaction/statutory costs: **₹37,211.57**.

The best cell's gross result before slippage and transaction/statutory charges is approximately **₹26,922**, so the negative net result is consistent with the frozen accounting identity:
**gross P&L − slippage − transaction/statutory costs = net P&L**.

## Data-quality and coverage observations

The diagnostics show that:
- the first 20 study sessions cannot form a complete 20-session pre-signal RV window and are therefore excluded;
- many next-expiry (bucket 1) days lack a usable 09:30 ATM CE+PE quote in the pinned exact-expiry data;
- a small number of otherwise-qualified signals lack one or more entry/exit option legs and are recorded as MISSING_LEG;
- these are retained as diagnostics rather than silently substituted.

Because the next-expiry bucket has materially lower executable coverage, its negative cells should not be interpreted as a statement about the whole next-expiry NIFTY market. The primary decision is driven by the fully enumerated executable sample actually available under the frozen rule.

## Interpretation

The result rejects this **specific** intraday IV–RV implementation as a viable candidate under the project's ₹5,000/week discovery gate. It does not reject the broader academic hypothesis that option-implied volatility can differ systematically from realized volatility.

Recent literature is mixed. A 2026 Nifty 50 structural study reports positive VRP on many days but also substantial regime dependence and estimator sensitivity; another 2026 study reports that short-volatility strategies can lose money after realistic frictions in Nifty options. These findings support testing the measurement and regime architecture carefully rather than assuming a generic volatility premium is directly monetizable.

## Strengths

- Preregistered finite grid; no post-result parameter expansion.
- Exact Base/Stress friction comparison.
- Historical lot-size schedule.
- One signal per day and deterministic execution timestamps.
- No result-based WFA parameter selection.
- Complete 12-cell output even where a cell has sparse trades.
- Separate diagnostics for missing data/legs.

## Limitations

- IV is solved with Black–Scholes q=0 rather than a dividend-aware or futures-based Black-76 specification.
- The current implementation relies on exact option timestamps and therefore inherits the source's quote-availability limitations.
- The next-expiry bucket is materially more sparse.
- The discovery sample is not a substitute for independent OOS evidence.
- No order-book bid/ask reconstruction is performed; fixed slippage is the declared execution stress model.

## Next research direction

Do not tune this family. The next family should use a **distinct signal/data source**, prioritizing a candidate whose required data fields are actually present in the pinned cache. The Phase 31.4 catalogue identifies OI/volume microstructure as testable-with-nulls and order-book imbalance as data-gated; India VIX/global data are not assumed available when the current cache does not contain them.

## Reproducibility artifacts

- Plan: docs/phase31_6_plan.md
- Engine: research/phase31_6_iv_rv_defined_risk.py
- Tests: tests/test_phase31_6_iv_rv_defined_risk.py
- Base summary: reports/phase31_6/base/cell_summary.csv
- Stress summary: reports/phase31_6/stress/cell_summary.csv
- Base diagnostics: reports/phase31_6/base/diagnostics.csv
- Stress diagnostics: reports/phase31_6/stress/diagnostics.csv

## External evidence

- NSE India, Contract Specifications: https://www.nseindia.com/static/products-services/equity-derivatives-contract-specifications
- NSE India, NIFTY 50 F&O: https://www.nseindia.com/static/products-services/equity-derivatives-nifty50
- Agarwal, Y. (2026), The Variance Risk Premium in Nifty 50: A Structural Anatomy Across Nine Empirical Filters: https://ssrn.com/abstract=6530119
- Pillai, S. (2026), Trading the Volatility Risk Premium on Nifty 50: Strategy Backtest with Realistic Frictions: https://ssrn.com/abstract=6876580
