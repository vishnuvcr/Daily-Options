# Phase 13.1 — Frozen Later-Period OOS Validation Plan

## Purpose
Validate the exact Phase 13 leading configuration on a later, untouched 2021-01-01 through 2025-12-31 period without any parameter optimization.

## Frozen strategy
- Underlying: NIFTY
- Signal time: 14:45 IST
- Lookback: 10 one-minute observations
- Standardized return threshold: z >= 1.5
- Prior-range confirmation: spot > prior 30-minute high
- Realized-volatility gate: >= 80th percentile of the rolling volatility state
- Direction: LONG
- Structure: ATM CALL
- Expiry: next monthly expiry
- Entry: next minute after signal
- Hold: 10 minutes
- Stop: 30% below entry premium
- Target: 60% above entry premium
- No re-optimization, parameter expansion, or result-based narrowing

## Data
Primary later-period dataset: Hugging Face artist-23/nifty-options-data.
Pinned revision: 45e0a04.
Coverage reported by the dataset page: 33,963,731 rows, 2020-12-29 through 2025-12-26, with timestamp/OHLC/IV/volume/OI/strike/spot/expiry-type/strike-type/option-type fields.

## Execution
- Validation dates: 2021-01-01 through 2025-12-31.
- Base slippage: ₹0.20 premium points per leg.
- Stress slippage: ₹0.40 premium points per leg.
- Paytm Money brokerage/cost model from config/cost_model_2026.yaml.
- Date-aware NIFTY lot size.
- One active strategy position per signal path; no pyramiding.
- Entry uses next-minute option open.
- Exit uses stop/target collision handling in documented bar order, otherwise final bar close.

## Integrity controls
1. Unit tests must pass before data acquisition.
2. Dataset revision must be explicit and immutable.
3. Cache must be reusable; workflow must not silently replace a pinned dataset.
4. No parameter search occurs in this phase.
5. Base and stress are identical except for slippage.
6. All signal/entry/exit timestamps must preserve the information barrier.
7. Zero-trade or schema-defect outputs are not interpreted as strategy evidence.
8. Every engineering failure is appended to docs/error_log.md.
9. A final result is classified only after both base and stress complete.

## Promotion gate
A Phase 13.1 result is not promoted merely because it is positive. Promotion requires:
- positive net active-day expectancy in both base and stress;
- meaningful trade count and multi-year coverage;
- at least one untouched validation window at or above ₹1,000/lot/day where a valid windowing scheme is applicable;
- no single year or tiny trade cluster dominates the result;
- reproducible artifact and source revision recorded.

## Phase outcome
- PASS: all promotion conditions satisfy the frozen rule.
- NEAR-MISS: economically positive but below target or underpowered.
- FAIL: non-positive or materially unstable.
- DATA-LIMITED: insufficient independent observations to make a reliable decision.

## Next step
If Phase 13.1 is NEAR-MISS or DATA-LIMITED, the next branch must use an explicitly different validation source or hypothesis. No tuning of the frozen Phase 13 rule is allowed based on this phase's result.