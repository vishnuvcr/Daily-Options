# Strategy Error Log — OTM1 / 2xOTM2 Ratio Backspread

| ID | Date | Phase | Defect | Impact | Correction | Status |
|---|---|---|---|---|---|---|
| EOTM12-001 | 2026-09-29 | A workflow validation | Matrix friction expression was initially malformed/escaped | No evidentiary P&L | Corrected workflow expression | CLOSED |
| EOTM12-002 | 2026-09-29 | A data acquisition | huggingface_hub was not installed before snapshot_download | Base/Stress run 36527056729 stopped before P&L | Add huggingface_hub dependency | CLOSED; rerun pending |
| EOTM12-003 | 2026-09-29 | A engine | DuckDB timestamp-with-time-zone casting required explicit timezone normalization | No P&L accepted | Normalize to Asia/Kolkata before TIME filtering | CLOSED |
