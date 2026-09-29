# Research Status

Last updated: 2026-09-29

## Overall
**Phase 47 — Opening-gap magnitude normalized by prior-day range: CLOSED NEGATIVE DISCOVERY**

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


## 2026-09-29 frontier update
- Phase 41: **CLOSED DATA-LIMITED** — authoritative run 36467584676; 30.68% feature eligibility, 79.50% prior-chain coverage, 87.41% core-chain coverage, zero prior-information violations; no P&L accepted.
- Phase 42: **ACTIVE / PREREGISTERED** — option day-night return asymmetry × opening-gap direction. Authoritative workflow run **36468978862** is executing.


## 2026-09-29 frontier update
- Phase 42: **CLOSED DATA-LIMITED** — authoritative run 36469315584 attempt 2; feature eligibility 95.0777%, zero prior-information violations, but 0/5,364 required execution quote keys available and 0% execution coverage in every true cell. No P&L accepted.
- Phase 43: **CLOSED NEGATIVE DISCOVERY** — authoritative run 36471290988; 20 true cells; no cell met the ₹5,000/week promotion gate in both Base and Stress.
- Phase 44: **CLOSED DATA-LIMITED** — authoritative run 36471949846; LARGE_GAP cells had 94.44% execution coverage, below the frozen 95% gate; no P&L promotion accepted.
- Phase 45: **CLOSED NEGATIVE DISCOVERY** — authoritative run 36472742169; no 12-cell confirmation state cleared the promotion gate.
- Phase 46: **CLOSED NEGATIVE DISCOVERY** — authoritative run 36473334899; no 12-cell close-location state cleared the promotion gate.









## 2026-09-29 latest frontier update
- Phase 46: **CLOSED NEGATIVE DISCOVERY** — authoritative run 36473334899.
- Phase 47: **CLOSED NEGATIVE DISCOVERY** — authoritative run 36538234322; best cell ₹714/week Base / ₹666 Stress; no WFA/OOS.
- Phase 48: **CLOSED NEGATIVE DISCOVERY** — authoritative run 36538835468; all 8 true cells negative under Base and Stress; no WFA/OOS.
- Phase 49: **CLOSED NEGATIVE DISCOVERY** — authoritative run 36539451804; best cell ₹88/week Base / ₹9 Stress; no WFA/OOS.
- Phase 50: **CLOSED NEGATIVE DISCOVERY** — authoritative run 36539948879; best cell ₹163/week Base / ₹116 Stress; no WFA/OOS.
- Phase 51: **CLOSED DATA-LIMITED** — authoritative run 36540501382; no P&L accepted.
- Phase 52: **CLOSED NEGATIVE DISCOVERY** — authoritative run 36548301179; 98.12% feature eligibility, 98.80% same-session ATM-IV coverage, best cell -₹101/week Base / -₹183 Stress; all 12 cells failed.
- Phase 53: **CLOSED NEGATIVE DISCOVERY** — authoritative run **36548934744**; 98.12% feature eligibility, 98.80% same-session ATM-adjacent skew coverage, best cell -₹198/week Base / -₹293 Stress; all 12 cells failed.
- Next frontier: **Phase 54 — same-session 09:30 matched ATM IV call-put spread × opening direction**.


## 2026-09-29 latest frontier update
- Phase 52: **CLOSED NEGATIVE DISCOVERY** — authoritative run 36548301179; best MID_IV/FADE/15:10 = -₹100.61/week Base / -₹182.60 Stress.
- Phase 53: **CLOSED NEGATIVE DISCOVERY** — authoritative run **36548991737**; 97.95% final feature eligibility, 98.63% same-session skew coverage, 0 prior-information violations, 99.26–100% execution coverage. Best MID_SKEW/FADE/15:10 = -₹177.32/week Base / -₹252.72 Stress; no WFA/OOS.
- Current frontier: **Phase 54 — same-session 09:30 ATM put–call IV spread × opening direction**.
