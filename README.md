# Daily-Options Research Lab

Research program for discovering and validating an intraday NSE options strategy with a target of at least Rs 1,000 NET profit per trading day per active lot, after brokerage, statutory charges, exchange charges, spread/slippage, and conservative execution assumptions.

## Current status — 2026-09-24

Phase 4, Phase 3G, and Phase 3H have failed their stated promotion gates and are retired. Phase 3I has passed its strict futures/spot predictive gate and is now in the corrected matching 2017–2020 option implementation.

| Phase | Branch | Status |
|---|---|---|
| 0 | main | BOOTSTRAPPED |
| 1 | phase-1-data-foundation | COMPLETE-SCAFFOLD |
| 2 | phase-2-baseline-tournament | COMPLETE — GATE FAIL |
| 3 | phase-3-options-structure | PARTIAL — lead families retired |
| 3F | phase-3f-option-microstructure | COMPLETE — lead families retired |
| 4 | phase-4-walk-forward-selection-v2 | COMPLETE — FAIL_PRELIMINARY |
| 3G | phase-3g-oi-confirmed-breakout | COMPLETE — FAIL_PRELIMINARY; RETIRED |
| 3H | phase-3h-option-lead-lag | COMPLETE — FAIL_PRELIMINARY; RETIRED |
| 3I | phase-3i-futures-spot-lead-lag | IN PROGRESS — OPTION IMPLEMENTATION |\n| 5 | phase-5-robustness | BLOCKED until a candidate passes validation |
| 6 | phase-6-paper-shadow | PLANNED |
| 7 | phase-7-manuscript | PLANNED |

## Phase 3G result

- Corrected run 35916973751 completed after the walk-forward date bug was fixed.
- 128 pre-registered variants: 0 positive on all-calendar-day mean net at 0.20-point slippage; best Rs -61.11/lot/day.
- At 0.40-point stress slippage, 0/128 were positive; best Rs -79.55/lot/day.
- Corrected walk-forward: 13 test windows; 1 positive at base friction and 0 positive at stress friction; mean test-window net Rs -192.79 and Rs -252.79 respectively.
- Decision: retire Phase 3G without enlarging the grid.

## Phase 3H result

- Run 35918302989 completed successfully after the indexed-engine and cache corrections.
- 108 pre-registered variants: all negative at both base and stressed slippage.
- Base best mean net: Rs -181.83/lot/day; stress best mean net: Rs -241.83/lot/day.
- Nested WFA: 0/16 positive test windows at both frictions; mean test-window net Rs -191.39 and Rs -251.39 respectively.
- Decision: retire Phase 3H without enlarging the option-pressure family.

## Phase 3I status

- Data gate: PASS — 991 common trading dates, 99.733% timestamp overlap, 99.193% common-day session completeness at the >=350-minute threshold.
- Strict predictive gate: PASS — two qualifying 3-minute continuation families (10 bps futures-minus-spot lead gap; 10 bps basis change), stable across both sample halves and at least two forward horizons.
- Option implementation: correcting two pre-run bookkeeping defects before accepting any numerical P&L.

## Cost baseline

Research default remains Rs 20 per executed order, 0.15% option-sale STT from 2026-04-01, configurable exchange/statutory rates, and 0.20 option-premium points round-trip slippage. The broker baseline is intentionally conservative and is revalidated against current Paytm Money pricing before promotion.

## Files

- docs/research_plan.md
- docs/research_status.md
- docs/error_log.md
- docs/conversation_log.md
- docs/phase3g_results.md
- docs/phase3h_results.md
- docs/phase4_walk_forward_results.md
- docs/phase3i_hypothesis.md
- docs/phase3i_option_implementation.md
- config/cost_model_2026.yaml
- research/
- .github/workflows/

This project is research, not a promise of guaranteed profit. The target is treated as a falsifiable hypothesis.
