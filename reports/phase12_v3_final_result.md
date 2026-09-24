# Phase 12 v3 — Final Result: NIFTY Futures/Spot Lead-Lag → Debit Spread

## Execution provenance

- Branch: phase-12-derivative-lead-options-v3-zenodo-pilot
- Workflow run: 35992405332
- Commit: 49909d5afd8555b6d358e893070e24bcffc71153
- Artifact ID: 10804659354
- Artifact SHA-256: c2eb2bd537a9bdeb00beb0e2da270369819aec1a3ef4d04262f419e962950efb
- Source archive: Zenodo 10899828
- Pilot period: 2019–2020
- Preregistered simulation cells: 288
- Signal/contract configurations: 144
- Fixed risk profiles: 2
- Base slippage: 0.20 premium points per leg
- Stress slippage: 0.40 premium points per leg

## Data integrity

Unit tests, archive acquisition, recursive extraction, headerless schema parsing, IST timing, option-file coverage and representative next-minute leg-overlap checks all passed before P&L.

## Base friction

- Signals/entries: 52,476
- Executable trades: 51,760
- Variants with trades: 144 of 288
- Target-qualified variants: 0
- Best variant: lw1|z1.50|09:45:00|MONTH|w2|h30|r1
- Best mean active-day net: -₹151.50/lot/day
- Best median active-day net: -₹184.78/lot/day
- Best win rate: 15.36%
- Best profit factor: 0.222
- Best max drawdown: -₹40,368.01
- Best total net: -₹40,449.23
- Walk-forward windows: 4
- Positive walk-forward windows: 0
- Target walk-forward windows: 0
- Mean walk-forward test net: -₹144.72/lot/day
- Walk-forward gate: FAIL_PRELIMINARY

## Stress friction

- Signals/entries: 52,476
- Executable trades: 51,760
- Target-qualified variants: 0
- Best variant: lw1|z1.50|09:45:00|MONTH|w2|h30|r1
- Best mean active-day net: -₹211.50/lot/day
- Best median active-day net: -₹244.78/lot/day
- Best win rate: 10.49%
- Best profit factor: 0.144
- Best max drawdown: -₹56,268.01
- Best total net: -₹56,469.23
- Walk-forward windows: 4
- Positive walk-forward windows: 0
- Target walk-forward windows: 0
- Mean walk-forward test net: -₹204.72/lot/day
- Walk-forward gate: FAIL_PRELIMINARY

## Decision

Phase 12 is retired. The futures/spot lead-gap mechanism did not produce positive cost-adjusted expectancy anywhere in the preregistered grid, and all four walk-forward test windows were negative in both friction settings. No result-driven tuning will be performed.

## Limitation

The Zenodo futures series is a continuous Nifty_F1 first-month futures series and does not expose exact expiry identity at each row. The phase is therefore a valid negative hypothesis-screen result, not a final exact-contract price-discovery study.

## Next frontier

Phase 13 moves to a materially different mechanism: modern NIFTY option data, volatility regime + price structure + defined-risk option execution, and a strict no-trade filter.