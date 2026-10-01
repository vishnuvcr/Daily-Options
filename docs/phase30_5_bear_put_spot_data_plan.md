# Phase 30.5 — Bear Put underlying spot-data validation

## Purpose
Provide a reproducible 1-minute NIFTY 50 spot series for the Bear Put resistance/crack/gap-down interpretation grid.

## Source candidates reviewed
1. **Technovus nifty50-historical-data** — public GitHub repository, MIT-licensed, 1-minute NIFTY50 OHLC. Its README states full-year 2018–2025 coverage and 2026 coverage from January 1. The current audited commit is `75f273a2dec36b10f4ded3a00721fae2172edccb` (2026-09-25).
2. **beingRajat/data-scraping** — uses Yahoo Finance, but documents that free Yahoo 1-minute history is limited to the most recent 7 days; therefore it is not suitable for the 2025–2026 historical study window. It remains a provenance reference only.
3. **Rissin nse-options-intraday** — excellent for option contracts but its schema is option-only (CE/PE, strike, expiry); it does not provide the NIFTY cash index series needed to define price-action resistance.

## Decision
Use Technovus spot OHLC as the primary historical underlying series, pinned to commit `75f273a2dec36b10f4ded3a00721fae2172edccb`.

## Validation gates
- 1-minute timestamps normalize to Asia/Kolkata.
- OHLC integrity: high >= max(open, close, low), low <= min(open, close, high).
- No duplicate timestamp rows.
- No impossible negative/zero index prices.
- Trading-day coverage overlaps every NIFTY weekly expiry calendar in the 2025-09 to 2026-08 research window.
- The spot data's daily first/last bars are retained for audit.
- Missing intraday bars are reported, not forward-filled through signal generation.
- External source commit, file hashes and byte counts are stored in a manifest.

## Research boundary
This phase does not assign a resistance rule, crack threshold, entry day, stop-loss or exit. Those remain explicit interpretation variables in the next bounded phase.

## Status
Spot-data source selected; validation workflow pending.
