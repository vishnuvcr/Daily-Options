# Error Log

| ID | Date | Phase | Error / failed assumption | Impact | Correction | Status |
|---|---|---|---|---|---|---|
| E0001 | 2026-09-23 | 0 | README read returned 404 because repository has no contents | Initial audit looked like a missing repo | Confirmed repo exists but is empty; bootstrap state accepted | CLOSED |
| E0002 | 2026-09-23 | 0 | Paytm Money search surfaced older Rs 10/Rs 15/Rs 20 pages with different user cohorts | Could underestimate current brokerage | Use 2024 Paytm Money pricing update: flat Rs 20 across segments effective 2025-01-15 | CLOSED |
| E0003 | 2026-09-23 | 0 | NSE permitted-lot-size CSV could not be retrieved through the web content reader | Exact table not embedded yet | Use NSE contract-information page as authoritative source and create CI downloader/cacher | OPEN |
| E0004 | 2026-09-23 | 0 | Paytm Money current pricing page renders some trading-charge values dynamically | Static text does not expose all charges | Pin statutory/exchange components from authoritative sources and keep broker items configurable | OPEN |

Every subsequent error gets a new row. Fixes are never silently discarded.

| E0067 | 2026-09-24 | Phase 8 v2 | Run 35937700542 still executed an older/insufficient executable-entry query and raised `KeyError: 'open'` at entry-price persistence | No P&L produced | Current branch query includes `open`; added an explicit schema guard and triggered a fresh branch commit | OPEN — awaiting fresh workflow |
| E0068 | 2026-09-24 | Phase 9 | Run 35937112092 attempt 3 was cancelled by the GitHub runner shutdown signal during base computation | No P&L produced | Re-ran the cancelled job; fresh attempt is now executing base friction | OPEN |
| E0069 | 2026-09-24 | Phase 10 | Run 35937773719 raised `AttributeError: 'Series' object has no attribute 'leader'` during entry construction | No P&L produced | Replaced attribute access with explicit Series key access and committed the fix | OPEN — awaiting fresh workflow |

| E0070 | 2026-09-24 | Environment | Local container could not resolve github.com during an attempted branch clone, so local CI reproduction was unavailable | No effect on repository workflows | Use GitHub Actions as the authoritative branch execution environment; no result is inferred from the failed local clone | CLOSED |
