# Phase 11 v5e — Breakout/Pullback + OI Confirmation Result

Run: 35978104824  
Commit: ad57d005cbbf1a81a8d0392a83c5e4c4d3ffdeca  
Branch: phase-11-breakout-pullback-oi-v5e-authoritative  
Artifact: phase11-breakout-pullback-oi-v5  
Artifact SHA-256: 8e27584fb99e247e8f215a151c98d99a290f45e6d5668498557559b6d5091cae

## Result

- Preregistered variants: 64
- Signals: 2,220
- Executable entries: 2,020
- Trades: 2,020
- Variants with trades: 32
- Preliminary target-qualified variants: 0
- Walk-forward windows: 0
- Preliminary gate: FAIL_PRELIMINARY
- Base slippage: 0.20 premium points per leg
- Stress slippage: 0.40 premium points per leg

Best base variant:
- ID: or5|b0.0005|pb0.0005|09:45:00|h15|r1
- Mean active-day net: -₹122.28/lot/day
- Win rate: 5.22%
- Positive-day rate: 5.22%
- Profit factor: 0.066
- Max drawdown: -₹14,617.98
- Total net: -₹14,061.66

The same variant under doubled slippage:
- Mean active-day net: -₹138.10/lot/day
- Win rate: 3.48%
- Profit factor: 0.051
- Max drawdown: -₹16,389.98
- Total net: -₹15,881.66

Trade-exit audit across the base run:
- STOP: 1,036 trades
- TIME: 978 trades
- TARGET: 6 trades

## Decision

Phase 11 is retired. It does not meet the preliminary ₹1,000/lot/day gate, has strongly negative net expectancy across the leaderboard, and deteriorates further under doubled slippage. No post-result parameter tuning will be performed.

The zero walk-forward windows do not rescue or invalidate the preliminary conclusion: the family already failed before formal WFA because no configuration was positive or target-qualified in the base screen.

## Data / engineering status

Unit tests passed and cached public BANKNIFTY index/options data acquisition passed. The execution used fixed strikes, next-minute entry, direction-aware nearest wing selection, expiry-aware lot size and the repository cost model.

## Reproducibility

The original workflow artifact remains the authoritative numerical record. The artifact includes base/stress signals, entries, trades, leaderboards, walk-forward files and the decision summary.
