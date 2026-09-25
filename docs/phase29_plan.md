# Phase 29 — Historical data feasibility

## Objective

Evaluate whether the current public/cached data sources can support each canonical Equity Income candidate without look-ahead or hidden survivorship assumptions.

## Current verified source set

- NSE contract specifications and historical reports
- TradeMarkk 1-minute NIFTY/BANKNIFTY/SENSEX options source with strike/option_type/expiry and OI schema
- Rissin 1-minute NIFTY/BANKNIFTY/SENSEX intraday source for independent price validation
- NSE India VIX history
- NSE FII/FPI and DII reports
- Paytm Money current brokerage calculator/tariff verification path

## Feasibility states

- PRELIMINARY_FEASIBLE: public 1-minute source path exists, but strategy-specific quote/expiry/lot-size validation is still required.
- DATA_LIMITED: required underlying/tenor is not yet proven in the cached 1-minute source set.
- UNRESOLVED: canonical payoff requirement is not yet stable enough to map to a data requirement.

## Hard gate

No row is backtest eligible in Phase 29. Historical lot sizes, contract expiry identity and per-strategy quote completeness must be validated before Phase 30.

## Cost model inputs

Official NSE levies are verified from the current NSE fee page; Paytm Money brokerage/platform/depository/auto-square-off charges must be live-verified at the start of numerical testing rather than copied from historical marketing pages.

## Output

- reports/phase29_data_feasibility.csv
- reports/phase29_summary.json
- data/equity_income/phase29_source_manifest.json