# Phase 31.8 Error / Audit Log

| ID | Stage | Description | Impact | Resolution | Status |
|---|---|---|---|---|---|
| E0454 | Provenance audit | Persisted global-data manifest was generated with yfinance 1.7.0 while the newly authored workflow pins 0.2.66 | No numerical effect on the completed run because the run reused the persisted cache and did not re-download; reproducibility metadata must remain explicit | Preserve the exact cached files and manifest hashes; log the runtime mismatch and prevent silent source substitution | CLOSED — provenance audit |
