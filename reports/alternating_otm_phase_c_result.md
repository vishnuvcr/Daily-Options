# Alternating OTM Buy/Sell — Phase C Result

## Authoritative execution

Workflow: **36536840710**  
Branch: research/alternating-otm-phase-c-tail-filter-v1  
Parent baseline: 36535251511

Artifact integrity:
- Base input: workflow artifact 11018971057
- Stress input: workflow artifact 11018635908
- Both artifacts downloaded successfully in CI and their actual SHA-256 values were recorded before analysis.
- The first execution failure (36536750155) was implementation-only and did not produce an accepted result; EALTC-001 is closed.

## Data split

- Discovery: 861 trades through 2024-12-31.
- Untouched holdout: 348 trades from 2025-01-01 onward.
- Candidate selection used discovery only.

## Candidate selection

Registered family: four pre-entry features × five discovery quantiles (20 candidates).

Eligible candidates had to:
1. retain at least 50% of discovery trades; and
2. improve total discovery net P&L in both Base and Stress.

Selection metric: highest mean of Base and Stress discovery net-P&L improvement, then minimum improvement, retention, and win rate.

### Selected rule

**first15_abs_ret >= 0.00126795235**, i.e. keep the trade only when the first 15-minute absolute NIFTY return is at least **0.1268%**.

Discovery performance of selected rule:
- retained trades: 474 / 861 = 55.05%
- Base win rate: 57.38%
- Stress win rate: 52.32%
- Base discovery net improvement: +₹99,829.59
- Stress discovery net improvement: +₹142,789.59

The next-best eligible candidate was a gap-magnitude filter (gap_abs_pct <= 50th discovery percentile) with mean discovery improvement ₹119,509.70, so the selected rule was not chosen from a single observed holdout outcome.

## Untouched 2025+ validation

| Metric | Alternating baseline Base | Frozen filter Base | Alternating baseline Stress | Frozen filter Stress |
|---|---:|---:|---:|---:|
| Trades | 348 | 209 | 348 | 209 |
| Retained share | 100% | 60.06% | 100% | 60.06% |
| Win rate | 60.06% | **63.16%** | 57.47% | **60.29%** |
| Gross P&L | ₹129,102 | ₹126,857 | ₹129,102 | ₹126,857 |
| Costs | ₹154,010 | ₹92,411 | ₹214,106 | ₹128,375 |
| Net P&L | -₹24,907 | **+₹34,446** | -₹85,003 | **-₹1,518** |
| Mean/trade | -₹71.57 | **+₹164.81** | -₹244.26 | **-₹7.26** |
| Median/trade | ₹446.72 | **₹667.44** | ₹266.72 | **₹511.44** |
| Profit factor | 0.943 | **1.133** | 0.816 | **0.994** |
| Max drawdown | -₹87,600 | **-₹52,806** | -₹138,184 | **-₹63,074** |

The win-rate improvement survives the untouched holdout (+3.10 percentage points Base; +2.82 points Stress). Base expectancy becomes positive and drawdown falls. Stress, however, remains marginally negative.

## Holdout year behavior

| Friction | Year | Trades | Win rate | Net P&L |
|---|---:|---:|---:|---:|
| Base | 2025 | 141 | 67.38% | +₹58,695 |
| Base | 2026 | 68 | 54.41% | -₹24,249 |
| Stress | 2025 | 141 | 65.25% | +₹33,339 |
| Stress | 2026 | 68 | 50.00% | -₹34,857 |

The positive holdout aggregate is therefore not uniform through time: 2025 is positive, while 2026 is negative under both frictions.

## Robustness sensitivity

These adjacent thresholds were pre-specified as a sensitivity check, not used for selection:

- 40th percentile (0.1124% threshold): Base +₹52,253; Stress +₹12,353 on 231 holdout trades.
- 45th percentile (selected): Base +₹34,446; Stress -₹1,518 on 209 trades.
- 50th percentile (0.1456% threshold): Base +₹11,664; Stress -₹20,028 on 185 trades.

The sensitivity shows that the positive Stress result at the 40th percentile exists, but the frozen discovery-selected 45th-percentile rule does not inherit it. Because 2025+ was the untouched selection holdout, the 40th-percentile outcome cannot be promoted as a newly selected rule without contaminating the validation design.

## Interpretation

The alternating structure does have a real higher-win-rate regime, and the selected pre-entry filter further increases the holdout win rate while removing a meaningful portion of large-tail losses. However, the effect weakens in the 2026 holdout segment and does not clear the Base-and-Stress profitability requirement with the discovery-selected threshold.

Therefore Phase C is **closed as useful evidence, but not as a promoted trading rule**.

No further threshold tuning on the 2025+ holdout is authorized.

## Strengths

- Separate discovery and chronological holdout.
- Selection rule frozen before holdout evaluation.
- Base and doubled-slippage Stress both evaluated.
- Uses only information available before entry.
- Reuses the exact authoritative baseline trade artifacts rather than regenerating market data.

## Limitations

- The underlying alternating payoff remains exposed to rare large losses.
- The 2025+ holdout is only 348 trades and ends in mid-2026.
- The selected rule reduces trading frequency to about 60% of baseline.
- The 2026 portion is materially weaker than 2025.
- The experiment does not establish broker margin/capital efficiency for the naked-short-wing structure.

## Conclusion

Alternating the BUY/SELL directions materially increases win rate. A frozen discovery-derived early-session movement filter raises the holdout win rate further and converts the Base holdout to positive net P&L, but the doubled-slippage Stress holdout remains slightly negative.

The evidence supports the hypothesis that the alternating structure's main weakness is a subset of tail-loss days, but it does **not** yet establish a cost-robust, OOS-profitable trading rule.
