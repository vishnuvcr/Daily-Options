# Phase 44 — NIFTY Opening-Gap Magnitude × Gap Direction

### Research question
Does the magnitude of the current NIFTY opening gap condition whether following or fading the gap produces a robust, friction-adjusted intraday option-spread edge?

### Frozen states
- SMALL_GAP: |gap| < 0.50%
- MEDIUM_GAP: 0.50% <= |gap| < 1.00%
- LARGE_GAP: |gap| >= 1.00%

The thresholds are fixed before observing Phase 44 results. Both gap directions and both exits are tested; no bucket is selected post-result.

### Execution
Current gap = 09:15 NIFTY open / prior completed 15:10 close − 1. Zero gap = no trade. FOLLOW_GAP and FADE_GAP. Entry 09:31 option open; exits 10:30 and 15:10 option close. One-lot 200-point ATM directional debit spread, nearest expiry on/after trade date, historical lots, existing Paytm Money/NSE/statutory costs, Base/Stress slippage ₹0.20/₹0.40 per option-price unit/order.

### Discovery and nulls
3 magnitude states × 2 mappings × 2 exits = 12 true cells. Five fixed full-panel permutation null seeds 101,202,303,404,505 permute the frozen gap-state labels across eligible dates, yielding 60 null cells per friction regime.

### Gates
≥95% post-warm-up feature eligibility, ≥95% feature/expiry coverage, zero prior-information violations, ≥95% execution coverage in every true cell, and accounting reconciliation. Promotion requires mean weekly net ≥₹5,000, median weekly net ≥₹5,000 and positive-week rate ≥70% in both Base and Stress. No WFA/OOS unless a true cell clears all criteria.

### Stop rule
No post-result threshold changes, bucket merging/splitting, mapping selection, execution-time changes, strike/expiry changes or friction changes.
