# Phase 31.8 — Global Overnight Transmission — Final Status

**State: CLOSED — NEGATIVE DISCOVERY**

Authoritative run: **36341877019**

## Data gate
- Raw NIFTY sessions: 1,228
- Feature-eligible sessions: 1,164
- Complete global-feature sessions: 1,164
- Coverage: 100.0%
- Prior-date violations: 0
- Option execution coverage: 96.92%–98.17% across cells

## Discovery
Frozen grid: 3 features × 2 thresholds × 2 exits = 12 cells.

No cell passed the promotion gate:
- mean weekly net ≥ ₹5,000
- median weekly net ≥ ₹5,000
- positive-week rate ≥70%
- both Base and Stress

The closest positive mean-weekly result in the true grid was the ASIA_LEAD z≥1.0 / 10:30 cell:
- Base mean weekly net: ₹107.37
- Base median weekly net: -₹122.78
- Base positive-week rate: 45.45%
- Stress mean weekly net: ₹37.13
- Stress median weekly net: -₹211.39
- Stress positive-week rate: 45.45%

This is a near-miss only in mean magnitude; it does not satisfy the frozen consistency gate.

## Null controls
The five shuffled full-panel null seeds did not establish a comparable positive weekly-consistency effect. Their strongest isolated means remained far below the ₹5,000 target and generally had negative weekly medians.

## Decision
**Retire Phase 31.8.** No parameter tuning, added indices, alternate thresholds, different horizons, WFA or OOS is authorized from this result.

## Integrity note
The persisted global-data manifest records yfinance version **1.7.0**, while the newly authored workflow installs 0.2.66. The numerical run used the already-persisted cache and therefore did not re-download under the workflow's installed package. The exact cached source files and SHA-256 hashes are preserved in the manifest. This is logged as a reproducibility engineering issue, not as a result-changing data substitution.

## Next direction
Return to the bounded research plan and advance to the next distinct family only after updating the main status/README and preserving this result.
