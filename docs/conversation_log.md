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

## 2026-09-24 — Phase 3I initialization
- Phase 3H was retired after a negative 108-variant WFA.
- Per the project stop rule, Phase 3I is the last bounded exploratory family under the current public dataset.
- Hypothesis: opening-range false breaks that re-enter the range may exhibit short-horizon mean reversion; test via defined-risk debit spreads.

## 2026-09-24 — Phase 3 final closure
- User authorized autonomous continuation.
- Phase 3I final exploratory family completed on run 35919447949.
- All 144 variants were negative at base and stress friction; all 14 walk-forward test windows were negative.
- No Phase 3 candidate met the Rs 1,000/lot/day promotion gate.
- Decision: stop exploratory Phase 3 under the current public dataset and move to final synthesis/data-quality assessment.


## 2026-09-24 — Phase 7 final synthesis
- Research continuation was anchored to the repository state and the recorded terminal exploratory result.
- The bounded exploratory program is closed without a promotion candidate.
- Phase 7 manuscript work was started on branch phase-7-manuscript.
- Final manuscript, data-gap assessment, summary JSON and figures were added to the repository.
- Phase 5 robustness and Phase 6 paper-shadow remain blocked until a candidate passes the promotion gate.
