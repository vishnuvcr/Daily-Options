# Iron Condor Adjustment 

- Video ID: `1V-06qTH5Rc`
- Source URL: https://www.youtube.com/watch?v=1V-06qTH5Rc
- Candidate families: iron_fly, iron_condor, leaps
- Research status: SOURCE-FIDELITY REVIEW
- Backtest allowed: NO

## Structured source evidence
### adjustment_action — SOURCE-EXPLICIT
- move — source timestamp 340919.0s
- move — source timestamp 342520.0s
- move — source timestamp 345960.0s
- move — source timestamp 348800.0s
- move — source timestamp 352240.0s
- move — source timestamp 354440.0s
- move — source timestamp 358320.0s
- move — source timestamp 429240.0s

### adjustment_day — UNSPECIFIED
- UNSPECIFIED

### day_count_reference — UNSPECIFIED
- UNSPECIFIED

### delta_reference — UNSPECIFIED
- UNSPECIFIED

### entry_action — CONFLICTING
- sell — source timestamp 72640.0s
- buy — source timestamp 72640.0s
- sell — source timestamp 75080.0s
- buy — source timestamp 75080.0s
- sell — source timestamp 76920.0s
- buy — source timestamp 76920.0s
- sell — source timestamp 79080.0s
- buy — source timestamp 79080.0s

### entry_day — UNSPECIFIED
- UNSPECIFIED

### exit_day — UNSPECIFIED
- UNSPECIFIED

### expiry_reference — UNSPECIFIED
- UNSPECIFIED

### lot_reference — SOURCE-EXPLICIT
- 10:00 — source timestamp 572480.0s
- 10:00 — source timestamp 575720.0s
- 10:00 — source timestamp 577960.0s
- 10:00 — source timestamp 581240.0s
- 10:00 — source timestamp 583600.0s
- 10:00 — source timestamp 585040.0s
- 10:00 — source timestamp 587120.0s

### premium_zone — UNSPECIFIED
- UNSPECIFIED

### ratio_reference — SOURCE-EXPLICIT
- 10:00 — source timestamp 572480.0s
- 10:00 — source timestamp 575720.0s
- 10:00 — source timestamp 577960.0s
- 10:00 — source timestamp 581240.0s
- 10:00 — source timestamp 583600.0s
- 10:00 — source timestamp 585040.0s
- 10:00 — source timestamp 587120.0s

### stop_reference — CONFLICTING
- stop — source timestamp 137440.0s
- stop here, because now I'm going to tell you — source timestamp 140520.0s
- stop here, because now I'm going to tell you some negative points — source timestamp 143520.0s
- stop here, because now I'm going to tell you some negative points — source timestamp 146959.0s
- stop here, because now I'm going to tell you some negative points — source timestamp 149120.0s
- stop here, because now I'm going to tell you some negative points — source timestamp 150440.0s
- stop here, because now I'm going to tell you some negative points — source timestamp 152840.0s
- stop loss is — source timestamp 215640.0s

### strike_reference — SOURCE-EXPLICIT
- out of the money — source timestamp 54360.0s
- out of the money — source timestamp 55920.0s
- out of the money — source timestamp 58000.0s
- out of the money — source timestamp 60080.0s
- out of the money — source timestamp 63320.0s
- out of the money — source timestamp 66160.0s
- out of the money — source timestamp 68000.0s
- out of the money — source timestamp 169800.0s

### target_reference — UNSPECIFIED
- UNSPECIFIED

### time_reference — SOURCE-EXPLICIT
- 10:00 — source timestamp 572480.0s
- 10:00 — source timestamp 575720.0s
- 10:00 — source timestamp 577960.0s
- 10:00 — source timestamp 581240.0s
- 10:00 — source timestamp 583600.0s
- 10:00 — source timestamp 585040.0s
- 10:00 — source timestamp 587120.0s

### underlying — SOURCE-EXPLICIT
- Nifty — source timestamp 273360.0s
- Nifty — source timestamp 276919.0s
- Nifty — source timestamp 279120.0s
- Nifty — source timestamp 281160.0s
- Nifty — source timestamp 283360.0s
- Nifty — source timestamp 285760.0s
- Nifty — source timestamp 288560.0s

### width_reference — SOURCE-EXPLICIT
- 45 — source timestamp 279120.0s
- 45 — source timestamp 281160.0s
- 45 — source timestamp 283360.0s
- 45 — source timestamp 285760.0s
- 45 — source timestamp 288560.0s
- 45 — source timestamp 289720.0s
- 45 — source timestamp 292200.0s

## External corroboration
- Source: https://www.youtube.com/watch?v=1V-06qTH5Rc
- Source type: YouTube description
- Describes defending an iron condor when the market keeps moving or reverses.
- Discusses adding far-OTM options, widening the setup, breakevens/theta and extending the structure.
- Research use: supports a distinct adjustment-family candidate; exact trigger, strikes, sizing and stop remain transcript-dependent

## Rule status
- Entry rule: UNRESOLVED until exact trigger is reconciled.
- Strike rule: UNRESOLVED until exact construction is reconciled.
- Adjustment rule: UNRESOLVED until trigger/action pair is reconciled.
- Stop rule: UNRESOLVED until numeric or event condition is reconciled.
- Target/exit rule: UNRESOLVED until numeric/time condition is reconciled.
- Capital/lots: UNRESOLVED until historically reproducible.
- Paytm Money/NSE costs: NOT APPLIED IN PHASE 27.3.
- Backtest promotion: BLOCKED.
