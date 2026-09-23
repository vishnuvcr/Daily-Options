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

## 2026-09-24 — Research continuation from linked chat

- User requested continuation of the Daily-Options research from the prior linked conversation.
- Repository audit confirmed Phase 4 and Phase 3G are complete and retired; Phase 3H is the current bounded experiment.
- Current accepted research direction: short-horizon ATM option-price pressure versus subsequent NIFTY spot movement, with defined-risk debit spreads and realistic costs.
- Current CI run being monitored: GitHub Actions run 35918302989 on branch `phase-3h-option-lead-lag`.
- At this continuation checkpoint, unit tests and pinned-data acquisition have completed; the base/stress lead-lag tournament is executing. No numerical Phase 3H statistic is accepted until the run and artifact outputs complete.
- The project research log records user-visible decisions and evidence only; private hidden chain-of-thought is not stored.


## 2026-09-24 — Phase 3H final result
- User authorized autonomous continuation.
- Corrected Phase 3H run 35918302989 completed successfully after the pre-result E0043 path-variant correction and E0044 cache correction.
- All 108 variants were negative at base and stress slippage.
- Corrected WFA had 16 negative test windows out of 16 at both friction levels.
- Decision: retire option-price lead-lag as a lead family; do not widen thresholds or add ad hoc filters.
- Next bounded research direction: underlying-price regime-conditioned mean reversion/opening-range behavior with defined-risk spreads.

## 2026-09-24 — Phase 3I data gate result and predictive-gate correction

- Phase 3I CI successfully loaded all four Zenodo years after fixing nested archive extraction, compact schema normalization, and headerless CSV detection.
- Accepted data-gate output reports 991 common trading dates from 2017-01-02 through 2020-12-31, 99.733% timestamp overlap, and 99.193% common-day session completeness at the >=350-minute threshold.
- The first 72-variant predictive diagnostic found a small cluster of apparently positive futures/spot lead-gap configurations, but that initial code gate did not enforce the pre-registered two-horizon and both-halves stability rule.
- That first predictive result is explicitly provisional. The repository now enforces the declared stability rule, and only the corrected CI output can advance Phase 3I to option implementation.

## 2026-09-24 — Phase 3I option source correction
- The first option execution was rejected because its option-data coverage did not overlap the signal sample.
- The corrected stage uses the matching 2017-2020 Zenodo option archive.
