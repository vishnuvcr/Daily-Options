# Strategy Error Log — OTM1 / 2xOTM2 Ratio Backspread

| ID | Date | Phase | Defect | Impact | Correction | Status |
|---|---|---|---|---|---|---|
| EOTM12-001 | 2026-09-29 | A workflow validation | Matrix friction expression was initially malformed/escaped | No evidentiary P&L | Corrected workflow expression | CLOSED |
| EOTM12-002 | 2026-09-29 | A data acquisition | huggingface_hub was not installed before snapshot_download | Base/Stress run 36527056729 stopped before P&L | Add huggingface_hub dependency | CLOSED; rerun pending |
| EOTM12-003 | 2026-09-29 | A engine | DuckDB timestamp-with-time-zone casting required explicit timezone normalization | No P&L accepted | Normalize to Asia/Kolkata before TIME filtering | CLOSED |

| EOTM12-004 | 2026-09-29 | A engine | DuckDB 1.5 rejects direct TIMESTAMP WITH TIME ZONE -> TIME cast in option query | No P&L accepted; run stopped before first expiry | Normalize option timestamp to TIMESTAMP in the SELECT and TIME predicate | CLOSED; rerun pending |
| EOTM12-005 | 2026-09-29 | A engine/data selection | Corrected IST quote-time normalization still produced 0 complete four-leg trades in Base and Stress; the pipeline had no persisted stage-level diagnostics to identify whether entry timestamps, OTM strike availability, entry fills, or exits caused rejection | No P&L accepted; baseline remained non-evidentiary | Added per-session selection-stage diagnostics and persist diagnostics/coverage before raising the zero-trade error | OPEN — diagnostic rerun 36530427013 |
