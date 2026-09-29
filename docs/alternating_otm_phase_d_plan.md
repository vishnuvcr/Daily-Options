# Phase D — Alternating OTM Walk-Forward Validation

## Objective
Test whether the alternating BUY-1/SELL-2 structure and its pre-entry tail-loss mechanism remain profitable across rolling out-of-sample periods without using the already-consumed 2025+ holdout for rule selection.

## Frozen inputs
- Parent baseline: workflow 36535251511.
- Phase C selected mechanism: first15_abs_ret >= 0.126795%.
- Phase C 2025+ holdout is permanently excluded from parameter selection in Phase D.
- Existing Base and Stress cost models remain unchanged.

## Walk-forward design
Chronological folds:
1. Train 2021-07-01 through 2022-12-31; test 2023.
2. Train 2021-07-01 through 2023-12-31; test 2024.
3. Train 2021-07-01 through 2024-12-31; test 2025.
4. Train 2021-07-01 through 2025-12-31; test available 2026 data.

For each fold, the Phase-C mechanism is not re-tuned. The fixed threshold is evaluated as a preregistered economic hypothesis. A separate baseline is evaluated on the identical test dates.

## Primary comparisons
- Alternating unfiltered versus alternating + frozen 0.126795% first15_abs_ret filter.
- Base and Stress.
- Net P&L, mean/median trade, win rate, profit factor, max drawdown, max loss.
- Retained-trade percentage.
- Year/fold stability.

## Robustness gate
The mechanism is considered supported only if it improves or preserves net expectancy across multiple independent test folds and does not rely on one calendar year. Positive Base alone is insufficient if Stress systematically fails.

## Additional diagnostic
Measure whether losses excluded by the filter are disproportionately large relative to retained losses. This is descriptive and cannot alter the frozen rule.

## Phase boundary
No new threshold, feature, or combination is selected in Phase D. If the fixed rule fails walk-forward robustness, Phase D closes negative and a later phase must use a separately defined mechanism.