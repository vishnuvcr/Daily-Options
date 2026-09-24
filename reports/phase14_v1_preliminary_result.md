# Phase 14 v1 — Global Cross-Market Opening Gap Preliminary Result

Authoritative workflow: 35996090009
Branch: phase-14-global-cross-market-opening-gap-v1
Artifact SHA-256: eac72f9c4c9ab1e75f83fcc1a26cc54e9b8e1bb437b0e3c490485df3b07179b9

## Result
- 768 preregistered simulation cells.
- 15,464 generated entries.
- 30,256 trade records in both friction models.
- Base positive cells: 107/768.
- Stress positive cells: 95/768.
- Base preliminary target-qualified cells: 32/768.
- Stress preliminary target-qualified cells: 32/768.

Best raw base cell:
`SP500|gz1.0|gap0.0075|FADE|09:30:00|LONG|MONTH|h20|r0`
- Mean active-day net: ₹3,548.55/lot/day.
- 10 trades across 5 active days.
- Win rate: 80%.
- Profit factor: 56.45.
- Total net: ₹17,742.74.

Best raw stress cell:
- Same cell.
- Mean active-day net: ₹3,488.55/lot/day.
- 10 trades across 5 active days.
- Win rate: 60%.
- Profit factor: 44.16.

## Walk-forward

The only freeze-safe walk-forward schedule on the 2019–2020 sample produced one test window.

Training/validation selected:
`GLOBAL3|gz0.5|gap0.0075|FADE|09:30:00|LONG|MONTH|h20|r0`

Test result:
- Base: -₹1,232.12/lot/day.
- Stress: -₹1,292.12/lot/day.
- Positive test windows: 0/1.
- Target test windows: 0/1.

## Interpretation

The full-sample leaderboard contains target-sized numbers, but they are not evidence of a validated strategy because the best cells have only 5–6 active days and the sole freeze-safe out-of-sample window for the family was negative.

The freeze-safe selected rule is therefore carried forward unchanged to a later-period independent validation on the pinned 2020–2025 NIFTY option dataset. No parameter search is permitted in that validation.

## Decision

Phase 14 is classified as PROMISING / UNVALIDATED, not promoted and not yet retired. Promotion requires the exact frozen walk-forward-selected rule to demonstrate positive later-period performance after the same base/stress cost model.