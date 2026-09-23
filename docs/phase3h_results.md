# Phase 3H Results — Option Price Lead/Lag

## Canonical run

- Branch: `phase-3h-option-lead-lag`
- GitHub Actions run: 35918302989
- Head SHA: 64abd09e74e5a209b461f86efef4d41a91478681
- Accepted artifact: 10775828210
- Artifact SHA-256: 5478fa383b8d70a84944259e7ed4987414b684d4cf5c206b13861babf64c7c17
- Data source: `artist-23/nifty-options-data`
- Pinned revision: `45e0a04`
- Pre-registered variants: 108
- Feature rows: 438,043
- Signals: 132,078
- Executable entries: 132,072
- Simulated trades: 132,072
- Volume used: no

## Base friction — 0.20 option-premium points per leg

- All 108 variants had negative mean calendar-day net P&L.
- Best mean calendar-day net: **-Rs 181.83/lot/day**.
- Best configuration: WEEK expiry, 3-minute option-pressure lookback, 3% pressure threshold, 2-strike width, 10-minute hold.
- Best configuration: 1,223 trade-days, 21.50% positive days, 21.50% trade win rate, PF 0.254, max drawdown about -Rs 222,520/lot, total net about -Rs 222,382.
- Highest profit factor observed in the grid: about 0.312; it was still negative in mean net P&L.
- Target-qualified variants: 0/108.

## Stress friction — 0.40 option-premium points per leg

- All 108 variants remained negative.
- Best mean calendar-day net: **-Rs 241.83/lot/day**.
- The same WEEK/3-minute/3%/2-strike/10-minute configuration remained the top mean-net variant.
- Best configuration positive-day rate: 16.84%; PF 0.172; max drawdown about -Rs 295,660/lot; total net about -Rs 295,762.
- Target-qualified variants: 0/108.

## Forward lead-lag diagnostic

The feature-only diagnostic is economically weak and unstable:

- 1-minute option-pressure signals produced roughly 48%–53% directional hit rates at the first 1–5 minute horizons, with mean forward spot returns close to zero.
- 3-minute pressure showed some directional asymmetry in the raw diagnostic, but the sign and horizon were not stable across thresholds/directions.
- 5-minute pressure remained mixed and close to zero.
- The diagnostic therefore does not show a stable, execution-worthy option-to-spot lead that survives the option spread implementation.

## Nested walk-forward

The leakage-safe selection rule used 180 training days, 60 validation days, a 5-day embargo, 60 test days and a 60-day step. Parameters were selected only from training/validation.

### Base friction

- Test windows: 16
- Positive test windows: **0/16**
- Target-qualified test windows: **0/16**
- Mean test-window net: **-Rs 191.39/lot**
- Median test-window net: **-Rs 183.43/lot**
- 20,000-resample bootstrap percentile 95% interval for the mean test-window net: **[-Rs 214.99, -Rs 169.40]**

### Stress friction

- Test windows: 16
- Positive test windows: **0/16**
- Target-qualified test windows: **0/16**
- Mean test-window net: **-Rs 251.39/lot**
- Median test-window net: **-Rs 243.43/lot**
- 20,000-resample bootstrap percentile 95% interval: **[-Rs 274.99, -Rs 229.40]**

## Decision

**Phase 3H FAIL_PRELIMINARY; retire the option-price lead/lag family.**

The entire pre-registered family is negative after realistic costs, every walk-forward test window is negative, the bootstrap intervals exclude zero, and doubled slippage worsens the outcome. The Phase 3H stop rule therefore forbids parameter-grid expansion or post-hoc threshold tuning.

## Strengths

- Multi-year, 84-parquet-partition public option dataset pinned to a reproducible revision.
- 108-variant family pre-registered before the accepted run.
- Signal construction uses only contemporaneous or lagged option prices; forward spot returns are diagnostic only.
- Next-executable-minute entry with a two-minute execution budget.
- Defined-risk debit spreads rather than naked option buying.
- Date-aware NIFTY lot sizes and project cost model.
- Base and doubled-slippage runs.
- Nested train/validation/embargo/test walk-forward selection.
- Bootstrap uncertainty reported on the selected test-window means.

## Limitations

- Public option data are closing-price based rather than true bid/ask/depth.
- ATM feature rows can be affected by sparse contract timestamps.
- The phase establishes a negative result for this bounded option-pressure family; it does not prove that every derivative microstructure signal is uninformative.
- No live/paper execution claim is made.

## Research implication

The failed Phase 3H result shifts the next bounded experiment away from option-to-spot price pressure and toward a more direct market-price discovery variable: **NIFTY futures versus NIFTY spot lead-lag**.

Indian intraday studies using one-minute and five-minute data have repeatedly reported a meaningful role for NIFTY futures in price discovery, although the exact direction and strength vary by sample and method. This makes the futures-to-spot relationship testable rather than assumed.

## Next bounded hypothesis

Phase 3I should test whether short-horizon NIFTY-futures returns, basis changes and futures-versus-spot divergence contain incremental information about the next few minutes of NIFTY spot returns, then express only pre-registered signals through defined-risk option spreads. The data gate must first verify historical 1-minute futures coverage, contract rollover handling, timestamps, volume/OI fields and session completeness before any strategy optimization.
