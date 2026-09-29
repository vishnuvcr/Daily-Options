# Phase D Results — Frozen Holdout Filter

Authoritative source: clean Base/Stress workflow 36532252218. Phase D workflow 36533292973 SUCCESS.

Discovery threshold for prior-day range top quintile: 1.352%.

Rules frozen from Phase C:
1. Exclude expiry-day entries.
2. Exclude prior-day range above the discovery 80th percentile.
3. Require both exclusions.

## Untouched 2025+ holdout

| Friction | Rule | Trades | Retention | Net P&L | Mean P&L | Win rate | Profit factor |
|---|---|---:|---:|---:|---:|---:|---:|
| Base | Baseline | 348 | 100.00% | -₹282,985.19 | -₹813.18 | 27.59% | 0.541 |
| Base | Exclude expiry day | 276 | 79.31% | -₹184,105.15 | -₹667.05 | 30.07% | 0.562 |
| Base | Exclude top 20% prior-day range | 293 | 84.20% | -₹175,650.58 | -₹599.49 | 28.67% | 0.636 |
| Base | Require both exclusions | 231 | 66.38% | -₹111,294.06 | -₹481.79 | 32.03% | 0.658 |
| Stress | Baseline | 348 | 100.00% | -₹343,081.19 | -₹985.87 | 26.72% | — |
| Stress | Exclude expiry day | 276 | 79.31% | -₹231,721.15 | -₹839.57 | 28.99% | — |
| Stress | Exclude top 20% prior-day range | 293 | 84.20% | -₹226,542.58 | -₹773.18 | 27.99% | — |
| Stress | Require both exclusions | 231 | 66.38% | -₹151,338.06 | -₹655.14 | 31.17% | 0.572 |

## Decision

The frozen filters improve the magnitude of loss and win rate, but none produces positive holdout expectancy. The research therefore does not promote a trading rule from this strategy family.
