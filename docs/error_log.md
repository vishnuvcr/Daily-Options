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

| E0009 | 2026-09-23 | 3 | Fixed 65-lot assumption was invalid across the 2025-2026 sample because NIFTY lot size changed from 75 to 65 at the Dec 2025 transition | Earlier Rs/lot backtests are provisional | Added date-aware NIFTY lot-size resolver and flagged earlier figures for correction | OPEN |
| E0010 | 2026-09-23 | 3 | Focused straddle grid repeatedly rescanned the same option path for hundreds of configurations | Excessive CI runtime and canceled run | Added precomputed outcome matrix so filters reuse simulated exits | CLOSED |
| E0011 | 2026-09-23 | 3C | Full-chain workflow heredoc indentation caused a YAML-validity failure before job creation | Full-chain validation could not start | Replaced the multiline download script with a one-line Python command | CLOSED |
| E0012 | 2026-09-23 | 3C | Polars rejected parquet timestamps containing timezone offset +05:30 | Iron-fly validation stopped before strategy execution | Read parquet with PyArrow, strip timezone metadata to naive microsecond timestamps, then construct Polars frame | CLOSED |

| E0013 | 2026-09-23 | 3C | Full-chain iron-fly code rescanned the entire 34M-row parquet once per trading day | Validation runtime became unnecessarily long | Partitioned the parquet once by trading date and restricted each day to the 09:15-13:15 research window | CLOSED |

| E0014 | 2026-09-23 | 3C | Full-chain extractor treated a single day with no complete CE/PE overlap as a global dataset failure, even though diagnostic confirmed many days have full 75-strike overlap | Prevented compact dataset creation unnecessarily | Changed extraction to skip incomplete days and retain all valid dates; fail only when the entire dataset has no overlap | CLOSED |

Every subsequent error gets a new row. Fixes are never silently discarded.
