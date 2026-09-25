# Phase 25.1 — Strategy Fidelity Audit

## Purpose
Determine whether the Phase 25 numerical experiment actually tested the user-supplied Falcon strategy before using its negative result to retire the family.

## Finding
The Phase 25 run was a valid execution of the implemented formalization, but that formalization is not sufficiently established as the exact source strategy. Therefore the Phase 25 negative result must be treated as formalization-specific, not as a definitive Falcon-strategy result.

## 1. What Phase 25 actually tested

- Sell 5 near-expiry CE + 5 near-expiry PE.
- Buy 3 next-expiry CE + 3 next-expiry PE.
- Near legs were selected as the option closes closest to a target premium of 20/25/30.
- In the DIAGONAL_PREMIUM interpretation, far-week legs were selected independently to be closest to the same target premium while constrained outward from the near-week strikes.
- The adjustment bought 5 near-expiry CE one listed strike above the original short call and 5 near-expiry PE one listed strike below the original short put.
- Stop thresholds were 0.5×, 1.0× and 1.5× initial gross credit.
- Entry times were 09:30, 10:00, 11:00, 13:00 and 14:00.
- Adjustment times were 09:30, 10:00 and 11:00.
- Entry/adjustment signals used the minute close and execution the next minute open.
- Expiry-relative timing was expiry−4 sessions / expiry−3 sessions / expiry−1 session.

This is a broad experimental formalization, not a single uniquely established source rule.

## 2. Critical evidence that the 270-cell family was not fully tested

The frozen grid contains 270 cells: 5 entry times × 3 premium targets × 2 far modes × 3 adjustment times × 3 stops = 270.

However, the Base and Stress leaderboards each contain only 135 variants. All 135 missing variants are SAME_STRIKE variants.

- 135 DIAGONAL_PREMIUM variants produced trades.
- 135 SAME_STRIKE variants produced no executable setup/trade rows.
- The statement that all 270 variants were loss-making is therefore incorrect.
- The correct statement is that the 135 executable DIAGONAL_PREMIUM variants were negative in this run; the SAME_STRIKE interpretation was not tested numerically by the artifact because it produced no leaderboard entries.

## 3. Source-fidelity ambiguity: far-week strike relationship

The repository source catalogue explicitly says the transcript does not establish whether the 3-lot far-week options use the same strikes as the 5-lot near-week shorts or independently selected strikes at approximately the same premium.

Phase 24/25 chose the second interpretation (DIAGONAL_PREMIUM) and retained same-strike only as a sensitivity. That is a modelling choice, not a demonstrated source fact.

Because this choice changes the payoff, vega, delta and tail shape materially, a negative DIAGONAL_PREMIUM result cannot be used to reject an exact SAME_STRIKE Falcon implementation.

## 4. Source-fidelity ambiguity: hard stop

The source material available in the repository says a hard stop is required but does not provide the numerical threshold. Phase 25 therefore tested 0.5/1.0/1.5× initial gross credit.

Those thresholds are experimental formalizations, not recovered source parameters. The exact stop rule is therefore a strategy-definition issue, not merely an optimization parameter.

## 5. Source-fidelity ambiguity: timing

The source catalogue states Friday entry / Monday adjustment / Wednesday exit for the historical Thursday-expiry regime but does not specify an exact intraday entry or adjustment clock. Phase 25 therefore tested five entry times and three adjustment times.

This is a sensitivity study around an incompletely specified source rule, not proof of the exact timing used by the presenter.

## 6. Expiry regime mixing

The Rissin sample contains both Thursday-expiry historical contracts and Tuesday-expiry contracts after the NIFTY weekly-expiry change. The implementation correctly used expiry-relative session offsets for the translation, but the result should still be reported separately by expiry regime.

For the best executable Base cell (09:30 | p25 | DIAGONAL_PREMIUM | adj11:00 | stop0.5):
- Thursday-expiry trades: 33, total net approximately -₹46,238.
- Tuesday-expiry trades: 12, total net approximately -₹27,828.

This does not rescue the strategy, but it shows the negative aggregate was not solely produced by mixing the regimes.

## 7. What can be concluded

The Phase 25 run establishes only this:

The specific premium-matched outward-diagonal formalization, with the tested timing grid and 0.5/1.0/1.5× gross-credit stop grid, was unprofitable after the repository cost and slippage model on the pinned 2024–2025 Rissin sample.

It does not establish that the exact Falcon strategy from the video is unprofitable.

## 8. Required correction before any Falcon retirement

No result-driven optimization is allowed.

The next research step is source-fidelity reconstruction, not another leaderboard search:
1. Recover the exact far-week strike rule from the original video/transcript: same strike, fixed strike offset, premium-matched strike, or another explicit relation.
2. Recover the actual hard-stop definition.
3. Recover whether the adjustment is time-based or condition-based.
4. Freeze the exact entry and adjustment execution convention.
5. Unit-test the exact leg structure.
6. Rerun the exact rule on the independent Rissin data.
7. Only after that, evaluate Base/Stress and decide whether WFA/OOS is warranted.

## Status

Phase 25 retirement is suspended.

The numerical artifact is preserved as an experiment on one formalization. Falcon remains an unresolved strategy hypothesis pending fidelity correction.