# Error Log — Phase 49

| ID | Date | Stage | Error | Effect | Correction | Status |
|---|---|---|---|---|---|---|
| E049-000 | 2026-09-29 | Preregistration | None | None | N/A | CLOSED |

| E049-001 | 2026-09-29 | Pre-execution review | Copied Phase-48 workflow retained stale Phase-48 checkout/push refs | No numerical result | Corrected checkout, push and rebase refs to phase-49-prior-range-regime-gap-v1; preregistered design unchanged | CLOSED |

| E049-002 | 2026-09-29 | Phase 49 data gate run 36539272016 | Rolling quantiles required 60 populated rows, which incorrectly treated missing session range observations as warm-up failures and reduced feature eligibility to 83.13% | Base/Stress discovery skipped; no numerical P&L accepted | Reimplemented the regime thresholds using the last 60 valid completed range observations strictly before the prior session; coverage gate unchanged | CLOSED |
