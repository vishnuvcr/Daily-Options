# Daily-Options Research Lab

Research program for discovering and validating an intraday NSE options strategy with a target of at least Rs 1,000 NET profit per trading day per active lot, after brokerage, statutory charges, exchange charges, spread/slippage, and conservative execution assumptions.

## Current status — 2026-09-24

**Phase 8 and Phase 9 are active.** The user-directed stopping rule requires continued research until a reproducible Rs 1,000 net/lot/day strategy clears the formal validation gate.

| Phase | Branch | Status |
|---|---|---|
| 0 | main | BOOTSTRAPPED |
| 1 | phase-1-data-foundation | COMPLETE-SCAFFOLD |
| 2 | phase-2-baseline-tournament | COMPLETE — GATE FAIL |
| 3 | phase-3-options-structure | COMPLETE — LEAD FAMILIES RETIRED |
| 3F | phase-3f-option-microstructure | COMPLETE — LEAD FAMILIES RETIRED |
| 4 | phase-4-walk-forward-selection-v2 | COMPLETE — FAIL_PRELIMINARY |
| 3G | phase-3g-oi-confirmed-breakout | COMPLETE — FAIL_PRELIMINARY; RETIRED |
| 3H | phase-3h-option-lead-lag | COMPLETE — FAIL_PRELIMINARY; RETIRED |
| 3I | phase-3i-opening-false-break-reversion | COMPLETE — FAIL_PRELIMINARY; RETIRED |
| 5 | phase-5-robustness | BLOCKED — no candidate passed validation |
| 6 | phase-6-paper-shadow | BLOCKED |
| 7 | phase-7-manuscript | COMPLETE — SYNTHESIS CHECKPOINT |
| 8 | phase-8-hybrid-ml-momentum-v1 | ACTIVE — corrected 96-variant CI run |
| 9 | phase-9-regime-credit-spread-v1 | ACTIVE — corrected 96-variant CI run |

## Frozen Phase 3 evidence


Canonical Phase 3I run: 35919447949.

- 144 pre-registered variants.
- 404,235 spot feature rows.
- 119,196 signal rows.
- 118,860 executable trades.
- Base friction: 0/144 positive variants; best mean calendar-day net -Rs 854.06/lot/day.
- Stress friction: 0/144 positive variants; best mean calendar-day net -Rs 886.27/lot/day.
- Walk-forward: 14/14 test windows negative.
- Base mean test-window net: -Rs 1,626.99/lot.
- Stress mean test-window net: -Rs 1,686.99/lot.
- Final decision: retire the exploratory family and stop further parameter mining on the current public close-based datasets.

## Active targets

Phase 8 tests regime-aware NIFTY momentum/mean reversion plus ATM option-premium confirmation with dynamic exits. Phase 9 tests regime-filtered defined-risk credit spreads. Both families are pre-registered at 96 variants each; no numerical result is accepted until corrected CI runs complete.

## Active research documents

- [Phase 8 hypothesis](docs/phase8_hypothesis.md)
- [Final manuscript checkpoint](docs/final_manuscript.md)
- [Data-gap assessment](docs/data_gap_assessment.md)
- [Research plan](docs/research_plan.md)
- [Research status](docs/research_status.md)
- [Error log](docs/error_log.md)
- [Conversation log](docs/conversation_log.md)
- [Final summary JSON](reports/final_research_summary.json)
- [Final walk-forward figure](docs/figures/final_wfa_summary.svg)
- [Final Phase 3I figure](docs/figures/final_phase3i.svg)

## Cost baseline

Research default remains Rs 20 per executed order, 0.15% option-sale STT from 2026-04-01, configurable exchange/statutory rates, and 0.20 option-premium points per-leg base slippage. The default is conservative; any future paper/live stage must use the actual Paytm Money account tariff.

## Next step

Phase 8 runs first on the pinned public option dataset. Regardless of its outcome, the overall study continues under the updated Rs 1,000 target until a candidate clears formal out-of-sample and cost-aware validation. Better synchronized/executable data remains the next upgrade path.

This project is research, not a promise of guaranteed profit. The target is treated as a falsifiable hypothesis.
