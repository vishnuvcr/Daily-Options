# Phase 32 Status

**Branch:** `phase-32-options-skew-smile-dislocation-v1`

**Authoritative run:** **36339168867**

**State:** **CLOSED — negative discovery result; no strategy promoted.**

## Data gate

- Raw NIFTY 09:30 sessions: **1,225**
- Warm-up-complete sessions: **1,165**
- Strict-next-expiry coverage: **100%**
- Valid four-quote IV surface: **1,143 / 1,165 = 98.11%**
- Prior-surface look-ahead violations: **0**
- Feature-eligible sessions after the 60-session prior-only z-score: **691**
- Execution coverage across all 12 true cells: **96.74%–100.00%**
- Base/Stress data gate: **PASS**

## Frozen experiment

- Features: SKEW_Z, SMILE_Z
- Thresholds: |z| >= 1.0 and |z| >= 1.5
- Exits: 10:30, 13:30, 15:10 IST
- True cells: **12**
- Null seeds: **101, 202, 303, 404, 505**
- Null summaries: **60 Base + 60 Stress**
- Historical NIFTY lot sizes and date-aware Paytm Money/NSE/statutory cost model
- Base slippage ₹0.20 / Stress slippage ₹0.40 per option-price unit per order

## Economic result

- Base promotion passes: **0/12**
- Stress promotion passes: **0/12**
- Maximum Base mean weekly net: **-₹408.84**
- Maximum Stress mean weekly net: **-₹521.02**
- Maximum Base positive-week rate: **16.42%**
- Maximum Stress positive-week rate: **11.94%**
- No true cell exceeded its matched five-seed null mean in either friction regime.
- WFA/OOS promotion: **NOT AUTHORIZED**

## Decision

Phase 32 is closed as negative discovery evidence. No post-result tuning is allowed. The next materially distinct research family may be preregistered separately; Phase 32 itself will not be optimized further.

## Primary result

See `reports/phase32/final_result.md` for the complete manuscript, tables, appendices, figures and reproducibility record.
