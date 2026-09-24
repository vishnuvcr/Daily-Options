# Phase 13 — Late-Day Volatility Acceleration

## Research question

Can a late-session NIFTY range-break signal, conditioned on an elevated intraday volatility state, generate a positive cost-adjusted one-lot option strategy after realistic slippage and walk-forward validation?

## Motivation

Recent NSE ORB research reports operationally attractive raw breakout returns but weak statistical evidence in a one-year single-stock sample, specifically calling for stricter cost modelling and out-of-sample validation. citeturn901768search0 A 2026 NIFTY volatility-regime paper finds persistent intraday volatility states with short-lived elevated regimes and incremental short-horizon forecasting value, while return differences between regimes were not statistically significant. citeturn901768search3

This phase therefore does not assume that a breakout is profitable. It tests whether **late-day range expansion + elevated realized-volatility state** improves option-execution economics.

## Preregistration

384 fixed simulation cells:

- signal lookback: 10 or 15 minutes;
- standardized return threshold: 1.0 or 1.5;
- realized-volatility percentile gate: 60th or 80th percentile;
- signal times: 14:45, 15:00, 15:15 IST;
- execution: next minute;
- structure: long ATM option or one-step ATM debit spread;
- expiry mode: next weekly or next monthly;
- hold: 10 or 20 minutes;
- fixed risk profile: 30% stop / 60% target OR 50% stop / 100% target.

No post-result parameter expansion is allowed.

## Gates

Promotion requires all of:
1. positive cost-adjusted preliminary mean with meaningful trade count;
2. at least one cell >= ₹1,000/lot/day;
3. positive and economically useful walk-forward test performance;
4. survival under doubled slippage;
5. no single test window carrying the result.

The source remains the 2019–2020 Zenodo intraday archive, so any positive result is only a hypothesis-stage result until independently validated on a later dataset with exact current contract identity.
