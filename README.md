# Daily-Options Research Lab

Research program for discovering and validating an intraday NSE options strategy with a target of at least Rs 1,000 NET profit per trading day per active lot, after brokerage, statutory charges, exchange charges, spread/slippage, and conservative execution assumptions.

## Current status — 2026-09-24

Phase 4 and Phase 3G have both failed their stated promotion gates and are retired. Phase 3H is the active bounded experiment.

| Phase | Branch | Status |
|---|---|---|
| 0 | main | BOOTSTRAPPED |
| 1 | phase-1-data-foundation | COMPLETE-SCAFFOLD |
| 2 | phase-2-baseline-tournament | COMPLETE — GATE FAIL |
| 3 | phase-3-options-structure | PARTIAL — lead families retired |
| 3F | phase-3f-option-microstructure | COMPLETE — lead families retired |
| 4 | phase-4-walk-forward-selection-v2 | COMPLETE — FAIL_PRELIMINARY |
| 3G | phase-3g-oi-confirmed-breakout | COMPLETE — FAIL_PRELIMINARY; RETIRED |
| 3H | phase-3h-option-lead-lag | ACTIVE — indexed CI rerun 35918302989 |
| 5 | phase-5-robustness | BLOCKED until a candidate passes validation |
| 6 | phase-6-paper-shadow | PLANNED |
| 7 | phase-7-manuscript | PLANNED |

## Phase 3G result

- Corrected run 35916973751 completed after the walk-forward date bug was fixed.
- 128 pre-registered variants: 0 positive on all-calendar-day mean net at 0.20-point slippage; best Rs -61.11/lot/day.
- At 0.40-point stress slippage, 0/128 were positive; best Rs -79.55/lot/day.
- Corrected walk-forward: 13 test windows; 1 positive at base friction and 0 positive at stress friction; mean test-window net Rs -192.79 and Rs -252.79 respectively.
- Decision: retire Phase 3G without enlarging the grid.

## Next research direction

Phase 3H tests derivative price-discovery / option-lead-lag: whether short-horizon ATM call/put price changes contain incremental information about the next 1-5 minute NIFTY spot move, with any tradable edge expressed via defined-risk debit spreads.

## Cost baseline

Research default remains Rs 20 per executed order, 0.15% option-sale STT from 2026-04-01, configurable exchange/statutory rates, and 0.20 option-premium points round-trip slippage. The broker baseline is intentionally conservative and is revalidated against current Paytm Money pricing before promotion.

## Files

- docs/research_plan.md
- docs/research_status.md
- docs/error_log.md
- docs/conversation_log.md
- docs/phase3g_results.md
- docs/phase4_walk_forward_results.md
- config/cost_model_2026.yaml
- research/
- .github/workflows/

This project is research, not a promise of guaranteed profit. The target is treated as a falsifiable hypothesis.
