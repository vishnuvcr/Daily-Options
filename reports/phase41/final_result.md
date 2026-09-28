# Phase 41 — NIFTY Option-Gamma Concentration × Opening-Gap Direction

## Final status
**CLOSED — DATA-LIMITED.**

Authoritative workflow run: **36467584676**  
Branch: `phase-41-gamma-concentration-opening-gap-v1`

No Base, Stress, null-control, WFA or OOS P&L is accepted.

## Data-gate result

| Metric | Result | Frozen requirement | Outcome |
|---|---:|---:|---|
| Post-warm-up sessions | 1,154 | — | observed |
| Feature-eligible sessions | 354 | — | observed |
| Feature eligibility | 30.68% | >=95% | FAIL |
| Prior-chain coverage | 79.50% | >=95% | FAIL |
| Core-chain coverage | 87.41% | >=95% | FAIL |
| Prior-information violations | 0 | 0 | PASS |
| Signal rows | 628 | — | observed |
| Minimum execution coverage | 96.67% | >=95% | PASS (diagnostic only) |

The gate failed before discovery because the gamma-chain observability was insufficient. Base and Stress discovery were correctly skipped.

## Integrity interpretation

The run passed unit tests, restored/acquired the pinned NIFTY/options source, constructed the feature panel without prior-information violations, and persisted the diagnostic artifacts. The failure is therefore classified as **data observability**, not as evidence that the trading hypothesis is profitable or unprofitable.

The preregistered rules are not changed after seeing the gate result. In particular, the 60-observation lookback, ±0.75 z thresholds, ±₹100/±₹500 chain windows, exact-expiry construction, gap mappings, entry/exit times, spread width, lot sizing, cost model and Base/Stress slippage remain frozen.

## Scientific conclusion

Phase 41 does not provide an economic result. The available pinned source does not support the required >=95% complete prior-session gamma surface over the study window under the frozen construction. Any attempt to lower the coverage threshold, change the strike windows, impute missing gamma observations, or alter the signal definition would constitute post-result redesign and is not permitted.

## Evidence retained

- `reports/phase41/gate/data_gate.json`
- `reports/phase41/gate/feature_diagnostics.csv`
- `reports/phase41/gate/feature_panel.csv`
- `reports/phase41/gate/price_coverage.csv`
- `reports/phase41/source_manifest.json`

## Next step

Advance to a materially distinct, preregistered Phase 42 family. Phase 42 must be screened for data observability before any economic interpretation, and must preserve the same realistic Paytm Money/NSE/statutory cost treatment, Base/Stress slippage, null controls and weekly promotion gate.
