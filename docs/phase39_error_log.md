# Phase 39 Error Log

Any defect discovered before numerical acceptance will be logged here and in docs/error_log.md. A defective run is quarantined and cannot supply strategy evidence.

| ID | Date | Stage | Description | Impact | Resolution | Status |
|---|---|---|---|---|---|---|
| E0390 | 2026-09-28 | Phase 39 preregistration | New option-implied-versus-realized opening-move family was frozen after Phase 38 closure; no numerical execution yet | None | Freeze the full signal/execution/cost/null specification before data access | CLOSED — preregistration |
| E0391 | 2026-09-28 | Phase 39 unit tests / run 36409062624 | ATM strike rounding used Python banker’s rounding, so an exact half-step such as 22525 mapped to 22500 rather than the frozen nearest-₹50 half-up convention | No data acquisition or P&L occurred; run quarantined | Use deterministic half-up rounding with floor(x+0.5); rerun the full unit suite before data access | OPEN — corrected pending clean rerun |
