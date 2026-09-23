# Error Log

| ID | Date | Phase | Error / failed assumption | Impact | Correction | Status |
|---|---|---|---|---|---|---|
| E0001 | 2026-09-23 | 0 | README read returned 404 because repository has no contents | Initial audit looked like a missing repo | Confirmed repo exists but is empty; bootstrap state accepted | CLOSED |
| E0002 | 2026-09-23 | 0 | Paytm Money search surfaced older Rs 10/Rs 15/Rs 20 pages with different user cohorts | Could underestimate current brokerage | Keep conservative Rs 20/order research default and version broker tariff separately | CLOSED |
| E0003 | 2026-09-23 | 0 | NSE permitted-lot-size CSV could not be retrieved through the web content reader | Exact table not embedded yet | Use NSE contract-information page as authoritative source and create CI downloader/cacher | OPEN |
| E0004 | 2026-09-23 | 0 | Paytm Money current pricing page renders some trading-charge values dynamically | Static text does not expose all charges | Pin statutory/exchange components from authoritative sources and keep broker items configurable | OPEN |
| E0005 | 2026-09-23 | 1 | Phase-1 workflow parsed YAML but initially did not install PyYAML | Manual workflow would fail before tests | Added pyyaml to workflow dependency installation | CLOSED |
| E0006 | 2026-09-23 | 2 | Baseline CI ran the tournament as a file and could not import the research package | Backtest stopped before execution | Changed CI to run the module with python -m research.baseline_tournament | CLOSED |
| E0007 | 2026-09-23 | 3 | Vertical-spread VWAP used pandas NA, making signal boolean comparison ambiguous | Phase 3 stopped before spread results | Switched to numeric NaN and reran | CLOSED |
| E0008 | 2026-09-23 | 3 | Push-triggered Phase 3 workflow was repeatedly relaunched by research-log commits | Wasted CI runs and noisy provenance | Changed Phase 3 to manual-only execution | CLOSED |
| E0014 | 2026-09-24 | 3F | Source viewer reports negative minimum volume and unusually large positive maximum | Volume features could be contaminated | Quarantine anomalous volume; require reconciliation before relying on it | OPEN |
| E0015 | 2026-09-24 | 3F | First automatic data-audit run failed before download because the shell heredoc delimiter was indented in YAML | No data audit executed | Replaced heredoc with a single-line Python invocation | CLOSED |
| E0016 | 2026-09-24 | CI | Legacy Phase 1 workflow still triggers on every branch push | Unrelated CI noise | Keep phase-specific workflows path-filtered and isolate legacy triggers during cleanup | OPEN |
| E0017 | 2026-09-24 | 3F | Tournament workflow executed a repository script directly, so research package imports failed | Strategy screen did not execute | Run as python -m research.phase3f_microstructure_tournament | CLOSED |
| E0018 | 2026-09-24 | 3F | Repeated pandas filtering inside nested loops was too slow | Wasted CI compute | Replaced with vectorized joins and one-trade-per-day construction | CLOSED |
| E0023 | 2026-09-24 | 3F-skew CI | Simultaneous push and pull-request triggers canceled the useful run | Corrected commit did not reach data acquisition | Removed overlapping PR trigger | CLOSED |
| E0024 | 2026-09-24 | 3F-skew | Python re-filtered UTC timestamps after SQL had converted to IST | Candidate signals were eliminated | Apply the same IST conversion in Python | CLOSED |
| E0026 | 2026-09-24 | 4 | First Phase 4 walk-forward run failed while summarizing an empty selected-window DataFrame | Numerical file existed but run failed | Guard empty-result summary logic | CLOSED |
| E0027 | 2026-09-24 | 4 | Initial Phase 4 engine recomputed every parameter inside every window | Excessive runtime | Precompute core outcomes and aggregate by window | CLOSED |
| E0028 | 2026-09-24 | 4 | Prior-session close was computed but not merged into the daily feature table | Gap filter caused KeyError | Build prev_close directly from daily last spot | CLOSED |
| E0029 | 2026-09-24 | 4 | Raw timestamps were kept in UTC while entry logic used IST clocks | Observation table became empty | Shift timestamps by +5:30 before feature construction | CLOSED |
| E0030 | 2026-09-24 | 4 | DataFrame attribute access was used for fields such as gap during filter expansion | Walk-forward stopped before scoring | Use explicit bracketed column indexing | CLOSED |
| E0031 | 2026-09-24 | 4 | Explicit ATM labels were assumed to exist simultaneously for call and put | Candidate set became empty | Select executable strike nearest spot from the common call/put strike set | CLOSED |
| E0032 | 2026-09-24 | 4 | Call and put quote timestamps could differ inside the entry window | Valid entries were rejected | Allow independent timestamps and anchor to the later quote | CLOSED |
| E0033 | 2026-09-24 | 4 | Entry clock used midnight instead of the 09:15 IST market open | WFA returned zero observations | Correct entry timestamp to 09:15 IST plus the configured offset | CLOSED |
| E0034 | 2026-09-24 | 4 | WFA engine rebuilt daily series and group-bys repeatedly inside each window | Run appeared stalled | Pre-aggregate daily P&L once and compute full diagnostics only for selected test candidates | CLOSED |
| E0035 | 2026-09-24 | Research environment | Direct local git clone failed because DNS/network resolution to github.com was unavailable in the execution container | Local clone could not be used for inspection | Continue using the GitHub connector as the authoritative repository interface; no research result depends on the failed clone | CLOSED |

| E0013 | 2026-09-24 | 3F | Phase 3E showed the one-year sample lacked usable spot-index volume and was too limited for IV/OI microstructure research | Repeating price-only feature tuning would add little information | Open a new phase using an IV/OI-capable multi-year dataset and require schema/liquidity validation | CLOSED |
| E0022 | 2026-09-24 | 3F-skew | Four-leg cost-model unit test used an incorrect manual gross-P&L sign formula | CI unit test failed before data acquisition | Corrected the test to match the explicit signed cash-flow implementation | CLOSED |

| E0036 | 2026-09-24 | 4 | Manual Phase 4 result-table transcription contained one floating-point typo | Repository table temporarily diverged from the CI artifact | Corrected the value against the downloaded artifact | CLOSED |\n\n| E0037 | 2026-09-24 | 3G | First Phase 3G execution failed because entry-row construction dropped trade_id before path simulation | No Phase 3G statistics were produced | Preserve trade_id through entry selection and path simulation | CLOSED |
| E0038 | 2026-09-24 | 3G | Initial OI confirmation implementation used a backward-looking OI change at the break timestamp | Specification did not satisfy the declared post-break confirmation barrier; no result from that run is eligible for promotion | Use forward OI change over the confirmation window and delay entry until the window has elapsed | CLOSED |

| E0039 | 2026-09-24 | 3G | First fast2 result produced an empty WFA table because reusable WFA compared Python date objects with timestamp-valued trade_date rows | Preliminary leaderboard was valid but OOS window statistics were unavailable | Normalize trade_date to Python dates inside walk_forward before window membership tests | FIXED |
| E0040 | 2026-09-24 | 3G-CI | Fast2 branch run 35916489142 failed at checkout because GitHub runner reported a transient server certificate verification error | No research code executed in that run | Re-triggered through a new fast2 workflow; subsequent checkout/data/tests passed | CLOSED |

| E0039 | 2026-09-24 | 3G | Reusable walk-forward evaluator compared Python date objects with timestamp-valued trade dates, returning zero WFA windows | OOS statistics were unavailable from the first artifact | Normalize trade_date to Python dates inside WFA; independently recompute from immutable path artifact | CLOSED |
| E0041 | 2026-09-24 | 3G | Accepted fast2 artifact showed all 128 variants negative after costs | Candidate family did not meet the research target | Retire Phase 3G rather than enlarge the grid | CLOSED |

Every subsequent research or engineering error gets a new row. Fixes are never silently discarded.
