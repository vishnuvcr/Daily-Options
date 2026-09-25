# Phase 29.1 — Data-readiness verification

## Purpose

Deepen Phase 29 from source-capability mapping to deterministic source-readiness checks without starting trading P&L.

## Research questions

1. Do the pinned public sources actually expose the index-option and independent-validation partitions required by the 71 Equity Income candidate rows?
2. Which candidate families are structurally data-limited because they require stock options, long-dated/LEAPS continuity, or other fields not verified in the pinned 1-minute sources?
3. Which execution inputs are verified versus still dependent on strategy-specific contract joins, historical lot-size tables, and quote-quality assumptions?
4. Can the research proceed to numerical testing without treating OHLC bars as bid/ask quotes or using future information?

## Scope

No strategy parameters are tuned and no P&L is computed in Phase 29.1. The output is a reproducible data-readiness matrix that feeds the existing Phase 30 gate.

## Frozen source pins

- TradeMarkk thetrademarkk/india-index-options-1m, revision 51ca58c.
- Rissin rissin/nse-options-intraday, revision 78b1c5468255d18cf492984bfe6fe4e3ac874d7c.
- NSE contract/circular sources for expiry and market-lot verification.

## Methodology

1. Read strategy_families.csv from the Phase 28 branch copy used by the Phase 29 workflow.
2. Query the Hugging Face dataset tree at the exact frozen revisions; never use main for the readiness decision.
3. Verify deterministic partition existence for NIFTY/BANKNIFTY/SENSEX index options and the Rissin independent year partitions.
4. Record published schema capabilities and explicitly separate OHLC availability from executable bid/ask availability.
5. Flag intraday OI dependence: TradeMarkk exposes OI in its option schema; Rissin's Upstox intraday track documents OI as unavailable/NaN.
6. Verify the currently applicable NIFTY weekly-expiry convention and date-versioned historical lot-size milestones from official NSE circulars; do not back-project the current weekday or lot size across the historical sample.
7. Produce one row per candidate with readiness status, blocking requirement and backtest permission. Every row remains backtest_allowed=NO until strategy-specific quote completeness and contract-level lot/expiry validation are proven.

## Gate to Phase 30

A candidate can leave the Phase 29 gate only when all economically material fields for its source-faithful rule are verified: contract identity, expiry regime, historical lot size, required option fields, sufficient quote coverage, and an executable-price proxy that does not use future information. OHLC-only sources remain eligible for research only through an explicitly documented slippage model; they are not treated as bid/ask data.

## Outputs

- reports/phase29_readiness_matrix.csv
- reports/phase29_readiness_summary.json
- data/equity_income/phase29_readiness_source_inventory.json
- docs/phase29.1_data_readiness_plan.md

## Stop condition

Stop Phase 29.1 after the readiness matrix, official lot/expiry evidence, and reproducibility manifest are complete. Do not convert data limitations into strategy conclusions and do not launch Phase 30 from this stage unless the explicit gate is satisfied.
