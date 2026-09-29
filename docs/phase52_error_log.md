# Error Log — Phase 52

| ID | Date | Stage | Error | Effect | Correction | Status |
|---|---|---|---|---|---|---|
| E052-000 | 2026-09-29 | Preregistration | None | None | N/A | CLOSED |

| E052-001 | 2026-09-29 | Pre-execution review | Information-barrier violation count used the full panel instead of post-warm-up rows | Could contaminate the gate with intentional warm-up rows | Count violations only on post-warm-up panel; feature construction and thresholding unchanged | CLOSED |

| E052-001 | 2026-09-29 | Base discovery runs 36540878666 / 36540906389 | build_signals attempted int(NaN) for rows with missing 09:30 ATM strike despite feature_eligible being true | No Base/Stress P&L accepted | Signal construction now requires non-null ATM and expiry before trade-cell expansion; research definition and gates unchanged | CLOSED |
