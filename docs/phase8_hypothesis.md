# Phase 8 — Hybrid Momentum + Option-Premium Confirmation

## Research question

Can a regime-aware directional/mean-reversion signal, filtered by contemporaneous option-premium momentum and managed with adaptive exits, produce at least Rs 1,000 net per active lot per trading day after realistic costs?

## External hypothesis source

The public `dhruvYadavjii/AI-trader` repository documents a NIFTY tick-replay system using EMA/RSI/VWAP trend features, option-premium confirmation, regime filtering and dynamic/risk-managed exits. Its published March-April 2026 sample reports 49 trades, 71% win rate and Rs 53,715 net P&L for its medium-risk profile, or about Rs 1,096 per trade; a high-risk profile reports 52 trades and Rs 62,762 net, about Rs 1,207 per trade. Those figures are treated only as a hypothesis lead because the published sample is short and uses a different tick-data source.

## Phase 8A pre-registration

### Trend continuation

CALL conditions:
- EMA9 > EMA20 > EMA50;
- RSI >= 55;
- 3-minute NIFTY return > 0;
- ATM call premium rising over both 1 and 3 minutes.

PUT conditions are symmetric.

### Mean reversion

CALL conditions:
- RSI <= 30;
- spot is at least 2 rolling standard deviations below its 20-minute mean;
- EMA20/EMA50 separation is <= 0.15% of spot;
- ATM call premium confirms upward.

PUT conditions are symmetric.

### Grid

48 variants:
- 2 families;
- 2 signal-start times;
- WEEK/MONTH expiry;
- 3-of-4 or 4-of-4 condition requirement;
- 15/30/45-minute maximum hold;
- 2 dynamic exit profiles.

Exit profiles:
1. 15% initial stop, 40% target, trailing starts at +12%, 8% trail gap.
2. 20% initial stop, 60% target, trailing starts at +20%, 12% trail gap.

## Execution and costs

- Feature timestamp uses only completed minute information.
- Entry uses the next available option minute open.
- The option strike selected at entry is frozen for the entire trade.
- Stop/target collisions are resolved conservatively: if both are touched in one minute, the stop is assumed first.
- Brokerage/statutory/exchange costs use the repository cost model.
- Base slippage: 0.20 premium points per leg.
- Stress slippage: 0.40 premium points per leg.
- NIFTY lot size is date-aware.

## Promotion

Preliminary screen: mean active-day net >= Rs 1,000/lot.

Formal promotion additionally requires positive untouched-test expectancy, at least one untouched test window >= Rs 1,000/lot/day, and no material collapse under doubled slippage.

A negative Phase 8A family is retired, but the overall study continues to another scientifically distinct phase rather than ending.
