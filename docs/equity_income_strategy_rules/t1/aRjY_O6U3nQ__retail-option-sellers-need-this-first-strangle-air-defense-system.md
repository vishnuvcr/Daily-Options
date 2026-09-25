# Retail Option Sellers Need This First - STRANGLE AIR DEFENSE SYSTEM

- Video ID: `aRjY_O6U3nQ`
- Source URL: https://www.youtube.com/watch?v=aRjY_O6U3nQ
- Candidate families: iron_condor, ratio_spread, strangle, jade_lizard
- Research status: SOURCE-FIDELITY REVIEW
- Backtest allowed: NO

## Structured source evidence
### adjustment_action — CONFLICTING
- add — source timestamp 366600.0s
- add — source timestamp 369240.0s
- add — source timestamp 373280.0s
- add — source timestamp 375560.0s
- add — source timestamp 377720.0s
- add — source timestamp 380600.0s
- add — source timestamp 383560.0s
- hedge — source timestamp 635520.0s

### adjustment_day — UNSPECIFIED
- UNSPECIFIED

### day_count_reference — UNSPECIFIED
- UNSPECIFIED

### delta_reference — SOURCE-EXPLICIT
- 0.2 — source timestamp 99200.0s
- 0.2 — source timestamp 102000.0s
- 0.2 — source timestamp 104000.0s
- 0.2 — source timestamp 106720.0s
- 0.2 — source timestamp 109800.0s
- 0.2 — source timestamp 112280.0s
- 0.2 — source timestamp 115440.0s

### entry_action — SOURCE-EXPLICIT
- sell — source timestamp 55440.0s
- sell — source timestamp 58400.0s
- sell — source timestamp 60640.0s
- sell — source timestamp 63120.0s
- sell — source timestamp 65280.0s
- sell — source timestamp 68240.0s
- sell — source timestamp 70600.0s
- sell — source timestamp 71880.0s

### entry_day — UNSPECIFIED
- UNSPECIFIED

### exit_day — UNSPECIFIED
- UNSPECIFIED

### expiry_reference — UNSPECIFIED
- UNSPECIFIED

### lot_reference — SOURCE-EXPLICIT
- 3:25 — source timestamp 211840.0s
- 3:25 — source timestamp 213560.0s
- 3:25 — source timestamp 215920.0s
- 3:25 — source timestamp 218040.0s
- 3:25 — source timestamp 222160.0s
- 3:25 — source timestamp 225040.0s
- 3:25 — source timestamp 228320.0s

### premium_zone — SOURCE-EXPLICIT
- 0 — source timestamp 356960.0s
- 0 — source timestamp 359200.0s
- 0 — source timestamp 362000.0s
- 0 — source timestamp 363480.0s
- 0 — source timestamp 366600.0s
- 0 — source timestamp 369240.0s

### ratio_reference — SOURCE-EXPLICIT
- 3:25 — source timestamp 211840.0s
- 3:25 — source timestamp 213560.0s
- 3:25 — source timestamp 215920.0s
- 3:25 — source timestamp 218040.0s
- 3:25 — source timestamp 222160.0s
- 3:25 — source timestamp 225040.0s
- 3:25 — source timestamp 228320.0s

### stop_reference — UNSPECIFIED
- UNSPECIFIED

### strike_reference — CONFLICTING
- delta — source timestamp 99200.0s
- delta — source timestamp 102000.0s
- delta — source timestamp 104000.0s
- delta — source timestamp 106720.0s
- delta — source timestamp 109800.0s
- delta — source timestamp 112280.0s
- delta — source timestamp 115440.0s
- out of the money — source timestamp 347760.0s

### target_reference — CONFLICTING
- target exit is approximately 5 minutes — source timestamp 362000.0s
- target exit is approximately 5 minutes before the expiry — source timestamp 363480.0s
- target exit is approximately 5 minutes before the expiry — source timestamp 366600.0s
- target exit is approximately 5 minutes before the expiry — source timestamp 369240.0s
- target exit is approximately 5 minutes before the expiry — source timestamp 373280.0s
- target exit is approximately 5 minutes before the expiry — source timestamp 375560.0s
- target exit is approximately 5 minutes before the expiry — source timestamp 377720.0s

### time_reference — SOURCE-EXPLICIT
- 3:25 — source timestamp 211840.0s
- 3:25 — source timestamp 213560.0s
- 3:25 — source timestamp 215920.0s
- 3:25 — source timestamp 218040.0s
- 3:25 — source timestamp 222160.0s
- 3:25 — source timestamp 225040.0s
- 3:25 — source timestamp 228320.0s

### underlying — SOURCE-EXPLICIT
- Nifty — source timestamp 112280.0s
- Nifty — source timestamp 115440.0s
- Nifty — source timestamp 117080.0s
- Nifty — source timestamp 119040.0s
- Nifty — source timestamp 121080.0s
- Nifty — source timestamp 122720.0s
- Nifty — source timestamp 124280.0s
- Nifty — source timestamp 211840.0s

### width_reference — SOURCE-EXPLICIT
- 10 — source timestamp 356960.0s
- 10 — source timestamp 359200.0s
- 10 — source timestamp 362000.0s
- 10 — source timestamp 363480.0s
- 10 — source timestamp 366600.0s
- 10 — source timestamp 369240.0s
- 10 — source timestamp 373280.0s

## External corroboration
- Source: https://www.youtube.com/watch?v=aRjY_O6U3nQ
- Source type: YouTube description
- Uses India VIX and time to expiry to estimate NIFTY expected range.
- Explains 1-sigma and 2-sigma ranges and applies them to short strangles and iron condors.
- Describes adjusting positions when price moves toward the short strikes.
- Research use: supports family/payoff identification and regime-input requirements; does not establish exact strike/stop/exit rules

## Rule status
- Entry rule: UNRESOLVED until exact trigger is reconciled.
- Strike rule: UNRESOLVED until exact construction is reconciled.
- Adjustment rule: UNRESOLVED until trigger/action pair is reconciled.
- Stop rule: UNRESOLVED until numeric or event condition is reconciled.
- Target/exit rule: UNRESOLVED until numeric/time condition is reconciled.
- Capital/lots: UNRESOLVED until historically reproducible.
- Paytm Money/NSE costs: NOT APPLIED IN PHASE 27.3.
- Backtest promotion: BLOCKED.
