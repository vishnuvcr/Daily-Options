# Phase C Results — OTM12 Loss Patterns

Authoritative source: clean Base workflow 36532252218. Phase C workflow 36533168599 SUCCESS.

## Baseline samples

| Sample | Trades | Wins | Losses | Win rate | Gross P&L | Costs | Net P&L |
|---|---:|---:|---:|---:|---:|---:|---:|
| Discovery | 861 | 216 | 645 | 25.09% | -₹142,907.50 | ₹292,029.18 | -₹434,936.68 |
| Holdout | 348 | 96 | 252 | 27.59% | -₹129,102.25 | ₹153,882.94 | -₹282,985.19 |
| All | 1,209 | 312 | 897 | 25.81% | -₹272,009.75 | ₹445,912.12 | -₹717,921.87 |

## Statistical result

All 15 frozen pre-entry features had discovery winner/loser Mann–Whitney p-values above 0.15. The clean Base shallow loss tree had 5-fold chronological CV AUC ≈ 0.506.

## Recurring adverse regimes

- Prior-day range above the discovery 80th percentile (~1.352%) had discovery mean P&L -₹944.23 and holdout mean P&L -₹1,951.54.
- Expiry-day entries had holdout mean P&L about -₹1,373.33 and holdout win rate 18.06%.
- First-15-minute and premium-geometry patterns changed between discovery and holdout, so they were not promoted to the filter phase.

## Payoff mechanism

The fixed structure profits when one wing's two farther OTM longs expand enough to offset the nearer short, the opposite wing and costs. In the full sample, 44.7% of losses had both wing-level gross contributions negative; 0% of winning trades had both wings negative.
