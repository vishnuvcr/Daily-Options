# Phase 31.9 — India VIX × Realized Volatility × NIFTY Opening-Gap Direction: Final Result

## Executive conclusion

Authoritative GitHub Actions run **36334135198 (run 6)** completed the frozen Phase 31.9 pipeline: unit tests, pinned NIFTY cache, official NSE India VIX acquisition, prior-only data gate, Base and Stress discovery, null controls, execution-coverage validation, report persistence and artifact upload.

**Promotion result: 0/12 true cells passed the preregistered ₹5,000/week economic-and-consistency gate in Base, and 0/12 passed it in Stress. Phase 31.9 is therefore closed without WFA/OOS promotion.**

The strongest discovery cell by mean weekly net was:

**Base:** LOW regime × FADE_GAP × 15:10 exit — **-₹114.44/week mean**, **-₹428.87/week median**, **35.14% positive weeks**, **-₹4,234.21 total net**.

**Stress:** MID regime × FADE_GAP × 15:10 exit — **-₹238.14/week mean**, **-₹552.35/week median**, **42.39% positive weeks**, **-₹21,908.68 total net**.

No cell had positive total net P&L in either friction regime. Some true cells did outperform every registered null-control mean for the same cell, but those differences occurred while the absolute net economics remained negative and far below the project promotion gate.

## Research question

Does the relationship between the previous session's India VIX close and prior-only NIFTY 20-session realized volatility identify opening-gap regimes in which a deterministic ATM directional debit spread can reach the project's ₹5,000 net/week target after realistic costs and Base/Stress slippage?

## Preregistered methodology

The study window was **2021-07-01 through 2026-08-31**.

Frozen grid:
- Regime: LOW (VIX/RV20 ≤ 0.90), MID (0.90–1.10), HIGH (>1.10).
- Gap mode: FOLLOW_GAP or FADE_GAP.
- Exit: 10:30 or 15:10 IST.
- Total true cells: 3 × 2 × 2 = **12**.

Signal barrier:
- Previous completed NIFTY close only.
- Previous completed India VIX close only.
- RV20 from the previous 20 completed NIFTY close-to-close log returns, annualized with √252.
- No current-day VIX or current-day close entered the signal.
- Zero opening gap produced no trade.

Execution:
- 09:31 option open entry.
- Selected horizon option close exit.
- Nearest NIFTY expiry on/after trade date.
- ATM strike nearest ₹50.
- One-lot 200-point directional debit spread.
- Historical lot-size schedule.
- Base slippage ₹0.20/order.
- Stress slippage ₹0.40/order.
- Frozen transaction/statutory charge model.

Null controls:
- Five fixed seeds: 101, 202, 303, 404, 505.
- Regime labels permuted across the complete feature-eligible panel before threshold/signal reconstruction.
- 60 null summaries per friction regime.

## Data gate and provenance

The corrected official-NSE acquisition completed using **89-day request windows** and persisted per-chunk hashes/row counts.

| Gate item | Result |
|---|---:|
| Raw NIFTY sessions | 1,228 |
| Feature-eligible sessions | 1,206 |
| Warm-up/missing-feature sessions | 22 |
| Complete feature coverage | 100.00% |
| Prior-date barrier violations | 0 |
| India VIX rows persisted | 1,281 |
| VIX minimum date | 2021-07-01 |
| VIX maximum date | 2026-08-31 |
| Required feature coverage | ≥95% |
| Data gate | **PASS** |

The NSE historical-reports service explicitly exposes Historical Data — India VIX, and the Phase 31.9 acquisition used the official NSE VIX historical endpoint with source-response hashes and a persisted manifest. citeturn526592search0turn526592search2

## True-cell results — Base

| Regime | Direction | Exit | Trades | Total net | Mean/wk | Median/wk | Positive weeks | Max drawdown |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| LOW | FOLLOW | 10:30 | 108 | ₹-18,970.41 | ₹-512.71 | ₹-580.06 | 35.14% | ₹-24,913.75 |
| LOW | FOLLOW | 15:10 | 109 | ₹-36,212.40 | ₹-978.71 | ₹-1,262.57 | 32.43% | ₹-45,258.95 |
| LOW | FADE | 10:30 | 109 | ₹-13,284.49 | ₹-359.04 | ₹-499.67 | 40.54% | ₹-18,703.78 |
| LOW | FADE | 15:10 | 108 | ₹-4,234.21 | ₹-114.44 | ₹-428.87 | 35.14% | ₹-19,231.55 |
| MID | FOLLOW | 10:30 | 232 | ₹-44,678.25 | ₹-490.97 | ₹-292.13 | 39.56% | ₹-49,623.36 |
| MID | FOLLOW | 15:10 | 233 | ₹-89,262.17 | ₹-980.90 | ₹-1,009.37 | 37.36% | ₹-96,380.46 |
| MID | FADE | 10:30 | 234 | ₹-33,479.66 | ₹-363.91 | ₹-353.56 | 39.13% | ₹-32,249.44 |
| MID | FADE | 15:10 | 234 | ₹-11,682.78 | ₹-126.99 | ₹-482.82 | 42.39% | ₹-47,415.18 |
| HIGH | FOLLOW | 10:30 | 847 | ₹-151,219.67 | ₹-741.27 | ₹-790.95 | 31.37% | ₹-152,709.63 |
| HIGH | FOLLOW | 15:10 | 846 | ₹-100,846.31 | ₹-494.34 | ₹-641.89 | 39.22% | ₹-135,063.19 |
| HIGH | FADE | 10:30 | 847 | ₹-106,794.40 | ₹-523.50 | ₹-548.90 | 32.84% | ₹-109,996.48 |
| HIGH | FADE | 15:10 | 846 | ₹-184,059.52 | ₹-902.25 | ₹-1,640.42 | 37.75% | ₹-195,327.98 |

## True-cell results — Stress

| Regime | Direction | Exit | Trades | Total net | Mean/wk | Median/wk | Positive weeks | Max drawdown |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| LOW | FOLLOW | 10:30 | 108 | ₹-23,591.94 | ₹-637.62 | ₹-620.04 | 35.14% | ₹-28,320.08 |
| LOW | FOLLOW | 15:10 | 109 | ₹-40,777.06 | ₹-1,102.08 | ₹-1,367.54 | 29.73% | ₹-48,211.59 |
| LOW | FADE | 10:30 | 109 | ₹-17,957.99 | ₹-485.35 | ₹-599.62 | 40.54% | ₹-21,198.34 |
| LOW | FADE | 15:10 | 108 | ₹-8,814.81 | ₹-238.24 | ₹-508.84 | 35.14% | ₹-20,345.18 |
| MID | FOLLOW | 10:30 | 232 | ₹-54,893.10 | ₹-603.22 | ₹-357.86 | 34.07% | ₹-58,743.13 |
| MID | FOLLOW | 15:10 | 233 | ₹-99,319.54 | ₹-1,091.42 | ₹-1,107.22 | 37.36% | ₹-105,439.90 |
| MID | FADE | 10:30 | 234 | ₹-43,798.44 | ₹-476.07 | ₹-457.24 | 34.78% | ₹-42,448.27 |
| MID | FADE | 15:10 | 234 | ₹-21,908.68 | ₹-238.14 | ₹-552.35 | 42.39% | ₹-50,510.72 |
| HIGH | FOLLOW | 10:30 | 847 | ₹-187,785.78 | ₹-920.52 | ₹-962.48 | 28.43% | ₹-189,063.86 |
| HIGH | FOLLOW | 15:10 | 846 | ₹-136,750.06 | ₹-670.34 | ₹-763.91 | 38.24% | ₹-164,764.55 |
| HIGH | FADE | 10:30 | 847 | ₹-143,360.52 | ₹-702.75 | ₹-714.98 | 29.41% | ₹-142,676.43 |
| HIGH | FADE | 15:10 | 846 | ₹-219,917.84 | ₹-1,078.03 | ₹-1,844.21 | 35.29% | ₹-230,714.61 |

## Execution coverage

All 12 cells cleared the preregistered **95% execution-price coverage** requirement in both Base and Stress.

Coverage ranged from approximately **96.67% to 100.00%** across the cells. The same persisted price-coverage files were used for both friction regimes.

## Null-control analysis

For the best Base true cell (LOW / FADE / 15:10), the true mean weekly net was **₹-114.44**, while its five registered null means ranged from approximately **₹-599.85 to ₹-157.29**. The true value exceeded all five null means, but both the true value and every null value remained economically negative.

For HIGH / FOLLOW / 15:10, the true Base mean was **₹-494.34**, versus five null means ranging from about **₹-789.85 to ₹-604.75**. In Stress the true mean was **₹-670.34**, versus null means ranging from about **₹-930.58 to ₹-747.05**.

These placebo separations are diagnostic rather than promotional: the preregistered absolute economic target was not approached.

## Promotion-gate assessment

The promotion criteria were:
- mean weekly net ≥ ₹5,000;
- median weekly net ≥ ₹5,000;
- ≥70% positive weeks;
- adequate execution coverage;
- both Base and Stress.

**Result: 0/12 cells qualified in Base; 0/12 qualified in Stress.**

The strongest Base cell was still **₹5,114.44/week below** the minimum mean target. The strongest Stress cell was still **₹5,238.14/week below** the minimum mean target.

No WFA, OOS, parameter selection, or trading promotion is authorized.

## Costs and accounting

Every validated trade obeyed:

**net P&L = raw gross − slippage cost − transaction/statutory costs**

For example, the Base LOW/FADE/15:10 cell produced:
- raw gross: **₹12,798.50**
- slippage: **₹4,617.50**
- transaction/statutory costs: **₹12,415.21**
- net: **₹-4,234.21**

The negative outcome is therefore not a missing-cost or unaccounted-friction artifact.

## Statistical interpretation

The study is a finite discovery experiment rather than a final out-of-sample validation. The full sample supports a reproducible rejection of this **specific frozen family** under its declared execution assumptions:

1. The VIX/RV20 regime classification is reproducible and has complete feature coverage after the mandatory warm-up.
2. The gap FOLLOW/FADE rules do not generate sufficient net weekly expectancy.
3. Doubling slippage makes the already-negative results more negative.
4. Some signal cells distinguish themselves from their registered null permutations, but the separation is too small and too negative to satisfy the economic gate.
5. Since no discovery cell clears the gate, further optimization within this family would violate the preregistered stop rule.

## Strengths

- Strict prior-information barrier.
- Official NSE India VIX source with cryptographic provenance.
- Historical NIFTY option execution data cached and pinned.
- Finite preregistered 12-cell grid.
- Full-panel null controls.
- Base/Stress friction testing.
- Historical lot-size schedule.
- Explicit execution coverage.
- Explicit accounting reconciliation.
- No result-driven parameter expansion.

## Limitations

- India VIX is a daily close measure; it does not encode intraday VIX term structure or skew.
- RV20 is a simple realized-volatility estimator.
- The opening gap is measured from NIFTY session prices rather than a richer pre-open/order-book representation.
- One-minute option data does not reconstruct full bid/ask depth or queue position.
- The discovery period is not an untouched OOS sample.
- Only the frozen regime boundaries, two directions and two exits were tested; the family is not an exhaustive search over all VIX/RV formulations.

## Conclusion

**Phase 31.9 is CLOSED as negative discovery evidence.**

The frozen India VIX × RV20 regime × opening-gap directional-spread family does not meet the project's ₹5,000 net/week requirement after realistic transaction costs and Base/Stress slippage. No cell is eligible for WFA/OOS.

The result should be retained because it is informative: it rejects a specific, preregistered mechanism without post-result tuning and demonstrates that regime classification alone did not create adequate option-trading economics.

## Future research

The next research family must be materially distinct and separately preregistered. The project roadmap still permits option-skew/smile dislocations, dealer/gamma proxies, FII/DII/futures positioning with valid time alignment, and hybrid breadth/volatility mechanisms. Any next family must start with a fresh evidence review, data-availability gate, finite grid and null design.

## Reproducibility

Authoritative run: **36334135198**.

Key artifacts:
- `reports/phase31_9/gate/data_gate.json`
- `reports/phase31_9/base/true_cell_summary_base.csv`
- `reports/phase31_9/stress/true_cell_summary_stress.csv`
- `reports/phase31_9/base/null_summary_base.csv`
- `reports/phase31_9/stress/null_summary_stress.csv`
- `reports/phase31_9/base/price_coverage.csv`
- `reports/phase31_9/stress/price_coverage.csv`
- `data/cache/phase31_9_india_vix/manifest.json`

No live-trading recommendation is implied by this discovery result.
