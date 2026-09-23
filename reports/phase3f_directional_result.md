# Phase 3F Directional Microstructure Screen — Result

Run: GitHub Actions `35906761397` (2026-09-24 UTC)
Dataset: `artist-23/nifty-options-data`, revision `45e0a04`
Source rows audited: 33,963,731 across 84 parquet files.
Feature rows at selected entry times: 7,303.
Raw option rows used by the screen: 15,390,804.

## Screen

Signals combined:
- near-ATM call/put OI imbalance;
- near-ATM call/put volume imbalance;
- 15-minute spot return;
- ATM IV / 15-minute realized-volatility ratio.

Execution:
- signal at time t;
- entry at t+1 minute;
- ATM-to-OTM debit spread;
- widths 1 and 2 strikes;
- 30/60/90-minute holds;
- one candidate trade per day/expiry/parameter tuple;
- ₹20/order brokerage, exchange/SEBI/STT/stamp/GST model and 0.20-point slippage.

972 parameter/structure variants were evaluated. The ₹1,000 net/day target was not reached.

## Best preliminary configuration

| Metric | Value |
|---|---:|
| Expiry type | MONTH |
| Width | 2 strikes |
| Hold | 30 min |
| OI imbalance threshold | 0.20 |
| Volume imbalance threshold | 0.20 |
| 15-min return threshold | 0.10% |
| IV/RV minimum | 1.25 |
| Trades | 92 |
| Active days | 92 |
| Calendar days | 1,223 |
| Mean active-day net | -₹234.26 |
| Mean all-day net | -₹17.62 |
| Median trade | -₹202.89 |
| Trade win rate | 16.30% |
| Positive-day rate | 1.23% |
| Profit factor | 0.148 |
| Total net | -₹21,551.59 |
| Max drawdown | -₹21,379.94 |

## Decision

**FAIL_PRELIMINARY.** No variant qualified for the ₹1,000/day target.

The directional IV/OI/volume imbalance hypothesis is not promoted. The next Phase 3F experiment is a defined-risk short-volatility/iron-fly regime screen using the same audited IV/OI fields, because continuing to tune this directional family would be low-value after the multi-year screen failed.
