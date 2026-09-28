# Phase 40 Error Log

| ID | Date | Stage | Description | Impact | Resolution | Status |
|---|---|---|---|---|---|---|
| E0400 | 2026-09-28 | Preregistration | New overnight-gap/implied-move family frozen before numerical execution | None | Freeze full signal, execution, cost, null and gate specification | CLOSED |
| E0401 | 2026-09-28 | Pre-run feature construction | Contiguous-row z-score would propagate missing GAP_RATIO rows into later states | Potentially understate feature coverage; no P&L | Use previous 60 valid GAP_RATIO observations, no imputation | CLOSED — pre-run |
| E0402 | 2026-09-28 | Pre-run information barrier | RV20 calculation included the current signal-day close instead of ending on the prior completed session | Would create look-ahead | Shift RV20 by one session so prior-day RV only uses prior data | CLOSED — pre-run |

| E0403 | 2026-09-28 | Phase 40 source diagnostic / run 36466038985 | Diagnostic compared a pandas Timestamp trade date with datetime.date expiry values | No strategy/data evidence; data gate did not run | Normalize diagnostic trade date to Python date before expiry comparison | CLOSED — pre-run |
