# Phase 9 — Regime-Filtered Defined-Risk Credit Spreads

## Research question

Can intraday NIFTY premium-selling produce at least Rs 1,000 net per active lot/day when the sold tail is aligned with a directional regime, the position is defined-risk, and a hard buyback stop prevents large adverse excursions?

## Hypothesis

Bull regime -> bull-put credit spread.
Bear regime -> bear-call credit spread.

The regime requires:
- EMA20/EMA50 direction;
- 5-minute underlying momentum in the same direction;
- ATM IV / 20-minute realized-volatility ratio >= 1.10.

This differs economically from the retired short straddle: only the opposite tail is sold, risk is capped by the long hedge, and the sold tail is conditioned on trend.

## 96-variant pre-registration

- family: BULL_PUT / BEAR_CALL;
- entry: 09:45 / 10:15 IST;
- expiry: WEEK / MONTH;
- spread width: 2 / 3 strike steps;
- short strike: fixed 3 strike steps OTM at entry;
- maximum hold: 60 / 120 / 180 minutes;
- exit profile:
  - 1.5x credit stop + 50% credit capture target;
  - 2.0x credit stop + 65% credit capture target.

No additional thresholds will be added after the result.

## Execution

The signal is computed only from completed data. Entry is the next executable minute. Both absolute strikes are selected at entry and held fixed.

Within a minute, a stop/target collision is resolved in favor of the stop.

Base slippage is 0.20 premium points per leg; stress is 0.40.

## Costs and promotion

Brokerage, STT, exchange, SEBI, stamp duty, GST and date-aware lot sizes use the repository cost model.

Preliminary gate: mean active-day net >= Rs 1,000/lot.
Formal gate: positive untouched-test expectancy plus at least one untouched test window >= Rs 1,000/lot/day and no material collapse under doubled slippage.
