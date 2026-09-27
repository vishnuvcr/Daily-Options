# Phase 31.10 — Institutional Futures Positioning × NIFTY Opening-Gap Translation

## Executive conclusion

Authoritative GitHub Actions run **36337462383 (run 10)** completed the corrected Phase 31.10 pipeline. The frozen institutional-positioning hypothesis was tested across 12 true cells in Base and Stress, with five full-panel null permutations per cell.

**Promotion result: 0/12 Base and 0/12 Stress. No WFA/OOS promotion is authorized.**

No true cell had positive total net P&L. The least-negative Base cell by mean weekly net was FII index-futures net-ratio z-score, threshold 1.0, 10:30 exit: **₹-929.82/week mean**, **₹-770.90/week median**, **29.07% positive weeks**, **₹-159,928.81 total net**. The same cell under Stress produced **₹-1,077.44/week mean**, **₹-855.21/week median**, **24.42% positive weeks**, **₹-185,320.24 total net**.

## Research question

Does prior-session participant-wise NIFTY index-futures positioning — especially FII/DII positioning and FII-DII divergence — contain enough directional information to produce a profitable defined-risk NIFTY option-spread strategy after realistic costs and Base/Stress slippage?

## Methodology

Study window: **2021-07-01 through 2026-08-31**.

Primary official source: NSE participant-wise F&O open-interest archive. **1,234/1,234 source files** were successfully retrieved and hashed. Each file contained FII, DII, Pro and Client participant rows.

For participant p:

`IDX_NET_RATIO = (INDEX_FUTURES_LONG - INDEX_FUTURES_SHORT) / (INDEX_FUTURES_LONG + INDEX_FUTURES_SHORT)`

Three frozen features:
1. FII index-futures net-ratio 60-observation prior-only z-score.
2. DII index-futures net-ratio 60-observation prior-only z-score.
3. FII-minus-DII index-futures net-ratio 60-observation prior-only z-score.

Frozen thresholds: absolute z >= 0.5 and >= 1.0.

Frozen horizons:
- 10:30 IST
- 15:10 IST

Signal direction:
- positive feature -> call debit spread;
- negative feature -> put debit spread.

Execution:
- 09:31 option-open entry;
- nearest NIFTY expiry on/after trade date;
- nearest ₹50 ATM strike;
- 200-point one-lot directional debit spread;
- historical lot sizes;
- frozen project brokerage/statutory charge model;
- Base slippage ₹0.20/order;
- Stress slippage ₹0.40/order.

Null controls: five complete-panel feature permutations with seeds 101, 202, 303, 404 and 505.

## Data gate

| Item | Result |
|---|---:|
| Raw NIFTY sessions | 1,225 |
| Feature-eligible sessions | 1,164 |
| Complete feature sessions | 1,164 |
| Feature coverage | **100.00%** |
| Prior-positioning barrier violations | **0** |
| Participant-OI source files | **1,234/1,234** |
| Required coverage | ≥95% |
| Data gate | **PASS** |

## Base true-cell results

| Feature | Threshold | Exit | Trades | Total net | Mean/week | Median/week | Positive weeks |
|---|---:|---:|---:|---:|---:|---:|---:|
| FII_IDX_NET_Z | 0.5 | 10:30 | 871 | -₹236,369.76 | -₹1,045.88 | -₹898.90 | 29.20% |
| FII_IDX_NET_Z | 0.5 | 15:10 | 871 | -₹716,679.70 | -₹3,157.18 | -₹3,024.56 | 21.15% |
| FII_IDX_NET_Z | 1.0 | 10:30 | 591 | -₹159,928.81 | **-₹929.82** | -₹770.90 | 29.07% |
| FII_IDX_NET_Z | 1.0 | 15:10 | 591 | -₹518,322.08 | -₹3,013.50 | -₹2,374.93 | 17.44% |
| DII_IDX_NET_Z | 0.5 | 10:30 | 886 | -₹232,642.46 | -₹1,029.39 | -₹796.31 | 29.65% |
| DII_IDX_NET_Z | 0.5 | 15:10 | 889 | -₹701,203.29 | -₹3,089.00 | -₹2,205.84 | 22.91% |
| DII_IDX_NET_Z | 1.0 | 10:30 | 666 | -₹168,859.68 | -₹943.35 | -₹793.27 | 29.05% |
| DII_IDX_NET_Z | 1.0 | 15:10 | 669 | -₹490,436.32 | -₹2,724.65 | -₹1,907.23 | 22.78% |
| FII_DII_DIVERGENCE_Z | 0.5 | 10:30 | 856 | -₹247,158.75 | -₹1,098.48 | -₹909.04 | 27.11% |
| FII_DII_DIVERGENCE_Z | 0.5 | 15:10 | 858 | -₹835,510.51 | -₹3,713.38 | -₹3,549.65 | 19.11% |
| FII_DII_DIVERGENCE_Z | 1.0 | 10:30 | 564 | -₹162,853.56 | -₹946.82 | -₹693.12 | 28.49% |
| FII_DII_DIVERGENCE_Z | 1.0 | 15:10 | 566 | -₹519,521.31 | -₹3,038.14 | -₹2,380.91 | 22.22% |

## Stress true-cell results

| Feature | Threshold | Exit | Total net | Mean/week | Median/week | Positive weeks |
|---|---:|---:|---:|---:|---:|---:|
| FII_IDX_NET_Z | 0.5 | 10:30 | -₹274,155.00 | -₹1,213.08 | -₹1,019.46 | 25.66% |
| FII_IDX_NET_Z | 0.5 | 15:10 | -₹754,336.13 | -₹3,323.07 | -₹3,076.40 | 20.26% |
| FII_IDX_NET_Z | 1.0 | 10:30 | -₹185,320.24 | **-₹1,077.44** | -₹855.21 | 24.42% |
| FII_IDX_NET_Z | 1.0 | 15:10 | -₹543,590.20 | -₹3,160.41 | -₹2,477.26 | 16.86% |
| DII_IDX_NET_Z | 0.5 | 10:30 | -₹270,554.64 | -₹1,197.14 | -₹978.87 | 26.99% |
| DII_IDX_NET_Z | 0.5 | 15:10 | -₹738,978.03 | -₹3,255.41 | -₹2,405.74 | 21.15% |
| DII_IDX_NET_Z | 1.0 | 10:30 | -₹197,360.47 | -₹1,102.57 | -₹892.81 | 25.14% |
| DII_IDX_NET_Z | 1.0 | 15:10 | -₹518,844.62 | -₹2,882.47 | -₹2,049.13 | 21.67% |
| FII_DII_DIVERGENCE_Z | 0.5 | 10:30 | -₹284,748.09 | -₹1,265.55 | -₹1,036.46 | 24.00% |
| FII_DII_DIVERGENCE_Z | 0.5 | 15:10 | -₹873,052.01 | -₹3,880.23 | -₹3,669.59 | 18.22% |
| FII_DII_DIVERGENCE_Z | 1.0 | 10:30 | -₹187,085.66 | -₹1,087.71 | -₹824.41 | 24.42% |
| FII_DII_DIVERGENCE_Z | 1.0 | 15:10 | -₹543,774.95 | -₹3,179.97 | -₹2,575.68 | 21.05% |

## Execution coverage

All 12 true cells cleared the 95% execution-price coverage requirement.

Coverage ranged from **97.41% to 98.96%**. The same price-coverage artifacts were validated separately for Base and Stress.

## Null controls

All 60 null summaries per friction were generated and persisted.

The null controls are diagnostic: they test whether date-specific association between positioning and outcomes is stronger than a complete-panel permutation. Even where a true cell may exceed individual null means, the absolute net economics remain substantially negative, so no cell qualifies for promotion.

## Costs

The accounting identity is:

`net P&L = raw gross - slippage - transaction/statutory costs`

For example, Base FII z-score 1.0 / 10:30:
- raw gross: **-₹68,823.25**
- slippage: **₹25,404.00**
- transaction/statutory costs: **₹65,701.56**
- net: **-₹159,928.81**

Thus the negative result is not explained by an omitted friction term; gross strategy economics were already negative.

## Interpretation

The experiment rejects this particular institutional-positioning formulation under the frozen implementation assumptions.

Important distinction:
- it does **not** prove that FII/DII positioning contains no information;
- it shows that these three prior-only standardized index-futures positioning signals, mapped directly into the tested debit-spread structure and executed at the declared times, did not satisfy the project's economic gate.

The long-horizon 15:10 exit was consistently more negative than the 10:30 exit across all three feature families.

## Strengths

- Official NSE participant-OI source.
- 1,234 source files hashed and persisted.
- 100% feature coverage after the declared warm-up.
- Zero prior-information barrier violations.
- Finite 12-cell preregistered grid.
- Complete-panel null controls.
- Base and Stress slippage.
- Historical lot-size schedule.
- Explicit transaction/statutory accounting.
- Separate execution-coverage validation.
- No post-result threshold expansion.

## Limitations

- Participant OI is an end-of-day positioning aggregate, not intraday order flow.
- Futures positioning alone does not reveal the complete option hedge book.
- The chosen 60-observation z-score is only one finite normalization.
- Option execution still depends on historical one-minute prices rather than full bid/ask queue reconstruction.
- The discovery period is not an untouched OOS sample.
- Cash FII/DII flow was not used as a primary historical feature because the public endpoint does not provide a reliable full-period daily backfill.

## Conclusion

**Phase 31.10 is CLOSED as negative discovery evidence.**

No cell met the project's ₹5,000/week mean and median requirements, the 70% positive-week requirement, and the Base/Stress requirement simultaneously. No WFA/OOS promotion is justified from this family.

## Future direction

The next family should be materially distinct rather than simply tuning the failed institutional-positioning thresholds. Candidate research areas already identified in the project roadmap include:
- option-skew/smile dislocations;
- dealer/gamma exposure proxies;
- volatility-surface term-structure dislocations;
- combined global-lead + India-volatility mechanisms;
- carefully time-aligned futures/options positioning with a different execution hypothesis.

Any next family must be separately preregistered with its own data gate, finite grid, null controls and stop rule.

## Reproducibility

Authoritative numerical run: **36337462383**.

Artifacts:
- `reports/phase31_10/gate/data_gate.json`
- `reports/phase31_10/base/true_cell_summary_base.csv`
- `reports/phase31_10/stress/true_cell_summary_stress.csv`
- `reports/phase31_10/base/null_summary_base.csv`
- `reports/phase31_10/stress/null_summary_stress.csv`
- `reports/phase31_10/base/price_coverage.csv`
- `reports/phase31_10/stress/price_coverage.csv`

No live-trading recommendation is implied by this discovery result.
