# Phase 12 v3 — Futures/Spot Lead-Lag + Defined-Risk Option Pilot

Authoritative workflow run: 35992405332
Branch: phase-12-derivative-lead-options-v3-zenodo-pilot
Commit: 49909d5afd8555b6d358e893070e24bcffc71153
Artifact: phase12-zenodo-pilot-v3
Artifact SHA-256: c2eb2bd537a9bdeb00beb0e2da270369819aec1a3ef4d04262f419e962950efb

## Validity

This is the first accepted Phase 12 numerical result. Earlier Phase 12 artifacts were explicitly rejected because of CI/parser/timing/contract-selection defects and are retained only as audit history.

- 288 fixed simulation cells = 144 signal/contract configurations × 2 fixed risk profiles.
- 52,476 generated entries.
- 51,760 executable trades in both base and stress.
- 2019–2020 Zenodo 1-minute NIFTY spot, continuous first-month NIFTY futures (F1), and options.
- Next-minute execution.
- Base slippage: 0.20 premium points/leg.
- Stress slippage: 0.40 premium points/leg.
- Full nested walk-forward with 4 test windows.

## Base result

Best tested cell: lw1|z1.50|09:45:00|MONTH|w2|h30|r1

- Trades: 267
- Active days: 267
- Mean active-day net: -₹151.50/lot/day
- Median active-day net: -₹184.78
- Win rate: 15.36%
- Profit factor: 0.222
- Max drawdown: -₹40,368
- Total net: -₹40,449
- Target-qualified cells >= ₹1,000/lot/day: 0

## Stress result

Same leading cell:
- Mean active-day net: -₹211.50/lot/day
- Median active-day net: -₹244.78
- Win rate: 10.49%
- Profit factor: 0.144
- Max drawdown: -₹56,268
- Total net: -₹56,469
- Target-qualified cells: 0

## Walk-forward

Base: 4 windows; 0 positive; 0 target; mean test-window net -₹144.72/lot/day; gate FAIL_PRELIMINARY.
Stress: 4 windows; 0 positive; 0 target; mean test-window net -₹204.72/lot/day; gate FAIL_PRELIMINARY.

## Interpretation

The futures/spot lead-lag feature did not translate into profitable defined-risk option execution under the tested rules and costs. Performance remained negative across the complete base leaderboard and deteriorated materially under doubled slippage.

The result is stronger than a single-period failure because the negative sign persisted through all four walk-forward windows. The best test window was still negative.

The continuous F1 futures series is not exact-contract-expiry identified in the published Zenodo schema. Therefore this pilot is a valid hypothesis result but not an exact-expiry production-validation dataset.

## Decision

Phase 12 v3 is RETIRED. No result-driven retuning, threshold hunting, or post-hoc variant narrowing will be performed.

Next research must change mechanism, not simply adjust the Phase 12 lead/lag parameters.