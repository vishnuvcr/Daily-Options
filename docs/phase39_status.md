# Phase 39 Status

## Final state
**CLOSED — DATA-LIMITED. No Base/Stress economics, WFA/OOS or promotion.**

Authoritative integrity rerun: workflow 36410759707, attempt 2.

## Frozen experiment
- NIFTY 09:15–09:29 realized opening move versus 09:30 ATM option-implied 15-minute move.
- Strictly prior 60-session MOVE_RATIO z-score; ±0.75 dislocation states.
- CONTINUE/FADE; 09:31 entry; 10:30/15:10 exits; one-lot 200-point debit spread.
- Historical lots; Paytm Money/NSE/statutory costs; Base/Stress slippage ₹0.20/₹0.40.

## Final data-gate result
- Raw sessions: 1,234.
- Post-warm-up sessions: 1,174.
- Feature-eligible: 838 / 1,174 = **71.38%**.
- Direct IV input coverage: **98.64%**.
- Expiry mapping: **100%**.
- Prior-information violations: **0**.
- Corrected minimum execution quote coverage: **96.99%**.
- Required feature/execution threshold: **95%**.
- Gate: **FAIL** because feature eligibility is 71.38%.

## Root limitation
Sixteen post-warm-up sessions lacked a usable MOVE_RATIO input. Because the frozen z-score requires 60 prior completed sessions, those sparse missing inputs propagate into 320 downstream sessions without a valid prior-only z-score. The observed 71.38% eligibility is therefore a direct consequence of the preregistered feature definition and is not being repaired by switching to a different lookback or by imputing missing IV.

## Economic disposition
No Base, Stress or null P&L was accepted. No strategy profitability conclusion can be drawn from Phase 39.

## Engineering closures
- E0391–E0397: CLOSED after clean correction/rerun. They were implementation defects only and did not provide economic evidence.
- E0398: final DATA-LIMITED closure due the 71.38% eligibility gate.

## Conclusion
Phase 39 is retired as **DATA-LIMITED**. The pinned source has sufficient raw ATM IV coverage for most sessions, but not enough complete prior-60-session feature histories to satisfy the preregistered ≥95% eligibility requirement. No post-result feature redesign is authorized.

## Next research
Advance to Phase 40: prior-day NIFTY ATM IV versus prior realized volatility, used to normalize the next-session opening gap. This is a distinct state variable from Phase 39 and will use a fresh preregistered branch.

## Reproducibility
- docs/phase39_plan.md
- docs/phase39_literature_review.md
- docs/phase39_status.md
- docs/phase39_error_log.md
- research/phase39_implied_realized_opening_dislocation.py
- tests/test_phase39_implied_realized_opening_dislocation.py
- research/phase39_source_diagnostic.py
- research/phase39_execution_diagnostic.py
- .github/workflows/phase-39-implied-realized-opening-dislocation.yml
- reports/phase39/