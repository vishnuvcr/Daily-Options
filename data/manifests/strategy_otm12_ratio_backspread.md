# Data Manifest — OTM1 / 2xOTM2 Ratio Backspread

Pinned source: thetrademarkk/india-index-options-1m
Revision: 51ca58c

Expected local paths:
- data/cache/phase24_trademarkk/index/NIFTY.parquet
- data/cache/phase24_trademarkk/options/NIFTY/*.parquet

Backtest window: 2021-07-01 through 2026-08-04.

Raw market data are not committed because of repository size. GitHub Actions cache is used to persist/reuse the pinned dataset. The workflow performs explicit index/expiry coverage validation before P&L.
