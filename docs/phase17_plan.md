# Phase 17 — NIFTY Exact-Expiry Premium-Skew + Option-Flow Pressure

## Research question
Can an intraday NIFTY defined-risk credit spread exploit unusually rich downside/upside option premium skew when spot momentum, realized-volatility state, option volume imbalance and open-interest imbalance agree, using an exact-expiry contract source?

## Why this is distinct
Phase 16 required IV but the Artist23 source does not provide an actual expiry date or IV field. Phase 17 deliberately switches both the data source and the observable signal mechanism:
- exact expiry is encoded by one NIFTY option parquet file per expiry date;
- premium skew is calculated directly from same-expiry option closes;
- volume/OI pressure is used as confirmation;
- entry uses the next-minute option open.

## Frozen grid
3 entry times × 2 premium-skew thresholds × 2 jump brakes × 2 RV-ratio states × 2 spread widths × 2 holds × 2 stops × 2 directions = 384 cells.

Entry times: 14:30, 14:45, 15:00 IST.
Premium-skew thresholds: 0.10, 0.15.
Jump brakes: |10-minute spot return| ≤ 0.30%, 0.50%.
RV ratio: 20-minute realized volatility / 120-minute realized-volatility mean ≥ 1.00, 1.25.
Width: one or two strikes beyond the ATM±2 short leg.
Hold: 15 or 30 minutes.
Stop: 1.25× or 1.50× entry credit.
Target: fixed at 50% of entry credit.

## Direction rule
Positive skew + non-negative spot return + non-negative PE-vs-CE volume/OI imbalance → PUT credit spread.
Negative skew + non-positive spot return + non-positive PE-vs-CE volume/OI imbalance → CALL credit spread.

## Data
TradeMarkk dataset: thetrademarkk/india-index-options-1m, pinned revision 51ca58c.
NIFTY spot: index/NIFTY.parquet.
NIFTY options: options/NIFTY/{YYYY-MM-DD}.parquet.
The dataset card states 1-minute OHLCV(+OI), exact strike, option_type and expiry fields, with coverage approximately 2021–2026.

## Execution controls
Unit tests → cached exact-expiry data → base slippage 0.20/leg → stress 0.40/leg.
No result-driven parameter changes.
Mean active-day net is the target metric.
No Phase 17 preliminary result is promoted without untouched walk-forward validation and independent holdout validation.

## Promotion gate
At least one configuration must be positive after full costs, remain positive under doubled slippage, reach ₹1,000 net per active lot per active trading day in an untouched test window, have sufficient trade/calendar coverage, and show no single tiny cluster dominating performance.


## 2026-09-24 pre-run source verification
The upstream TradeMarkk dataset tree shows NIFTY option files named by exact expiry date, such as 2021-05-27.parquet and successive weekly expiry files. The dataset card reports exact expiry/strike/option-type fields plus OHLCV/OI, making it suitable for this phase's contract-selection requirement.
