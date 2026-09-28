# Phase 39 — NIFTY Option-Implied vs Realized Opening-Move Dislocation
## Final Research Manuscript

**Status:** CLOSED — NEGATIVE DISCOVERY  
**Authoritative workflow:** 36465244174  
**Branch:** `phase-39-implied-realized-opening-dislocation-v1`

## Abstract
Phase 39 tested whether the magnitude of the first 15-minute NIFTY move, normalized by a contemporaneous option-implied 15-minute move, could identify a reproducible directional edge for a defined-risk debit spread. The frozen design used a strictly prior 60-valid-observation MOVE_RATIO z-score, HIGH/LOW dislocation states at ±0.75, CONTINUE/FADE mappings, 09:31 entry, 10:30/15:10 exits, one-lot 200-point debit spreads, historical lot sizes, Paytm Money/NSE/statutory charges and Base/Stress slippage of ₹0.20/₹0.40 per option-price unit/order.

The clean authoritative run passed all integrity gates. Of 1,234 raw sessions, 1,174 were post-warm-up; 1,158 were feature-eligible (98.64%). Direct IV coverage was 98.64%, expiry mapping was 100%, prior-information violations were zero, and the minimum true-cell execution coverage was 97.45%. Accounting reconciliation passed in every true cell.

Economically, 0/8 Base and 0/8 Stress cells passed the frozen weekly promotion gate. The best cell, LOW_DISLOCATION × CONTINUE × 15:10, produced only +₹48.75 mean weekly net in Base and −₹18.24 in Stress, with median weekly net negative in both and positive-week rates below 45%. No WFA/OOS or promotion was authorized.

## 1. Research question
Does a NIFTY opening move that is unusually large or small relative to the contemporaneous ATM option-implied 15-minute move predict continuation or reversal strongly enough to generate at least ₹5,000 net per completed trading week after realistic costs?

## 2. Aims and objectives
1. Construct an option-implied opening-move estimate available by the 09:30 IST information cutoff.
2. Compare the realized 09:15–09:29 NIFTY move with that implied move.
3. Standardize the ratio using only the prior 60 valid MOVE_RATIO observations, with no imputation.
4. Test fixed continuation and fade mappings using a one-lot 200-point debit spread.
5. Quantify Base and doubled-slippage Stress after Paytm Money/NSE/statutory costs.
6. Compare true cells with five fixed permutation-null controls.

## 3. Scientific methodology
Realized opening return:
[
R_{open}=(NIFTY_{09:29}-NIFTY_{09:15})/NIFTY_{09:15}
]

ATM strike is the deterministic nearest ₹50 to the 09:30 NIFTY close. ATM implied volatility is the simple mean of valid CE and PE implied volatilities for the nearest NIFTY expiry strictly after the signal date. Option quotes are the latest valid positive observations at or before 09:30 IST.

Implied 15-minute move:
[
M_{imp}=sigma_{ATM}sqrt{15/390}
]

MOVE_RATIO:
[
MOVE_RATIO=|R_{open}|/M_{imp}
]

The z-score uses the strictly prior 60 valid MOVE_RATIO observations. Missing observations are not imputed or forward-filled.

States:
- HIGH_DISLOCATION: z ≥ +0.75
- LOW_DISLOCATION: z ≤ −0.75
- otherwise no trade

Direction:
- CONTINUE follows the opening return.
- FADE takes the opposite direction.

Execution:
- entry 09:31 option open;
- exits 10:30 and 15:10 option close;
- one NIFTY lot;
- 200-point defined-risk debit spread;
- historical lot sizes;
- fixed brokerage/statutory cost model;
- Base slippage ₹0.20/order and Stress ₹0.40/order.

## 4. Data and integrity results

| Gate | Result | Requirement |
|---|---:|---:|
| Raw NIFTY sessions | 1,234 | — |
| Post-warm-up sessions | 1,174 | — |
| Feature eligible | 1,158 / 1,174 = **98.64%** | ≥95% |
| Direct IV coverage | **98.64%** | ≥95% |
| Expiry mapping | **100%** | ≥95% |
| Prior-information violations | **0** | 0 |
| Minimum true-cell execution coverage | **97.45%** | ≥95% |
| True cells | **8** | 8 |
| Accounting residual | **0.0 maximum** | reconciled |

All data and execution gates passed.

## 5. Economic results

| Cell | Base mean/week | Base median/week | Base positive weeks | Base total net | Stress mean/week | Stress median/week | Stress positive weeks | Stress total net |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HIGH_DISLOCATION × CONTINUE × 10:30 | −211.57 | −221.47 | 39.87% | −33,428.80 | −273.88 | −272.39 | 36.71% | −43,272.80 |
| HIGH_DISLOCATION × CONTINUE × 15:10 | −294.18 | −383.88 | 33.54% | −46,480.72 | −356.49 | −430.94 | 32.28% | −56,324.72 |
| HIGH_DISLOCATION × FADE × 10:30 | −249.97 | −218.55 | 36.94% | −39,245.42 | −312.42 | −277.61 | 31.85% | −49,049.42 |
| HIGH_DISLOCATION × FADE × 15:10 | −355.90 | −132.25 | 45.86% | −55,876.48 | −418.09 | −192.25 | 43.95% | −65,640.48 |
| LOW_DISLOCATION × CONTINUE × 10:30 | −290.32 | −258.86 | 32.04% | −52,548.47 | −357.46 | −318.86 | 29.28% | −64,700.47 |
| **LOW_DISLOCATION × CONTINUE × 15:10** | **+48.75** | **−194.98** | **44.51%** | **+8,871.89** | **−18.24** | **−231.43** | **43.96%** | **−3,320.11** |
| LOW_DISLOCATION × FADE × 10:30 | −220.33 | −208.98 | 37.70% | −40,320.12 | −287.17 | −254.97 | 35.52% | −52,552.12 |
| LOW_DISLOCATION × FADE × 15:10 | −407.94 | −388.22 | 36.07% | −74,652.29 | −474.56 | −439.58 | 34.97% | −86,844.29 |

Promotion outcome: **0/8 Base** and **0/8 Stress** cells passed the mean ≥₹5,000, median ≥₹5,000 and positive-week rate ≥70% gate.

The best Base cell's profit factor was 1.043, but its median week remained negative and Stress turned negative.

## 6. Null controls
Five fixed permutation-null seeds were evaluated for every cell in both friction regimes.

For LOW_DISLOCATION × CONTINUE × 15:10:
- Base true mean = +₹48.75/week.
- Base null means = +₹207.85, −₹175.49, +₹0.57, −₹11.30, −₹66.88.
- Stress true mean = −₹18.24/week.
- Stress null means = +₹137.90, −₹244.05, −₹69.74, −₹82.85, −₹136.85.

The true cell did not exceed all five null means in either friction regime. No true cell did.

## 7. Cost, risk and accounting analysis
Across the eight true cells, every accounting residual was exactly zero in the persisted summaries. The best Base cell still had a maximum drawdown of −₹22,396.91; Stress maximum drawdown was −₹25,491.31. Net P&L explicitly subtracts gross trading friction, slippage and transaction/statutory costs.

## 8. Discussion
The clean data and execution gates remove a data-coverage explanation for the poor economics. The family did not produce the required weekly edge, and the modest Base positive result in one cell disappeared under Stress.

The result does not justify post-result changes to the lookback, z thresholds, IV horizon, expiry selection, spread width, direction mapping, entry or exits. Such changes would turn the discovery stage into result-driven parameter selection.

## 9. Strengths
- Strong feature and execution coverage.
- Strict no-lookahead barrier.
- Explicit cost/slippage model and historical lot sizes.
- Fixed finite grid.
- Five permutation-null controls per cell.
- Full accounting reconciliation.
- Engineering defects were quarantined before accepted economics.

## 10. Limitations
- ATM IV is model-derived and inherits quote/model noise.
- Only one opening horizon and one spread width were tested.
- Discovery-stage failure correctly prevented WFA/OOS.
- The hypothesis is specific to the first 15 minutes and may not generalize to other horizons.

## 11. Conclusion
**Phase 39 is retired as negative discovery.** The option-implied versus realized opening-move dislocation family did not achieve the ₹5,000/week consistency objective after realistic costs and doubled slippage.

## 12. Future direction
The next distinct preregistered family is Phase 40: prior-day ATM IV / realized-volatility context combined with next-session overnight-gap dislocation normalized by the prior-day one-session implied move. Phase 39 parameters are not being reused or retuned.

## Appendix — Reproducibility
- `docs/phase39_plan.md`
- `docs/phase39_literature_review.md`
- `docs/phase39_status.md`
- `docs/phase39_error_log.md`
- `research/phase39_implied_realized_opening_dislocation.py`
- `tests/test_phase39_implied_realized_opening_dislocation.py`
- `.github/workflows/phase-39-implied-realized-opening-dislocation.yml`
- `reports/phase39/`
