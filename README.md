# Daily-Options Research Lab

Research program for discovering and validating an intraday NSE options strategy with a target of at least Rs 1,000 NET profit per trading day per active lot, after brokerage, statutory charges, exchange charges, spread/slippage, and conservative execution assumptions.

## Objective
- Search rule-based, volatility, order-flow, options-structure, regime and ML-assisted strategy families.
- Use leakage-safe walk-forward validation and a final untouched out-of-sample period.
- Model Paytm Money execution costs and Indian F&O charges explicitly.
- Treat Rs 1,000/lot/day as a measurable research target, never as a guaranteed return.
- Iterate through defined phases until a candidate clears the promotion gates or the current family is exhausted.

## Phase map
| Phase | Branch | Goal | Status |
|---|---|---|---|
| 0 | main | Research charter, audit trail, cost model, repository scaffolding | BOOTSTRAPPED |
| 1 | phase-1-data-foundation | Acquire/cache/validate spot, futures, option-chain, OI, IV and context data | PLANNED |
| 2 | phase-2-baseline-tournament | Benchmark ORB, VWAP, EMA, momentum, mean-reversion and volatility strategies | PLANNED |
| 3 | phase-3-options-structure | Test spreads, straddles/strangles, gamma/IV/OI and regime-conditioned structures | PARTIAL — price/structure families tested; 3E retired |
| 3F | phase-3f-option-microstructure | IV/OI/volume/strike-structure and volatility-regime hypothesis | ACTIVE — full data audit |
| 4 | phase-4-walk-forward-selection | Freeze candidate families and run nested walk-forward OOS selection | PLANNED |
| 5 | phase-5-robustness | Stress costs, slippage, delays, regime shifts, Monte Carlo and parameter perturbations | PLANNED |
| 6 | phase-6-paper-shadow | Daily paper-trading/shadow execution validation | PLANNED |
| 7 | phase-7-manuscript | Final strategy specification, results, figures, appendices and future research | PLANNED |

## Current status
- Phase 3E VWAP/RSI momentum was corrected and tested; no variant met the Rs 1,000/day target, so it is retired.
- Phase 3F is now the active research branch. It audits every parquet partition of a pinned multi-year IV/OI-capable dataset before strategy testing. The public source viewer currently shows an anomalous negative minimum for volume, so volume features are quarantined pending CI measurement and independent reconciliation.

## Initial evidence
As of 2026-09-24:
- The repository was empty when research began.
- NSE contract information currently provides permitted lot-size data and was updated 2026-09-10.
- From 2026-04-01, NSE option-sale STT is 0.15% of premium.
- Paytm Money announced flat Rs 20 brokerage across segments effective 2025-01-15.
- Public research/data sources include NSE reports, Zenodo NIFTY 1-minute options data (2017-2020), a Hugging Face NIFTY options dataset (2020-2025), and open-source NIFTY backtesting/data projects.

## Promotion gate
A strategy is not promoted merely because raw P&L is high. It must clear:
1. Positive net OOS expectancy after costs.
2. Mean OOS daily net P&L per lot >= Rs 1,000 over the final test horizon, or a documented near-miss.
3. Sufficient trade count and no single-day contribution dominating.
4. Stable performance across years/regimes and reasonable parameter perturbations.
5. No look-ahead, survivorship, strike/expiry-selection or execution-price leakage.
6. Positive under adverse slippage and transaction-cost stress.
7. Conservative execution remains viable.
8. Paper/shadow evidence does not show unacceptable live slippage or signal decay.

## Files
- docs/research_plan.md
- docs/research_status.md
- docs/error_log.md
- docs/conversation_log.md
- config/cost_model_2026.yaml
- research/ for strategy, validation and reports
- .github/workflows/ for manual phase workflows

This project is research, not a promise of guaranteed profit. The target is treated as a hypothesis to attack with evidence.


## Phase 3F data provenance
- Primary pinned source: [artist-23/nifty-options-data](https://huggingface.co/datasets/artist-23/nifty-options-data), revision `45e0a04`.
- Source tree contains `NIFTY/MONTH` and `NIFTY/WEEK` parquet partitions; the repository now scans the complete tree rather than a single file.
- Raw 1.27 GB source data are cached on GitHub Actions runners; the repository keeps the immutable source manifest and derived audit reports/artifacts rather than duplicating the binary dataset.
