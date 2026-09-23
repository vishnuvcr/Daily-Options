# Phase 3I Results — Opening-Range False-Break Mean Reversion

## Canonical run
- GitHub Actions run: 35919447949.
- Accepted commit: 86b6b50860af90d4f64e7591e992dc5e8fffba87.
- Artifact: 10777830090.
- Dataset: artist-23/nifty-options-data revision 45e0a04.
- Spot feature rows: 404,235.
- Signal rows: 119,196.
- Executable entries/trades: 118,860.
- Pre-registered variants: 144.
- Base and stress P&L were computed from the same trade-path artifact.

## Base friction
- Slippage: 0.20 option-premium points per leg.
- Positive variants by mean calendar-day net: 0/144.
- Variants with profit factor > 1: 0/144.
- Best mean calendar-day net: Rs -854.06/lot/day.
- Best configuration: 30-minute opening range, 0.10% break excursion, 0.05% re-entry, WEEK expiry, 1-strike width, 60-minute hold.
- Best profit factor: 0.0357.
- Best trade win rate: 20.05%.
- Best positive-day rate: 15.28%.
- Least-negative max drawdown among variants: about Rs -1.045 million/lot.
- Corrected WFA: 14 test windows.
- Positive test windows: 0/14.
- Target-qualified test windows: 0/14.
- Mean test-window net: Rs -1,626.99/lot.
- Median test-window net: Rs -1,684.55/lot.
- Mean positive-day rate across test windows: 9.38%.
- Bootstrap 95% interval for mean test-window net: approximately [Rs -1,697.91, Rs -1,553.48].

## Stress friction
- Slippage: 0.40 option-premium points per leg.
- Positive variants by mean calendar-day net: 0/144.
- Variants with profit factor > 1: 0/144.
- Best mean calendar-day net: Rs -886.27/lot/day.
- Same best configuration as base friction.
- Best profit factor: 0.0312.
- Best trade win rate: 18.64%.
- Best positive-day rate: 13.73%.
- Least-negative max drawdown among variants: about Rs -1.085 million/lot.
- Corrected WFA: 14 test windows.
- Positive test windows: 0/14.
- Target-qualified test windows: 0/14.
- Mean test-window net: Rs -1,686.99/lot.
- Median test-window net: Rs -1,744.55/lot.
- Mean positive-day rate across test windows: 7.17%.
- Bootstrap 95% interval for mean test-window net: approximately [Rs -1,757.91, Rs -1,613.48].

## Event-level diagnostic

The intended reversal mechanism did not appear in the forward spot diagnostics:
- Downside false-break -> CALL signals had mean forward spot returns of about -0.0005% at 15 minutes, +0.0083% at 30 minutes and +0.0107% at 60 minutes.
- Upside false-break -> PUT signals had mean forward spot returns of about -0.0037%, -0.0016% and -0.0064% at 15/30/60 minutes.
- Correct-direction hit rates were about 48.8% at 15 minutes, 50.0% at 30 minutes and 50.9% at 60 minutes.

The signal therefore did not exhibit a stable reversal edge in the underlying, and the defined-risk option expression lost heavily after costs.

## Decision

Phase 3I is FAIL_PRELIMINARY and RETIRED.

This is the final exploratory family under the current public dataset. No additional threshold widening, feature insertion, expiry selection or parameter sweep is permitted.

## Strengths
- Final exploratory family was pre-registered at 144 variants.
- Information barrier was explicit: opening range and false-break state use only data available before signal time; entry is delayed one minute.
- Costs, date-aware lot sizes and doubled slippage were included.
- Nested train/validation/embargo/test WFA prevented test-period parameter selection.
- Event diagnostics were separated from option P&L.

## Limitations
- Historical option data are close-based rather than executable bid/ask/depth.
- Source volume was quarantined because of known anomalies.
- The false-break event was constructed from the dataset's spot field, not from a licensed primary-index tape.
- Severe negative results on this specification should not be interpreted as proof that every opening-reversal strategy is impossible in live markets.

## Phase 3 conclusion

Across the bounded Phase 3/3F/3G/3H/3I families tested in this project, no strategy has cleared the promotion gates after costs and leakage-safe walk-forward validation. The program therefore moves to final synthesis rather than continued parameter mining.
