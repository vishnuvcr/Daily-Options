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

Every subsequent error gets a new row. Fixes are never silently discarded.

| E0013 | 2026-09-24 | 3F | Phase 3E showed the current one-year sample lacks usable spot-index volume and is too limited for IV/OI microstructure research | Repeating price-only feature tuning would add little information | Open a new phase using an IV/OI-capable multi-year dataset and require schema/liquidity validation before strategy testing | CLOSED |


| E0014 | 2026-09-24 | 3F | Public source viewer reports a negative minimum for the `volume` field and an unusually large positive maximum; the anomaly has not yet been independently reconciled | Volume-based microstructure features could be contaminated or misleading if used directly | Quarantine volume; scan all parquet partitions, quantify affected rows, and cross-check against an independent source before enabling volume features | OPEN |


| E0015 | 2026-09-24 | 3F | First automatic data-audit run failed before download because the shell heredoc delimiter was indented inside the YAML block | Dataset acquisition never started; no data conclusions were made | Replaced the heredoc with a single-line Python invocation and kept the workflow unit-tested before acquisition | CLOSED |

| E0016 | 2026-09-24 | CI | Legacy Phase 1 workflow still triggers on every branch push and is failing on this research branch, producing unrelated CI noise | Does not block Phase 3F directly but obscures phase-specific run status | Keep Phase 3F path-filtered; inspect and isolate legacy workflow triggers during CI cleanup before final merge | OPEN |


| E0017 | 2026-09-24 | 3F | Tournament workflow executed a repository script directly, so `research` package imports failed with `ModuleNotFoundError` after the data audit had already passed | Strategy screen did not execute; no numerical strategy result was produced | Run the tournament as `python -m research.phase3f_microstructure_tournament`, matching the corrected Phase 2 import pattern | CLOSED |


| E0018 | 2026-09-24 | 3F | First tournament implementation used repeated pandas filtering inside nested parameter loops and was computationally inefficient; the run was cancelled before producing a result | Excessive runtime and wasted CI time | Replaced with vectorized joins and one-trade-per-day construction; rerun completed successfully | CLOSED |


| E0022 | 2026-09-24 | 3F-skew | New four-leg cost-model unit test used an incorrect manual gross-P&L sign formula; the implementation returned the correct signed cash-flow result | CI unit test failed and blocked data acquisition; no strategy result was produced | Corrected the test's gross-P&L calculation to match the explicit long/short leg signs | CLOSED |


| E0023 | 2026-09-24 | 3F-skew CI | Simultaneous push and pull-request triggers shared the same concurrency group, causing the successful code push run to be canceled by the PR-triggered run | Corrected unit-test commit never reached data acquisition | Removed the overlapping pull_request trigger; workflow retains manual workflow_dispatch and path-filtered push execution | CLOSED |


| E0024 | 2026-09-24 | 3F-skew | IV-skew feature SQL correctly filtered IST times using +5:30, but Python re-filtered the resulting rows using raw UTC timestamps, eliminating every candidate signal | Two completed CI runs reported zero signals; no P&L result was generated, so no strategy conclusion was accepted | Apply the same +5:30 conversion in the Python signal builder before matching 09:45/10:00/10:15 IST | CLOSED |
