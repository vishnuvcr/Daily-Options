# Status — Alternating OTM Buy/Sell Phase C

Branch: research/alternating-otm-phase-c-tail-filter-v1

Current status: **CLOSED — WIN RATE IMPROVEMENT CONFIRMED, FRiction-ROBUST PROFITABILITY NOT CONFIRMED**

Authoritative workflow: **36536840710**

Parent baseline workflow: 36535251511

Phase objective: identify one simple pre-entry tail-loss exclusion rule from discovery data only, then validate that frozen rule on the untouched 2025+ holdout.

## Execution

- Discovery: 861 trades through 2024-12-31.
- Holdout: 348 trades from 2025-01-01 onward.
- Candidate grid: 4 features × 5 discovery quantiles = 20 rules.
- Selected rule: first15_abs_ret >= 0.126795%, corresponding to the 45th discovery percentile.
- Selection used discovery only; no holdout metric was used to choose the rule.

## Holdout result

Base:
- 209 trades from 348 baseline trades.
- Win rate 63.16% versus 60.06% unfiltered.
- Net P&L +₹34,446 versus -₹24,907 unfiltered.
- Profit factor 1.133.
- Max drawdown -₹52,806.

Stress:
- 209 trades.
- Win rate 60.29% versus 57.47% unfiltered.
- Net P&L -₹1,518 versus -₹85,003 unfiltered.
- Profit factor 0.994.
- Max drawdown -₹63,074.

## Interpretation

The selected rule removes a large portion of tail-loss exposure and materially improves both win rate and economics. However, the doubled-slippage Stress holdout remains slightly negative, and the 2026 holdout segment is negative under both frictions.

Therefore the rule is **not promoted as a trading strategy**.

The adjacent 40th-percentile sensitivity is positive in both Base and Stress on 2025+ (+₹52,253 / +₹12,353), but it is not a valid new selection because the 2025+ holdout has already been used for validation. No threshold retuning on this holdout is authorized.

## Next research gate

A subsequent phase must use a genuinely new validation design or a new untouched time period. Reusing the 2025+ holdout to choose 0.40 instead of the discovery-selected 0.45 threshold is prohibited.

Full result: reports/alternating_otm_phase_c_result.md
