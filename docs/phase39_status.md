# Phase 39 Status

## Final state
CLOSED — NEGATIVE DISCOVERY. No WFA/OOS and no promotion.

Authoritative workflow: 36465244174
Branch: phase-39-implied-realized-opening-dislocation-v1

## Data integrity
- Raw sessions: 1,234.
- Post-warm-up sessions: 1,174.
- Feature-eligible sessions: 1,158 / 1,174 = 98.637%.
- IV input coverage: 98.637%.
- Expiry mapping coverage: 100%.
- Prior-information violations: 0.
- Execution coverage minimum: 97.447%.
- Base and Stress accounting reconciliation: passed in all 8 cells.
- Base and Stress executed trades: 1,838 / 1,838 across the 8 cells.

## Economic result
0/8 Base cells and 0/8 Stress cells cleared the preregistered promotion gate:
- mean weekly net >= ₹5,000;
- median weekly net >= ₹5,000;
- positive-week rate >=70%.

Best Base cell by mean weekly net: LOW_DISLOCATION × CONTINUE × 15:10
- total net: +₹8,871.89
- mean weekly net: +₹48.75
- median weekly net: −₹194.98
- positive-week rate: 44.51%
- maximum drawdown: −₹22,396.91

The same cell under Stress:
- total net: −₹3,320.11
- mean weekly net: −₹18.24
- median weekly net: −₹231.43
- positive-week rate: 43.96%
- maximum drawdown: −₹25,491.31

All other true cells were negative in both Base and Stress.

## Null controls
Five fixed permutation null seeds were completed for both Base and Stress. Some null cells are positive in isolated runs, but none meets the economic promotion gate. Nulls were diagnostic only and were not used for tuning.

## Engineering closures
- E0391 CLOSED: Python banker’s rounding at an exact ₹25 half-step.
- E0392 CLOSED: exact-09:30 option-bar lookup was too strict for the pinned source.
- E0393 CLOSED: cutoff predicate was applied after ROW_NUMBER.
- E0394 CLOSED: option snapshot date join required timestamp-derived local dates.
- E0395 CLOSED: final authoritative run completed all frozen stages and validated artifacts.

## Disposition
Phase 39 is RETIRED — NEGATIVE DISCOVERY. The option-implied-versus-realized opening-move dislocation family did not produce the required ₹5,000 net per completed trading week after realistic costs and Stress slippage. No result-driven retuning is allowed.

## Reproducibility
- docs/phase39_plan.md
- docs/phase39_literature_review.md
- research/phase39_implied_realized_opening_dislocation.py
- tests/test_phase39_implied_realized_opening_dislocation.py
- .github/workflows/phase-39-implied-realized-opening-dislocation.yml
- reports/phase39/
