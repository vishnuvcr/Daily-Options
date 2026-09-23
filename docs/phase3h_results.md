# Phase 3H Results — Short-Horizon ATM Option Lead-Lag

## Canonical run
- Branch: phase-3h-option-lead-lag.
- GitHub Actions run: 35918302989.
- Commit: 64abd09e74e5a209b461f86efef4d41a91478681.
- Artifact: 10775828210.
- Dataset: artist-23/nifty-options-data revision 45e0a04.
- Feature rows: 438,043.
- Signal rows: 132,078.
- Executable entries/trades: 132,072.
- Pre-registered variants: 108.
- Volume was not used because the source volume field remains quarantined.

## Base-cost result
- Slippage: Rs 0.20 option-premium points per leg.
- All 108 variants had negative mean calendar-day net.
- Best mean calendar-day net: Rs -181.83/lot/day.
- Best profit factor: 0.312.
- Best trade win rate: 26.08%.
- Best variant: WEEK expiry, 3-minute lookback, 3% pressure threshold, 2-strike width, 10-minute hold.
- Corrected nested walk-forward: 16 test windows.
- Positive test windows: 0/16.
- Target-qualified test windows: 0/16.
- Mean test-window net: Rs -191.39/lot.
- Median test-window net: Rs -183.43/lot.
- Mean positive-day rate across test windows: 17.71%.
- 95% bootstrap interval for the mean test-window net: approximately [Rs -214.70, Rs -169.35].

## Stress-cost result
- Slippage: Rs 0.40 option-premium points per leg.
- All 108 variants remained negative.
- Best mean calendar-day net: Rs -241.83/lot/day.
- Best profit factor: 0.223.
- Best trade win rate: 21.18%.
- Corrected nested walk-forward: 16 test windows.
- Positive test windows: 0/16.
- Target-qualified test windows: 0/16.
- Mean test-window net: Rs -251.39/lot.
- Median test-window net: Rs -243.43/lot.
- Mean positive-day rate across test windows: 13.65%.
- 95% bootstrap interval for the mean test-window net: approximately [Rs -274.70, Rs -229.35].

## Lead-lag diagnostic
The signal-level diagnostic was deliberately separated from trading P&L. Conditional next-1/3/5-minute spot hit rates were only modestly directional rather than persistently strong:
- Across all tested lookback/threshold combinations, forward 1-minute directional hit rates ranged about 46.8%–56.1%.
- Forward 3-minute rates ranged about 48.7%–54.9%.
- Forward 5-minute rates ranged about 47.97%–53.13%.
- The strongest isolated 3-minute diagnostic was a 3-minute lookback / 1% threshold PUT signal with mean forward 3-minute spot move about -0.0106%, but its corresponding 3-minute directional hit rate was only about 52.2%.
This diagnostic does not support treating the option-pressure signal as a stable forecasting edge.

## Decision
Phase 3H FAIL_PRELIMINARY and retired.

No 108-variant expansion is permitted. The failure is present before robustness testing, remains negative after doubled slippage, and is negative in every untouched walk-forward test window.

## Engineering/provenance
The initial implementation had two pre-result engineering defects:
- E0043: identical executable setups were deduplicated without remapping path results to all parameter variants; fixed before accepted statistics.
- E0044: a new phase-specific cache key would have forced redundant dataset download; fixed by reusing the repository pinned-data cache.
No numerical result from pre-correction runs was accepted.

## Strengths
- 108 variants were pre-registered before numerical evaluation.
- All signal features used information available at or before signal time.
- Entry was delayed to the next executable minute with a two-minute execution tolerance.
- Defined-risk debit spreads limited payoff exposure.
- Date-aware NIFTY lot size and project transaction-cost model were used.
- Base and 2x-slippage runs were both executed.
- Nested train/validation/embargo/test WFA prevented final-test parameter selection.
- Predictive diagnostics were separated from execution P&L.

## Limitations
- The public data use closing prices rather than executable bid/ask/depth.
- The ATM label is time-varying, so the common ATM call/put feature is not a fixed-strike market-maker quote series.
- Historical option volume remains quarantined because of source anomalies.
- The lead-lag test is specific to this data source and specification; it does not establish that no derivative lead-lag effect exists under every market-data representation.
- No live or paper execution is implied.

## Next research direction
Move to a materially different regime-conditioned underlying-price family rather than another option-microstructure permutation. The next bounded candidate should use intraday price dislocation/mean-reversion or opening-range regime information, expressed with defined-risk spreads and the same cost-aware WFA gate.
