# Error Log — Alternating OTM Buy/Sell Phase C

| ID | Date | Stage | Error | Effect | Correction | Status |
|---|---|---|---|---|---|---|
| EALTC-000 | 2026-09-29 | Preregistration | None | No failure recorded | N/A | OPEN — awaiting first execution |

| EALTC-001 | 2026-09-29 | Feature validation | The rolling 20-session prior-range feature is intentionally NaN during warm-up, but the first implementation treated any NaN as a schema failure | Run 36536750155 stopped before candidate evaluation | Preserve warm-up rows in the rule mask; use non-null values to calculate thresholds; do not interpret missing warm-up state as an economic exclusion | CLOSED |
