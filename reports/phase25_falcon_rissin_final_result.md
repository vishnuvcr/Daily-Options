# Phase 25 — Falcon Spread Independent Rissin Replication — Final Result

## Provenance

- Workflow run: **36111174510**
- Branch: `phase-25-falcon-rissin-independent-v1`
- Head: `13cd66bd622f91eb1afb5984d8954e1d67c1f84d`
- Independent source: pinned Rissin `nse-options-intraday`, revision `78b1c5468255d18cf492984bfe6fe4e3ac874d7c`
- Research period: 2024-10-01 to 2025-12-31
- Frozen variants: **270**
- Base slippage: **0.20 premium points/order**
- Stress slippage: **0.40 premium points/order**
- Costs: Paytm Money order charges plus date-aware NSE transaction charges, STT, SEBI fee, stamp duty and GST

## Data and execution integrity

Both Base and Stress jobs completed successfully. All 7 unit tests passed. The pinned source coverage gate passed with **84,280,469 1-minute rows, 311 trading dates and 76 expiries**.

The executable simulation produced **680 frozen-rule setups, 47 distinct entry dates and 6,120 trade records**. Every one of the 270 variants was loss-making on the active-day net metric in both friction settings.

No post-result parameter changes were made.

## Base friction

Best frozen variant:
`09:30:00|p25|DIAGONAL_PREMIUM|adj11:00:00|stop0.5`

- Trades: **45**
- Win rate: **33.33%**
- Total net: **-₹74,066.24**
- Mean active-day net: **-₹1,645.92/lot/day**
- Median active-day net: **-₹1,683.06/lot/day**
- Target-qualified variants: **0/270**
- Positive-mean variants: **0/270**

## Stress friction

The same frozen variant remained the least-negative cell:

- Trades: **45**
- Win rate: **28.89%**
- Total net: **-₹99,866.24**
- Mean active-day net: **-₹2,219.25/lot/day**
- Median active-day net: **-₹2,315.07/lot/day**
- Target-qualified variants: **0/270**
- Positive-mean variants: **0/270**

The complete leaderboard is retained in the workflow artifacts.

## Decision

**Phase 25 is retired.**

The independent Rissin replication does not support the frozen Falcon Spread as a viable cost-adjusted intraday strategy over the tested 2024–2025 sample. The result is not a small miss around the ₹1,000 target: the best cell is materially negative in both Base and Stress, and no alternative cell in the 270-cell frozen family has positive mean active-day net.

Because the independent replication is negative across the entire preregistered family, the Falcon family is **not promoted to WFA/OOS** and no result-driven tuning of Falcon parameters is permitted.

## Research consequence

The research now moves to the next distinct hypothesis rather than spending additional phases narrowing the failed Falcon parameter family. The same cost/slippage framework, independent-data validation discipline and no-post-result-tuning rule remain in force.


## RETRACTION — 2026-09-25

This document's earlier Phase 25 numerical decision is **RETRACTED**. A forensic code audit found that the Phase 25 simulator's pre-adjustment stop scan extended beyond the adjustment timestamp and that its pre-stop cache key omitted adjustment time. This means the reported P&L did not faithfully implement the documented Falcon adjustment sequence. The report also treated a nominal 270-cell grid as if all 270 variants were executable, while only 135 variants appeared in the produced leaderboard.

The numerical values above are retained only as an audit record of the invalid run. They must not be interpreted as evidence that Falcon is unprofitable or that the family should be retired. The corrected simulator is being rerun on the same pinned independent Rissin data with unchanged strategy rules.
