[object Object]

## 2026-09-24 — Phase 18 iron-condor preflight correction

Phase 18 is an independent defined-risk short-volatility family using exact-expiry NIFTY options. Before execution, a structure-attribution defect was found and corrected: short-offset and wing-width are now explicit in setup construction, filtering, simulation and final variant mapping. No Phase 18 P&L from superseded code is accepted.


## 2026-09-24 — Phase 18 v2 PR execution trigger

PR #28 is the authoritative execution route. The branch-push workflow was not scheduled reliably, so the repository now uses the main-branch PR workflow `phase-18-v2-pr-execution.yml`; this log update intentionally synchronizes the PR without altering the frozen 192-cell strategy definition.
