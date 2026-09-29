# Phase D — Frozen Holdout Filter Probe

Branch: `research/otm12-phase-d-holdout-filter-v1`
Status: CLOSED
Authoritative workflow: 36533719671

## Frozen rule
Do not enter when prior-day range > 1.314516% AND days to expiry <= 1.5 calendar days.

## Holdout result
The rule was frozen using discovery data only.

| Friction | Holdout trades | Blocked | Blocked fraction | Baseline net P&L | Kept net P&L | Improvement |
|---|---:|---:|---:|---:|---:|---:|
| Base | 348 | 24 | 6.90% | -₹282,985.19 | -₹215,106.13 | +₹67,879.06 |
| Stress | 348 | 24 | 6.90% | -₹343,081.19 | -₹271,170.13 | +₹71,911.06 |

The blocked regime remained strongly negative on holdout:
- Base mean net P&L: -₹2,828.29, 95% bootstrap CI [-₹4,521.80, -₹1,243.52]
- Stress mean net P&L: -₹2,996.29, 95% bootstrap CI [-₹4,688.59, -₹1,411.07]

The retained strategy remained negative:
- Base mean: -₹663.91/trade
- Stress mean: -₹836.94/trade

## Interpretation
The frozen rule identifies a loss-concentration regime and improves the negative baseline. It does **not** convert the strategy into a profitable strategy on the untouched holdout. It is therefore evidence for selective avoidance, not evidence of a complete trading edge.
