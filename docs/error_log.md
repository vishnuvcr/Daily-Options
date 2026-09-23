# Error Log

| ID | Date | Phase | Error / failed assumption | Impact | Correction | Status |
|---|---|---|---|---|---|---|
| E0001 | 2026-09-23 | 0 | README read returned 404 because repository has no contents | Initial audit looked like a missing repo | Confirmed repo exists but is empty; bootstrap state accepted | CLOSED |
| E0002 | 2026-09-23 | 0 | Paytm Money search surfaced older Rs 10/Rs 15/Rs 20 pages with different user cohorts | Could underestimate current brokerage | Use 2024 Paytm Money pricing update: flat Rs 20 across segments effective 2025-01-15 | CLOSED |
| E0003 | 2026-09-23 | 0 | NSE permitted-lot-size CSV could not be retrieved through the web content reader | Exact table not embedded yet | Use NSE contract-information page as authoritative source and create CI downloader/cacher | OPEN |
| E0004 | 2026-09-23 | 0 | Paytm Money current pricing page renders some trading-charge values dynamically | Static text does not expose all charges | Pin statutory/exchange components from authoritative sources and keep broker items configurable | OPEN |
| E0005 | 2026-09-23 | 1 | Phase-1 workflow parsed YAML but initially did not install PyYAML | Manual workflow would fail before tests | Added pyyaml to workflow dependency installation before execution | CLOSED |
| E0006 | 2026-09-23 | 2 | Baseline CI ran the tournament as a file and could not import the research package | Backtest stopped before execution | Changed CI to run the module with python -m research.baseline_tournament | CLOSED |
| E0006 | 2026-09-23 | 2 | Baseline workflow executed research/baseline_tournament.py as a script, so the repository root was not on sys.path and the module import failed | Tournament could not reach the data backtest | Changed CI to execute python -m research.baseline_tournament; rerun is triggered by the fix commit | CLOSED |

| E0007 | 2026-09-23 | 3 | Vertical-spread VWAP used pandas NA, making signal boolean comparison ambiguous on missing/zero-volume cases | Phase 3 stopped before spread results were produced | Switched to numeric NaN and rerun the workflow | CLOSED |

| E0008 | 2026-09-23 | 3 | Push-triggered Phase 3 workflow was repeatedly relaunched by research-log commits, canceling earlier benchmark runs | Wasted CI runs and made run provenance noisy | Changed Phase 3 to manual-only execution with workflow_dispatch; documentation commits no longer trigger the benchmark | CLOSED |

| E0015 | 2026-09-23 | 3C | Compact full-chain extractor still raised a global overlap error because its per-strike CE/PE aggregation was brittle | Full-chain artifact was not produced | Replaced the CE/PE timestamp join with direct grouped CE/PE aggregation by date and strike | OPEN |
| E0016 | 2026-09-23 | 3D | RSI implementation returned all-NaN on monotonic data because zero downside was replaced with NaN | Phase 3D CI stopped at unit tests | Return RSI=100 for pure upside, 50 for flat, and standard formula otherwise | CLOSED |

Every subsequent error gets a new row. Fixes are never silently discarded.
