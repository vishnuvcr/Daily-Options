# Phase 43 Final Result — NEGATIVE DISCOVERY

## Authoritative run
Workflow **36471290988** completed the clean preregistered run after engineering corrections. Data gate, Base, Stress and validation all passed.

## Data integrity
- Raw sessions: 1,228
- Post-warm-up sessions: 1,168
- Feature-eligible sessions: 1,160 = **99.3151%**
- Feature coverage: **100%**
- Expiry mapping: **100%**
- Prior-information violations: **0**
- True cells: **20**
- Null controls: **5 × 20 = 100 cells per friction regime**
- Execution coverage: ~97.9%–99.2% across true cells
- Accounting reconciliation: PASS

## Economic result
No true cell met the promotion gate in either Base or Stress.

Best true cell in both regimes: **THURSDAY | FADE | H15_10**.
- Base: total net **₹11,389.69**, mean weekly **₹46.87**, median weekly **−₹1,147.48**, positive-week rate **39.92%**, execution coverage **98.78%**.
- Stress: total net **₹1,421.44**, mean weekly **₹5.85**, median weekly **−₹1,184.97**, positive-week rate **39.51%**, execution coverage **98.78%**.

All other cells were below the ₹5,000/week mean and median thresholds and/or the 70% positive-week threshold. No WFA/OOS was authorized.

## Null controls
The fixed weekday-label permutation controls did not produce a promoted null cell. Null economics remained broadly negative, providing no evidence that the observed small positive Thursday/FADE result was a robust exploitable effect.

## Conclusion
The preregistered weekday × opening-gap direction family is **CLOSED — NEGATIVE DISCOVERY**. The result does not support a ₹5,000/week trading strategy. No weekday, mapping or exit is selected for further tuning.

## Evidence
- reports/phase43/gate/data_gate.json
- reports/phase43/base/true_cell_summary_base.csv
- reports/phase43/stress/true_cell_summary_stress.csv
- reports/phase43/base/null_summary.csv
- reports/phase43/stress/null_summary.csv
