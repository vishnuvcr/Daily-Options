[object Object]

## 2026-09-24 — Phase 18 iron-condor preflight correction

Phase 18 is an independent defined-risk short-volatility family using exact-expiry NIFTY options. Before execution, a structure-attribution defect was found and corrected: short-offset and wing-width are now explicit in setup construction, filtering, simulation and final variant mapping. No Phase 18 P&L from superseded code is accepted.


## 2026-09-24 — Phase 18 v2 PR execution trigger

PR #28 is the authoritative execution route. The branch-push workflow was not scheduled reliably, so the repository now uses the main-branch PR workflow `phase-18-v2-pr-execution.yml`; this log update intentionally synchronizes the PR without altering the frozen 192-cell strategy definition.


## 2026-09-24 — Phase 18 retired; Phase 19 launched

Phase 18 corrected execution run `36040028422` completed Base and Stress successfully but found `setup_rows=0` and `filtered_setup_rows=0` with 3,753 frozen signals and 2,205,051 option quote rows. The four-leg iron-condor hypothesis is retired as source/execution-infeasible. Phase 19 launches a two-leg short-strangle regime with unchanged late-day/low-jump/low-RV framework and a 144-cell frozen grid.


## 2026-09-24 — Phase 19 timestamp-alignment correction

Phase 19 Base/Stress returned zero setups, but a targeted 20-signal diagnostic showed the option quote window was empty after the internal timestamp normalization. This contradicts the independent Phase 17c feasibility smoke, which found common PE/CE execution minutes. E0192 replaces the join-based quote loader with the validated direct local-time window query; no signal, offset, regime, exit or cost parameter changes.


## 2026-09-24 — Phase 19 dataset date-key correction

E0195 identified the remaining zero-setup cause: Phase 19 used the option file's `trading_day` as the join key. The pinned dataset convention requires `trade_date` to be derived from the timestamp after UTC→IST normalization. The loader has been corrected without changing entry times, offsets, regime filters, exits, slippage or costs.
