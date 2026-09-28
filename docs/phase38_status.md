# Phase 38 Status

## Final state
CLOSED — NEGATIVE DISCOVERY. No WFA/OOS or promotion.

Authoritative clean workflow: 36408210374
Branch: phase-38-opening-volatility-structure-v1

## Frozen experiment
- Study window: 2021-07-01 through 2026-08-31.
- First 15-minute opening range: 09:15–09:29.
- Strictly prior 60-session opening-range z-score.
- States: HIGH_VOL / LOW_VOL at ±0.75 z.
- Direction mappings: CONTINUE / FADE.
- Execution: 09:31 entry, 10:30 or 15:10 exit, one-lot 200-point debit spread, historical lot sizes.
- Base/Stress slippage: ₹0.20 / ₹0.40 per option-price unit per order.
- Fixed Paytm Money/NSE/statutory cost model.
- Five permutation-null seeds.

## Data and integrity result
- Raw NIFTY sessions: 1,228.
- Post-warm-up sessions: 1,168.
- Feature-eligible sessions: 1,168 / 1,168 = 100%.
- Complete feature sessions: 1,168 / 1,168 = 100%.
- Expiry-mapping coverage: 100%.
- Prior-information violations: 0.
- Base and Stress accounting reconciliation: passed for all 8 cells.
- Base executed trades: 1,919.
- Stress executed trades: 1,919.
- Base/Stress execution coverage: ≥95% in every true cell.

## Economic result
0/8 Base cells cleared the ₹5,000 mean-weekly + ₹5,000 median-weekly + ≥70% positive-week discovery gate.
0/8 Stress cells cleared the same gate.

Best true cell in both frictions was HIGH_VOL × FADE × 15:10:
- Base: total net +₹9,513.35, mean weekly +₹73.75, median +₹171.05, positive weeks 54.26%, max drawdown −₹33,072.41.
- Stress: total net +₹204.60, mean weekly +₹1.59, median +₹111.08, positive weeks 51.94%, max drawdown −₹35,736.13.

The other seven true cells were negative in both friction regimes.
One true cell exceeded the mean-weekly result of all five fixed null permutations in both Base and Stress, but remained far below the preregistered economic gate. This does not support promotion.

## Statistical disposition
No WFA/OOS was authorized because the discovery gate failed 0/8 cells in both friction regimes. No post-result threshold, interval, mapping, exit, spread-width or cost tuning is permitted.

## Engineering closures
- E0381 CLOSED: 09:30 spot/ATM eligibility hardening.
- E0382 CLOSED: Actions-run observability defect; direct Actions run collection established authoritative monitoring.
- E0383 CLOSED: constant-range unit-test fixture created zero rolling variance.
- E0384 CLOSED: explicit post-warm-up eligibility gate added.
- E0385 CLOSED: expiry gate initially mapped boolean eligibility flags instead of eligible dates.

## Final conclusion
Phase 38 is RETIRED — NEGATIVE DISCOVERY. The frozen opening-range volatility structure did not meet the weekly economic gate after realistic costs and doubled slippage.

## Reproducibility
Key files:
- docs/phase38_plan.md
- docs/phase38_literature_review.md
- research/phase38_opening_volatility_structure.py
- tests/test_phase38_opening_volatility_structure.py
- .github/workflows/phase-38-main-launcher.yml
- reports/phase38/