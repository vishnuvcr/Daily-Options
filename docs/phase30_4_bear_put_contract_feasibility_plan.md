# Phase 30.4 — Bear Put contract/data feasibility

## Objective
Establish the current and historical NIFTY contract geometry, lot-size transition, and cached 1-minute data availability needed for a later Bear Put numerical test.

## Source-backed contract facts
- NSE currently lists NIFTY 50 index options with four weekly expirations plus monthly expirations; the expiry day is Tuesday, or the previous trading day when Tuesday is a trading holiday.
- NSE's October 3, 2025 lot-size circular revised NIFTY from 75 to 65. The revision took effect for new contracts after the transition period; existing weekly/monthly contracts remained on the old lot through the December 30, 2025 expiry.
- Therefore, for the Falcon/Bear-Put research data window beginning September 1, 2025, the source-backed lot schedule for ordinary weekly NIFTY expiries is:
  - 75 for expiries through December 30, 2025;
  - 65 from January 6, 2026 onward.

## Data source
The Rissin `nse-options-intraday` dataset provides NIFTY 1-minute Parquet data from October 2024 onward, with contract expiry, strike, option type, OHLC, and timestamp fields. The completed Falcon run pinned the dataset revision at workflow runtime and acquired `NIFTY_2025.parquet` and `NIFTY_2026.parquet`.

## Hard gate
This phase does **not** authorize Bear Put P&L testing because the source phase still has unresolved:
- expiry selection;
- exact resistance definition;
- crack/gap-down trigger;
- exact stop-loss;
- exact exit/time-out;
- universal strike/debit rule.

## Acceptance tests for later numerical phase
1. Exact expiry join has no duplicate or missing contract keys.
2. Historical lot size is assigned from dated contract rules, not inferred from current data.
3. Entry/adjustment timestamps are normalized to Asia/Kolkata.
4. Contract price rows exist at all required decision and next-minute execution timestamps, or the strategy explicitly records no-trade for missing data.
5. The numerical engine never substitutes a later quote for an earlier missing decision quote without a registered tolerance rule.

## Status
Contract/data feasibility: **READY**
Strategy numerical authorization: **BLOCKED by source-rule resolution**
