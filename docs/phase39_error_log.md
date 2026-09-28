# Phase 39 Error Log

Any defect discovered before numerical acceptance will be logged here and in docs/error_log.md. A defective run is quarantined and cannot supply strategy evidence.

| ID | Date | Stage | Description | Impact | Resolution | Status |
|---|---|---|---|---|---|---|
| E0390 | 2026-09-28 | Phase 39 preregistration | New option-implied-versus-realized opening-move family was frozen after Phase 38 closure; no numerical execution yet | None | Freeze the full signal/execution/cost/null specification before data access | CLOSED — preregistration |
| E0391 | 2026-09-28 | Phase 39 unit tests / run 36409062624 | ATM strike rounding used Python banker’s rounding, so an exact half-step such as 22525 mapped to 22500 rather than the frozen nearest-₹50 half-up convention | No data acquisition or P&L occurred; run quarantined | Use deterministic half-up rounding with floor(x+0.5); rerun the full unit suite before data access | OPEN — corrected pending clean rerun |

| E0392 | 2026-09-28 | Phase 39 data gate / run 36409163981 | Exact 09:30 option-bar filtering produced 0/1,174 IV-eligible sessions because the pinned option partitions do not consistently contain an exact 09:30 observation | No P&L; data gate failed before Base/Stress | Use the audited latest-positive option observation at or before the fixed 09:30 information cutoff, preserving strict no-lookahead timing; no threshold or economic rule changes | OPEN — corrected pending rerun |

| E0393 | 2026-09-28 | Phase 39 data gate / run 36409329395 | The E0392 pre-cutoff quote query ranked the latest option row before applying the 09:30 cutoff, so a later row could receive row_number=1 and then be filtered out, leaving 0 IV inputs | No P&L accepted; data gate failed before Base/Stress | Move the 09:30 cutoff predicate into the source WHERE clause before ROW_NUMBER; retain latest valid positive quote at or before cutoff | OPEN — corrected pending rerun |

| E0394 | 2026-09-28 | Phase 39 data gate / run 36409544862 | The pinned option source’s trading_day field was not a safe signal-date join key; using it produced zero snapshot IV rows despite the audited timestamp-based loader succeeding on the same source | No P&L accepted; data gate failed before Base/Stress | Derive option trade date from the option timestamp itself and keep the <=09:30 local-time cutoff; rerun authoritative gate | OPEN — corrected pending rerun |

| E0395 | 2026-09-28 | Phase 39 source diagnostic / run 36409908831 | Diagnostic compared pandas Timestamp against datetime.date before reading source rows | No strategy/data evidence; diagnostic aborted before source inspection | Normalize the diagnostic trade date to Python date before expiry/date comparisons | OPEN — corrected pending rerun |

| E0396 | 2026-09-28 | Phase 39 data gate / run 36410150122 | query_0930_iv returned valid source rows, but pandas converted the query trade_date to Timestamp while request keys were Python date objects, so CE/PE rows never matched | No P&L accepted; data gate reported 0 IV inputs | Normalize query trade_date to Python date before key comparison | OPEN — corrected pending rerun |
