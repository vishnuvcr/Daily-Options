# Research Status

Last updated: 2026-09-28

## Overall
**Phase 41 — NIFTY option-gamma concentration × opening-gap direction: PREREGISTERED / ENGINEERING BUILD**

## Completed frontier closures
- Phase 34: DATA-LIMITED at 53.20% two-expiry prior-session surface coverage.
- Phase 35: global-shock/India-volatility state branch DATA-LIMITED; global-shock option-vol branch negative.
- Phase 36: global-shock breadth/disagreement negative.
- Phase 37: global-shock opening-dislocation negative.
- Phase 38: opening-volatility/price-structure negative; authoritative run 36408210374; 0/8 Base and 0/8 Stress promotion cells.
- Phase 39: option-implied versus realized opening-move dislocation negative; authoritative run 36465244174; 98.64% feature eligibility; 0/8 Base and 0/8 Stress promotion cells.
- Phase 40: prior-day ATM IV/RV state × overnight-gap implied-move dislocation negative; authoritative run 36466313849; 97.79% feature eligibility; 0/8 Base and 0/8 Stress promotion cells.

## Phase 41 current state
Phase 41 is the next distinct preregistered family. It tests whether the **concentration** of option gamma around ATM, estimated from prior-session OI and option prices, changes the tendency of the next session's opening gap to continue or mean-revert.

This is deliberately distinct from:
- Phase 31.7's raw OI/volume pressure;
- Phase 31.9's India VIX/RV gap regimes;
- Phase 39's implied-versus-realized opening-move ratio;
- Phase 40's prior-day implied-volatility / overnight-gap dislocation;
- earlier global-shock families.

## Frozen Phase 41 objectives
- Build a prior-session 15:10 exact-expiry NIFTY option-chain gamma-concentration measure.
- Use only data available at or before 15:10 on the prior completed session.
- Standardize the concentration measure with the strictly prior 60 valid observations.
- Test FOLLOW_GAP and FADE_GAP at 10:30 and 15:10.
- Apply historical lot sizes, Paytm Money/NSE/statutory costs and Base/Stress slippage.
- Run five fixed full-panel permutation nulls.
- Do not permit WFA/OOS unless both Base and Stress discovery gates clear.

## Current integrity rule
No Phase 41 P&L is accepted until unit tests, data gates, execution coverage, accounting and artifact persistence all pass.
