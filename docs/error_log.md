# Error Log

| ID | Date | Phase | Error / failed assumption | Impact | Correction | Status |
|---|---|---|---|---|---|---|
| E0001 | 2026-09-23 | 0 | README read returned 404 because repository has no contents | Initial audit looked like a missing repo | Confirmed repo exists but is empty; bootstrap state accepted | CLOSED |
| E0002 | 2026-09-23 | 0 | Paytm Money search surfaced older Rs 10/Rs 15/Rs 20 pages with different user cohorts | Could underestimate current brokerage | Use 2024 Paytm Money pricing update: flat Rs 20 across segments effective 2025-01-15 | CLOSED |
| E0003 | 2026-09-23 | 0 | NSE permitted-lot-size CSV could not be retrieved through the web content reader | Exact table not embedded yet | Use NSE contract-information page as authoritative source and create CI downloader/cacher | OPEN |
| E0004 | 2026-09-23 | 0 | Paytm Money current pricing page renders some trading-charge values dynamically | Static text does not expose all charges | Pin statutory/exchange components from authoritative sources and keep broker items configurable | OPEN |
| E0005 | 2026-09-23 | 1 | Phase-1 workflow parsed YAML but initially did not install PyYAML | Manual workflow would fail before tests | Added pyyaml to workflow dependency installation before execution | CLOSED |

Every subsequent error gets a new row. Fixes are never silently discarded.
