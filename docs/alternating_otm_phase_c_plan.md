# Alternating OTM Buy/Sell — Phase C Frozen Tail-Loss Filter Plan

## Research question

Can a simple pre-entry exclusion rule remove the large-tail losing trades of the alternating OTM1/2xOTM2 structure while preserving its higher win rate and materially improving net expectancy after Base and Stress transaction costs?

## Data split

- Discovery: 2021-07-01 through 2024-12-31, using the already-completed authoritative alternating baseline artifact from workflow 36535251511.
- Untouched holdout: 2025-01-01 onward.
- The holdout is not used to choose the feature, direction, threshold, or rule.

## Pre-entry candidate family

Only information known by the 09:30 reference is permitted.

Four registered one-factor tail-risk filters are tested:

1. first15_abs_ret >= discovery_quantile
2. gap_abs_pct <= discovery_quantile
3. prior20_median_range_pct <= discovery_quantile
4. prior_day_range_pct <= discovery_quantile

Quantiles tested: 0.30, 0.35, 0.40, 0.45, 0.50.

A candidate is eligible for selection only when it retains at least 50% of discovery trades and improves total discovery net P&L versus the unfiltered alternating baseline in both Base and Stress.

## Frozen selection rule

Among eligible candidates, select the rule with the highest mean of the Base and Stress discovery net-P&L improvement. Tie-breaks, in order:

1. larger minimum improvement across Base and Stress;
2. higher retained-trade proportion;
3. higher mean discovery win rate across Base and Stress.

No holdout metric participates in selection.

## Validation

Apply the single selected rule unchanged to the 2025+ holdout and report:

- trade count and retained share;
- win rate;
- gross P&L, transaction costs and net P&L;
- mean and median net P&L per trade;
- profit factor;
- maximum drawdown;
- maximum loss;
- annual 2025/2026 breakdown;
- comparison with the unfiltered alternating holdout baseline.

A selected rule is not considered promotion-ready unless the holdout evidence is economically and friction robust. In particular, a higher win rate alone is not sufficient.

## Execution and accounting

The input is the exact Base/Stress trade output from authoritative workflow 36535251511. No option prices are reconstructed, no new market download is performed, and no post-entry variable is used in the filter. All existing Paytm Money/NSE/statutory cost assumptions and Base/Stress slippage remain frozen.

## Phase boundary

If the selected rule does not survive the untouched holdout under both friction regimes, Phase C closes as negative/insufficient and no further threshold tuning is permitted on the same holdout. A later research phase may test a separately preregistered mechanism, but it cannot recycle the 2025+ holdout for selection.
