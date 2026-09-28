# Phase 39 Error Log

| ID | Date | Stage | Description | Impact | Resolution | Status |
|---|---|---|---|---|---|---|
| E0390 | 2026-09-28 | Preregistration | Frozen opening-move implied/realized family registered before numerical execution | None | Freeze full signal/execution/cost/null specification | CLOSED |
| E0391 | 2026-09-28 | Unit tests | Python banker rounding mis-mapped an exact ₹25 half-step | No data/P&L | Deterministic half-up ₹50 rounding | CLOSED |
| E0392 | 2026-09-28 | Data gate | Exact 09:30-only option lookup found no rows in the pinned source | No P&L | Latest positive quote at or before the fixed 09:30 cutoff | CLOSED |
| E0393 | 2026-09-28 | Data gate | Cutoff was applied after row ranking, discarding valid earlier quotes | No P&L | Apply cutoff in source filter before ROW_NUMBER | CLOSED |
| E0394 | 2026-09-28 | Data gate | Dataset trading_day was not the reliable signal-date join key | No P&L | Derive option trade date from timestamp in Asia/Kolkata | CLOSED |
| E0395 | 2026-09-28 | Feature construction | Contiguous-row rolling z-score propagated 16 isolated IV gaps into 380 missing z-scores | Initial gate fail; no economics | Use prior 60 valid MOVE_RATIO observations, no imputation/forward-fill | CLOSED |
| E0396 | 2026-09-28 | IV mapping | Query trade_date became pandas Timestamp while request keys were Python dates | No P&L | Normalize query dates before key matching | CLOSED |
| E0397 | 2026-09-28 | Execution mapping | Execution request dates/expiry values had Python-date vs Timestamp mismatches | No P&L | Normalize execution keys; minimum true-cell coverage 97.45% on clean run | CLOSED |
| E0398 | 2026-09-28 | Final discovery | Clean run failed the frozen weekly economic gate in all 8 Base and all 8 Stress cells | No WFA/OOS | Retire Phase 39 as negative discovery; no tuning | CLOSED |
