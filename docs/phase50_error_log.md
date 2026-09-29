# Error Log — Phase 50

| ID | Date | Stage | Error | Effect | Correction | Status |
|---|---|---|---|---|---|---|
| E050-000 | 2026-09-29 | Preregistration | None | None | N/A | CLOSED |

| E050-001 | 2026-09-29 | Pre-execution review | Copied Phase-48 workflow retained stale Phase-48 branch and script/test filenames | No numerical result | Corrected checkout/push refs and engine/test filenames to Phase 50 | CLOSED |

| E050-002 | 2026-09-29 | Workflow execution 36539830156 | Older workflow revision used stale phase-48 checkout ref, so checkout failed before any numerical work | No P&L | Current workflow branch ref is phase-50-opening-location-range-gap-v1 | CLOSED |
| E050-003 | 2026-09-29 | Workflow preflight | Base/Stress commands still referenced the copied Phase-48 engine filename | Would run the wrong implementation if not corrected | Repointed both commands to research/phase50_opening_location_range_gap.py | CLOSED |

| E050-004 | 2026-09-29 | Authoritative run 36539948879 | None | None | Data gate, Base, Stress, validation and accounting passed; phase closed negative | CLOSED |
