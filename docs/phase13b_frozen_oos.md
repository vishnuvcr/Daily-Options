# Phase 13b — Frozen Independent OOS Validation

Only the exact Phase 13 leading configuration is tested; no parameters are optimized in this phase.

Frozen rule: w10 | z1.5 | 80th-percentile RV | 14:45 IST | LONG ATM MONTH | 10-minute hold | 30% stop / 60% target.

Validation period: 2021-01-01 through 2025-12-31.

Dataset: artist-23/nifty-options-data. The public dataset contains 33,963,731 rows spanning 2020-12-29 to 2025-12-26 and exposes timestamp, OHLC, IV, volume, OI, strike_price, spot, expiry_type, strike_type and option_type.

Source: https://huggingface.co/datasets/artist-23/nifty-options-data