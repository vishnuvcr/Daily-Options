# Phase 3G Results — Dynamic Break + Post-Break OI Confirmation

## Canonical data/run
- Data source: artist-23/nifty-options-data, revision 45e0a04.
- Partitions audited/used: 84 parquet files.
- Raw rows audited: 33,963,731.
- Phase 3G grid: 128 pre-registered variants.
- Initial fast2 run: 35916600082; artifact: 10775362997.
- Corrected fast2 walk-forward run: 35916973751; commit: b499770d36fe06c15b1b3244a8b162cbd43deb22; artifact: 10775388676.
- Accepted raw path artifact contains 79,888 executable candidate trade paths.

## Temporal validity
The accepted Phase 3G artifacts use forward OI confirmation: OI change is measured after the price-structure break and entry occurs only after the confirmation window plus one minute. Earlier runs that used backward-looking OI change are excluded.

## Preliminary leaderboard

### Base friction
- Slippage: 0.20 option-premium points per leg.
- All 128 variants had negative mean calendar-day net.
- Best mean calendar-day net: -Rs 61.11/lot/day.
- Best positive-day rate: about 29.27%.
- Best profit factor: about 0.59.
- Zero variants reached the Rs 1,000/lot/day target.

### Stress friction
- Slippage: 0.40 option-premium points per leg.
- All 128 variants remained negative.
- Best mean calendar-day net: -Rs 79.55/lot/day.
- Best positive-day rate: about 26.74%.
- Best profit factor: about 0.48.
- Zero variants reached the Rs 1,000/lot/day target.

## Corrected walk-forward evaluation
The first artifact's reusable WFA function returned zero windows because it compared Python date objects against timestamp-valued trade_date rows. The function was corrected in commit b499770d36fe06c15b1b3244a8b162cbd43deb22.

The corrected WFA used the immutable path artifact and the same pre-registered selection rule:
- Training window: 180 trading days.
- Validation window: 60 trading days.
- Embargo: 5 trading days.
- Test window: 60 trading days.
- Step: 60 trading days.
- Select the best validation performer from the top-12 training candidates.
- No test-period parameter selection.

### Base friction
- Test windows: 13.
- Positive test windows: 1/13.
- Target-qualified test windows: 0/13.
- Mean test-window net: -Rs 192.79/lot.
- Median test-window net: -Rs 191.13/lot.
- Bootstrap 95% interval for the mean test-window net: approximately [-Rs 268.12, -Rs 117.72].

### Stress friction
- Test windows: 13.
- Positive test windows: 0/13.
- Target-qualified test windows: 0/13.
- Mean test-window net: -Rs 252.79/lot.
- Median test-window net: -Rs 251.13/lot.
- Bootstrap 95% interval for the mean test-window net: approximately [-Rs 328.12, -Rs 177.72].

## Decision
Phase 3G is FAIL_PRELIMINARY and is retired as a lead family.

The result is negative across the full bounded grid, worsens under doubled slippage, and stays negative under leakage-safe walk-forward selection. Because the complete pre-registered family failed before the robustness phase, no additional parameter sweep is permitted.

## Strengths
- Large multi-year option-chain source.
- 128 variants pre-registered before testing.
- Explicit post-break information barrier for OI.
- Date-aware NIFTY lot sizes.
- Brokerage, statutory charges and per-leg slippage included.
- Stress test doubles slippage.
- Walk-forward validation uses train/validation/embargo/test separation.
- Corrected WFA was rerun independently from the immutable path artifact rather than trusting the first empty WFA table.

## Limitations
- Public data are closing-price based rather than full executable bid/ask/depth.
- Volume was quarantined because of source anomalies and was not used.
- The lead-lag hypothesis is tested on this public data source only; the result is not a statement about all NSE option microstructure.
- No live/paper execution is implied by the historical result.

## Next bounded hypothesis
Test derivative price-discovery / option-lead-lag: whether short-horizon ATM call/put price changes contain incremental information about the next 1-5 minute NIFTY spot move, then express only pre-registered directional signals through defined-risk spreads.
