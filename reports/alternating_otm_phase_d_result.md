# Alternating OTM Buy/Sell — Phase D Walk-Forward Result

## Authoritative execution

Workflow: **36537486155**  
Branch: research/alternating-otm-phase-d-walkforward-v1  
Phase C parent: 36536840710  
Input baseline: 36535251511  
Artifact: 11019385172

The 0.126795% first15_abs_ret threshold was frozen from Phase C. No new threshold was optimized.

## Walk-forward design

- 2023 test: training history through 2022.
- 2024 test: training history through 2023.
- 2025 test: training history through 2024.
- 2026 test: training history through 2025.
- The same frozen threshold was applied to every test period.
- The consumed Phase C 2025+ holdout was not used to select parameters.

## Results

| Test year | Friction | Baseline net | Filtered net | Improvement | Baseline WR | Filtered WR | Filtered PF | Filtered DD |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 2023 | Base | -₹37,228 | -₹15,538 | +₹21,691 | 56.33% | 51.59% | 0.735 | -₹29,254 |
| 2023 | Stress | -₹66,628 | -₹30,658 | +₹35,971 | 47.76% | 42.06% | 0.539 | -₹40,534 |
| 2024 | Base | -₹52,124 | -₹15,323 | +₹36,801 | 61.79% | 60.16% | 0.869 | -₹28,894 |
| 2024 | Stress | -₹75,164 | -₹27,143 | +₹48,021 | 58.94% | 56.10% | 0.778 | -₹36,446 |
| 2025 | Base | +₹36,225 | +₹58,695 | +₹22,470 | 63.79% | 67.38% | 1.347 | -₹52,806 |
| 2025 | Stress | -₹7,491 | +₹33,339 | +₹40,830 | 61.32% | 65.25% | 1.188 | -₹57,666 |
| 2026 | Base | -₹61,133 | -₹24,249 | +₹36,884 | 51.43% | 54.41% | 0.730 | -₹37,701 |
| 2026 | Stress | -₹77,513 | -₹34,857 | +₹42,656 | 48.57% | 50.00% | 0.633 | -₹44,513 |

### Aggregate across the four chronological test periods

Base:
- Baseline total: **-₹114,260**
- Frozen-filter total: **+₹3,585**
- Improvement: **+₹117,845**
- Improvement occurred in **4/4** test years.

Stress:
- Baseline total: **-₹226,796**
- Frozen-filter total: **-₹59,319**
- Improvement: **+₹167,477**
- Improvement occurred in **4/4** test years.

## Important interpretation

The filter is not merely a 2025 artifact. It improved the alternating strategy's net P&L in every chronological test period under both friction assumptions.

However, this is an **improvement-over-baseline result**, not proof of a profitable strategy in every regime:

- 2023 remained negative.
- 2024 remained negative.
- 2026 remained negative.
- Only 2025 was profitable under both Base and Stress.
- The filter often reduced drawdown substantially and improved profit factor, but it did not eliminate the underlying negative expectancy in most years.

There is also an important win-rate observation: the filter does not universally increase win rate. In 2023 and 2024 the retained win rate was lower than the unfiltered alternating strategy even though net P&L improved. This confirms that win rate is not an adequate optimization target.

## Phase D decision

**CLOSED — ROBUST IMPROVEMENT CONFIRMED; PROFITABILITY NOT YET ESTABLISHED.**

The frozen first15_abs_ret mechanism survives four chronological test periods as a consistent loss-reduction mechanism. It should therefore remain part of the candidate architecture.

It is not promoted to live-trading status because aggregate Stress remains negative and most individual years remain negative.

## Next research gate

The next phase should investigate whether the remaining losses are associated with a distinct, independently measurable market regime rather than simply another threshold on first15_abs_ret.

Candidate mechanisms should be preregistered before testing and should focus on:
- directional breakout/tail magnitude after the 09:30 decision;
- expiry proximity;
- volatility regime;
- overnight/global transmission;
- option premium asymmetry;
- capital/margin efficiency and short-option risk.

No further first15 threshold tuning is warranted on the existing data.
