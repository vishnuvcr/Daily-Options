# Conversation and Decision Log

## 2026-09-24 — Phase 3G final result
- User authorized continuation with “Ok proceed”.
- The corrected Phase 3G fast2 run 35916973751 completed successfully after the date-normalization defect was fixed.
- Base-cost leaderboard: all 128 variants negative; best mean calendar-day net Rs -61.11/lot/day.
- Stress-cost leaderboard: all 128 variants negative; best mean calendar-day net Rs -79.55/lot/day.
- Corrected WFA: 13 test windows; base 1 positive, stress 0 positive; mean test-window net Rs -192.79 base and Rs -252.79 stress.
- Decision: retire the bounded dynamic-break + post-break-OI family without expanding its grid.
- Next bounded hypothesis: option-lead-lag / derivative price-discovery.

## 2026-09-24 — Phase 3H initialization
- Phase 3G was retired after corrected leakage-safe WFA failure.
- User authorized continuation.
- New bounded hypothesis: short-horizon ATM call-minus-put price pressure may lead the next 1–5 minute NIFTY spot move.
- Pre-registered 108 variants; no post-hoc expansion planned.

## 2026-09-24 — User reported apparent stall during Phase 3H
- User shared a screenshot showing repeated waiting/progress checks and asked whether the research was stuck.
- Verification showed the numerical Phase 3H job was genuinely long-running in one opaque CI step.
- No strategy result from that slow run was accepted.
- Decision: replace the nested pandas execution path with an indexed cached engine while preserving the 108-variant pre-registration, cost model, information barrier and WFA rules.
- Latest run: 35918302989, currently in progress after the corrected engine commit; dependency installation is still underway and no numerical result is yet accepted.
