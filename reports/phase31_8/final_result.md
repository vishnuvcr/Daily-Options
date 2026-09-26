# Phase 31.8 — Global Overnight Cross-Market Transmission: Final Result

## Executive conclusion

Phase 31.8 completed successfully through the frozen Base/Stress numerical grid, validation, null controls and execution-coverage checks in authoritative GitHub Actions run **36252922418 (run 9)**.

**Promotion result: 0/12 cells passed the ₹5,000/week economic-and-consistency gate in Base, and 0/12 passed it in Stress. The family is therefore closed without WFA/OOS promotion.**

The best observed true cell was **ASIA_LEAD | z=1.00 | 09:31 → 10:30**:
- Base: **₹14,172.92 total net**, **₹107.37 mean weekly net**, **-₹122.78 median weekly net**, **45.45% positive weeks**.
- Stress: **₹4,901.50 total net**, **₹37.13 mean weekly net**, **-₹211.39 median weekly net**, **45.45% positive weeks**.
- The same true cell beat all five null-control means on mean weekly P&L in both frictions, but remained far below the promotion threshold and had a negative median week.

The strategy family's positive gross return did not translate into an economically sufficient net edge after realistic costs. For the best Base cell, raw gross was **₹47,877.00**, versus **₹9,276.00 slippage + ₹24,428.08 transaction/statutory costs**, leaving ₹14,172.92 net. Under Stress, slippage rose to **₹18,552.00** and net fell to ₹4,901.50.

## Research question

Does information from the most recently completed U.S., European and Asian equity sessions, standardized strictly from prior data, provide an incremental and economically usable signal for intraday NIFTY defined-risk option spreads after slippage and transaction costs?

## Preregistered methodology

The phase used a frozen **12-cell** grid:
- Features: US_LEAD, ASIA_LEAD, GLOBAL_LEAD.
- Thresholds: z-score 0.50 and 1.00.
- Horizons: 10:30 and 15:10 exits.
- Signal generation: only completed foreign sessions strictly before the NIFTY session; 60-observation strictly prior rolling standardization.
- Entry: NIFTY 09:31.
- Structure: deterministic ATM directional debit spread with 200-point wing, nearest eligible expiry, historical lot-size schedule.
- Null controls: 5 full-panel permutation seeds × 12 cells = **60 null summaries per friction regime**.
- Frictions: Base ₹0.20 and Stress ₹0.40 slippage per order plus the frozen Paytm Money/NSE/statutory cost model used by the project.
- No-lookahead barrier: `merge_asof` with exact-date matching disabled; all six global predictors were required to come from strictly earlier dates.

## Data gate and provenance

The global data gate passed:
- Raw NIFTY sessions: **1,228**.
- Feature-eligible sessions after the mandatory 60-observation warm-up: **1,164**.
- Warm-up exclusions: **64**.
- Complete six-market feature coverage among eligible sessions: **100%**.
- Prior-date barrier violations: **0**.
- Study window: **2021-07-01 through 2026-08-31**.
- Global source: Yahoo Finance via pinned **yfinance 1.7.0** cache.
- Six indices: S&P 500, NASDAQ Composite, Nikkei 225, Hang Seng, DAX and KOSPI.

## True-cell results

| Feature | z | Exit | Base total | Base mean/wk | Base median/wk | Base +weeks | Stress total | Stress mean/wk | Stress +weeks | Price coverage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| US_LEAD | 0.5 | 10_30 | ₹-110150.26 | ₹-466.74 | -437.70 | 36.02% | ₹-139247.75 | ₹-590.03 | 33.90% | 98.10% |
| US_LEAD | 0.5 | 15_10 | ₹-216402.59 | ₹-916.96 | -921.91 | 35.17% | ₹-244963.28 | ₹-1037.98 | 34.32% | 97.95% |
| US_LEAD | 1.0 | 10_30 | ₹-66911.54 | ₹-359.74 | -360.43 | 38.71% | ₹-82155.96 | ₹-441.70 | 37.63% | 98.06% |
| US_LEAD | 1.0 | 15_10 | ₹-83733.88 | ₹-450.18 | -602.40 | 39.78% | ₹-98708.69 | ₹-530.69 | 39.25% | 98.06% |
| ASIA_LEAD | 0.5 | 10_30 | ₹-22702.80 | ₹-98.71 | -361.64 | 40.43% | ₹-47122.78 | ₹-204.88 | 39.57% | 97.93% |
| ASIA_LEAD | 0.5 | 15_10 | ₹-38936.79 | ₹-169.29 | -614.63 | 40.87% | ₹-63056.94 | ₹-274.16 | 39.57% | 97.93% |
| ASIA_LEAD | 1.0 | 10_30 | ₹14172.92 | ₹107.37 | -122.78 | 45.45% | ₹4901.50 | ₹37.13 | 45.45% | 96.92% |
| ASIA_LEAD | 1.0 | 15_10 | ₹12137.26 | ₹91.95 | -298.29 | 45.45% | ₹2994.15 | ₹22.68 | 43.94% | 96.92% |
| GLOBAL_LEAD | 0.5 | 10_30 | ₹-31360.23 | ₹-145.19 | -421.00 | 41.20% | ₹-52118.00 | ₹-241.29 | 38.89% | 98.17% |
| GLOBAL_LEAD | 0.5 | 15_10 | ₹-79311.32 | ₹-368.89 | -808.15 | 39.53% | ₹-99682.83 | ₹-463.64 | 39.53% | 97.97% |
| GLOBAL_LEAD | 1.0 | 10_30 | ₹-2611.28 | ₹-23.31 | -152.03 | 43.75% | ₹-9211.98 | ₹-82.25 | 41.96% | 97.52% |
| GLOBAL_LEAD | 1.0 | 15_10 | ₹-17582.37 | ₹-156.99 | -499.61 | 40.18% | ₹-24085.72 | ₹-215.05 | 39.29% | 97.52% |

## Promotion-gate assessment

Project-wide promotion requires, on an untouched OOS sample, mean weekly net ≥ ₹5,000, median weekly net ≥ ₹5,000, ≥70% positive weeks, adequate execution coverage, and acceptable Base/Stress robustness.

Phase 31.8 was only a discovery family. Because **0/12** cells met the economic/consistency gate even on the full discovery sample, none was eligible for WFA/OOS selection.

The strongest discovery cell fell short by a large margin:
- Base mean weekly net: **₹107.37** vs ₹5,000 target.
- Stress mean weekly net: **₹37.13** vs ₹5,000 target.
- Base median weekly net: **-₹122.78**.
- Stress median weekly net: **-₹211.39**.
- Positive weeks: **45.45%** in both frictions.

## Null-control result

For the strongest true cell (ASIA_LEAD, 1.00, H10_30), the five null-control mean weekly results were:

Base: ₹-144.56, ₹-278.45, ₹-262.85, ₹-56.75, ₹-138.49.

Stress: ₹-199.65, ₹-336.70, ₹-323.43, ₹-115.22, ₹-197.15.

The true cell exceeded all five placebo means in both frictions. This indicates the signal ordering was not simply reproduced by the registered permutations, but it is not sufficient evidence of a tradable strategy because the absolute net economics were far below the promotion gate and the weekly median/win rate were weak.

## Discussion

The global-transmission hypothesis produced a small positive result in the strongest ASIA_LEAD/high-threshold/early-exit configuration, but the effect was not large enough to survive the project's economic objective. The result also shows why gross directional predictability and tradable option P&L must be treated separately: the best Base cell generated ₹47,877 of raw gross over 220 trades, yet transaction/statutory costs and slippage absorbed most of the gross result.

The pattern is directionally consistent with the literature review's motivation for testing cross-market information spillovers, but this experiment does not establish that those spillovers can be monetized in NIFTY options after execution frictions. The family therefore provides a reproducible near-miss/negative result rather than a promotion candidate.

## Strengths

- Strict pre-open information barrier with an explicit prior-date test.
- Frozen, finite grid registered before numerical execution.
- Separate Base and doubled-slippage Stress results.
- Full-panel null permutations using five fixed seeds.
- Historical lot-size and deterministic contract selection.
- Exact execution-price coverage reported for every cell.
- Global inputs cached with provenance hashes.
- No post-result parameter tuning and no WFA/OOS selection after seeing the discovery leaderboard.

## Limitations

- The global inputs are daily index closes, not tick-level global-market microstructure.
- Yahoo Finance is a secondary market-data source for the international indices.
- The option execution model is constrained by the available one-minute historical contract data; real bid/ask depth is not reconstructed.
- The discovery sample spans the full pinned study window and therefore does not by itself establish out-of-sample performance.
- The phase deliberately tests only three composite features and two thresholds; it does not claim that every possible global-transmission specification is exhausted.

## Conclusion

Phase 31.8 is **closed without promotion**. The strongest fixed rule produced only ₹107.37/week Base and ₹37.13/week Stress on average, with 45.45% positive weeks and negative medians. No WFA/OOS stage is justified under the preregistered promotion gate.

This result should be treated as evidence that **global overnight index direction alone is not sufficient for the project's ₹5,000/week net target under the tested defined-risk NIFTY option structure and friction assumptions**.

## Future research direction

The project roadmap still contains other materially distinct hybrid/regime-conditioned mechanisms, notably India VIX + realized volatility, FII/DII/futures positioning where timestamps can be made valid, and trend/volatility/breadth ensembles. The next family should be selected as a new branch with a fresh finite preregistration and should not reuse the Phase 31.8 global-signal grid.

## Reproducibility

Authoritative numerical run: **36252922418**.

Relevant persisted artifacts:
- `reports/phase31_8/gate/data_gate.json`
- `reports/phase31_8/base/true_cell_summary_base.csv`
- `reports/phase31_8/stress/true_cell_summary_stress.csv`
- `reports/phase31_8/base/null_summary_base.csv`
- `reports/phase31_8/stress/null_summary_stress.csv`
- `reports/phase31_8/base/price_coverage.csv`
- `data/cache/phase31_8_global/manifest.json`

No live-trading recommendation is implied by this discovery result.
