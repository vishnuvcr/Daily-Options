# Daily-Options Research Lab

Research program for discovering and validating an intraday NSE options strategy with a target of at least Rs 1,000 NET profit per trading day per active lot, after brokerage, statutory charges, exchange charges, spread/slippage, and conservative execution assumptions.

## Current status — 2026-09-24

Phase 4 nested walk-forward validation is complete. The prior intraday ATM short-straddle near-miss failed the preliminary promotion gate and is retired as a lead family.

| Phase | Branch | Status |
|---|---|---|
| 0 | main | BOOTSTRAPPED |
| 1 | phase-1-data-foundation | COMPLETE-SCAFFOLD |
| 2 | phase-2-baseline-tournament | COMPLETE — GATE FAIL |
| 3 | phase-3-options-structure | PARTIAL — lead families retired |
| 3F | phase-3f-option-microstructure | COMPLETE — lead families retired |
| 4 | phase-4-walk-forward-selection-v2 | COMPLETE — FAIL_PRELIMINARY |
| 3G | phase-3g-oi-confirmed-breakout | NEXT |
| 5 | phase-5-robustness | BLOCKED until a candidate passes validation |
| 6 | phase-6-paper-shadow | PLANNED |
| 7 | phase-7-manuscript | PLANNED |

## Phase 4 result

- Run 35912159508 completed successfully.
- 7,331 observations, 432 total parameter variants, 14 walk-forward windows.
- 22 selected test windows: 8 positive, 14 non-positive.
- Mean selected test-window net: Rs -64.23 per lot.
- Median selected test-window net: Rs -43.69 per lot.
- Zero selected test windows cleared the Rs 1,000/day target.
- No selected-test bootstrap 95% lower bound was positive across the run.

## Next research direction

The next bounded hypothesis is Phase 3G: dynamic intraday price-structure breaks as the primary event, with option OI repositioning used only as post-break confirmation, then executed with a defined-risk debit spread.

A recent 2026 NIFTY event-study reports that OI repositioning is associated with structural breaks but did not retain a robust advance-prediction edge out of sample. That supports using OI as confirmation of an already-underway break rather than as a standalone forecasting trigger.

Latest external source:
https://papers.ssrn.com/sol3/Delivery.cfm/7394780.pdf?abstractid=7394780&mirid=1

## Cost baseline

Research default remains Rs 20 per executed order, 0.15% option-sale STT from 2026-04-01, configurable exchange/statutory rates, and 0.20 option-premium points round-trip slippage. The broker baseline is intentionally conservative and is revalidated against current Paytm Money pricing before promotion.

## Files

- docs/research_plan.md
- docs/research_status.md
- docs/error_log.md
- docs/conversation_log.md
- docs/phase4_walk_forward_results.md
- reports/phase4_walk_forward_summary.json
- reports/phase4_walk_forward_results.csv
- config/cost_model_2026.yaml
- research/
- .github/workflows/

This project is research, not a promise of guaranteed profit. The target is treated as a falsifiable hypothesis.
