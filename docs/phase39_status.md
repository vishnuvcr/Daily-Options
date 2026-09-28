# Phase 39 Status

## Final state
**CLOSED — NEGATIVE DISCOVERY. No WFA/OOS or promotion.**

Authoritative clean workflow: **36465244174**  
Branch: `phase-39-implied-realized-opening-dislocation-v1`

## Frozen experiment
- Study window: 2021-07-01 through 2026-08-31.
- Realized move: NIFTY 09:15 open to 09:29 close.
- Signal option IV: ATM CE/PE from the nearest expiry strictly after the signal date, using the latest valid positive quote at or before 09:30 IST.
- MOVE_RATIO = absolute realized opening return / ATM implied 15-minute move.
- Standardization: strictly prior 60 **valid MOVE_RATIO observations**, with no imputation or forward-fill.
- States: HIGH_DISLOCATION / LOW_DISLOCATION at ±0.75 z.
- CONTINUE/FADE mappings.
- Entry 09:31, exits 10:30/15:10, one-lot 200-point debit spread, historical lot sizes.
- Base/Stress slippage ₹0.20/₹0.40 per option-price unit/order and the established Paytm Money/NSE/statutory cost model.
- Five fixed permutation null seeds.

## Data and execution integrity
- Raw sessions: 1,234.
- Post-warm-up sessions: 1,174.
- Feature-eligible sessions: 1,158 / 1,174 = **98.64%**.
- Direct IV input coverage: **98.64%**.
- Expiry mapping coverage: **100%**.
- Prior-information violations: **0**.
- Minimum execution quote coverage across the 8 true cells: **97.45%**.
- Accounting reconciliation: passed with maximum residual 0.0 in the persisted true-cell summaries.

## Economic result
**0/8 Base** cells and **0/8 Stress** cells passed the frozen discovery gate requiring mean weekly net ≥₹5,000, median weekly net ≥₹5,000 and positive-week rate ≥70%.

Best Base and Stress cell:
**LOW_DISLOCATION × CONTINUE × 15:10**
- Base: 289 executed trades; 182 weeks; total net **+₹8,871.89**; mean weekly **+₹48.75**; median weekly **−₹194.98**; positive-week rate **44.51%**; profit factor **1.043**; maximum drawdown **−₹22,396.91**.
- Stress: 289 executed trades; 182 weeks; total net **−₹3,320.11**; mean weekly **−₹18.24**; median weekly **−₹231.43**; positive-week rate **43.96%**; profit factor **0.985**; maximum drawdown **−₹25,491.31**.

All other true cells had negative total net P&L in both frictions.

## Null controls
Five fixed permutation null seeds were run for every cell in both Base and Stress. No true cell exceeded all five null mean-weekly results in either friction regime. The best Base cell's null means were +₹207.85, −₹175.49, +₹0.57, −₹11.30 and −₹66.88 per week; its true mean was only +₹48.75. The best Stress cell's null means were +₹137.90, −₹244.05, −₹69.74, −₹82.85 and −₹136.85; its true mean was −₹18.24.

## Statistical disposition
No WFA/OOS was authorized because 0/8 cells cleared the discovery gate in either friction regime. No post-result tuning of the IV horizon, 60-observation lookback, ±0.75 thresholds, timing, expiry rule, spread width or cost model is permitted.

## Final conclusion
**Phase 39 is RETIRED — NEGATIVE DISCOVERY.** The option-implied versus realized opening-move dislocation family did not provide a reproducible ₹5,000/week edge after realistic costs and doubled slippage.

## Reproducibility
- `docs/phase39_plan.md`
- `docs/phase39_literature_review.md`
- `research/phase39_implied_realized_opening_dislocation.py`
- `tests/test_phase39_implied_realized_opening_dislocation.py`
- `.github/workflows/phase-39-implied-realized-opening-dislocation.yml`
- `reports/phase39/`
