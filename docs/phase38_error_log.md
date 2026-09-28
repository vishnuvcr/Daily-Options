# Phase 38 Error Log

No Phase 38 implementation errors have been observed at preregistration. Any defect discovered before numerical acceptance must be logged here and in `docs/error_log.md`, with the affected run quarantined and no P&L accepted from the defective run.

| E0381 | 2026-09-28 | Phase 38 pre-run static audit | Feature eligibility did not require a valid 09:30 NIFTY close/ATM reference, so a missing spot print could have reached integer ATM conversion | No P&L accepted; defect corrected before numerical execution | Require non-null 09:30 spot and derived ATM before a session is feature-eligible; keep zero prior-information barrier unchanged | CLOSED — pre-run implementation defect |

| E0382 | 2026-09-28 | CI execution probe | The initial connected run wrapper hid push-triggered runs, creating the appearance that Phase 38 had not executed | No P&L accepted; no research conclusion drawn | Inspect the repository Actions run collection directly; retain frozen parameters | CLOSED — interface observability defect |

| E0383 | 2026-09-28 | Phase 38 authoritative run 36382979851 | Unit-test fixture used constant early-session ranges, forcing rolling prior standard deviation to zero; tests incorrectly expected eligible rows and a different current observation despite the zero-variance fixture | No market data, P&L or strategy evidence reached; run quarantined | Make the fixture deterministically variable while preserving the frozen interval; clean rerun 36408210374 passed | CLOSED — test-fixture correction |
| E0384 | 2026-09-28 | Phase 38 pre-numerical gate audit | Data gate checked completeness among eligible sessions but did not explicitly enforce the preregistered >=95% feature-eligibility rate after the 60-session warm-up | No P&L accepted; corrected before numerical evidence | Add explicit post-warm-up eligibility-rate gate and persist the metric | CLOSED — pre-numerical implementation defect |

| E0385 | 2026-09-28 | Phase 38 authoritative run 36408107390 | The added expiry-mapping gate accidentally mapped the boolean feature_eligible column instead of the eligible session dates, causing a TypeError in the new unit test | No data acquisition or P&L reached; run quarantined | Evaluate expiry coverage only over eligible session dates; clean rerun 36408210374 passed | CLOSED — gate implementation correction |
