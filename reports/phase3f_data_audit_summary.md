# Phase 3F Data Audit Summary

Dataset: `artist-23/nifty-options-data`
Pinned revision: `45e0a04`
Audit run: GitHub Actions `35906761397`

| Field | Result |
|---|---|
| Parquet files | 84 |
| Rows | 33,963,731 |
| Date range | 2020-12-29 to 2025-12-26 |
| Unique dates | 1,228 |
| IV non-null | 100% |
| OI non-null | 100% |
| Volume non-null | 100% |
| Spot non-null | 100% |
| Option types | CALL, PUT |
| Expiry types | MONTH, WEEK |
| Strike types | ATM-10 through ATM+10 |
| Negative volume rows | 16 |
| Negative OI rows | 0 |
| Non-positive spot rows | 0 |
| Non-positive strike rows | 0 |
| Non-positive close rows | 0 |
| Invalid OHLC rows | 0 |
| IV > 300 observations | 485 |

## Data-quality decision

The 16 negative-volume rows are retained in the raw cache but converted to null before volume aggregation. They represent a tiny fraction of the source but have implausibly large negative magnitudes; the field remains provisional until an independent reconciliation is available.

IV values above 300 are not treated as automatically invalid because several occur in near-expiry/monthly near-ATM observations. Strategy features use an IV cap of 300 for the ATM IV aggregate, and the raw values remain available for later investigation.

The audit therefore passes schema/core numerical integrity but remains marked **QUARANTINE_DATA_QUALITY** for the volume field.
