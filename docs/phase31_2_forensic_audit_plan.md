# Phase 31.2 — Phase 31.1 forensic reconciliation audit

## Status
COMPLETE — Phase 31.1 remains quarantined pending provenance-corrected reproduction.

## Research question
Is the published Phase 31.1 result (09:30 NIFTY 2:2:1 ratio, 15:10 exit) reproducible from the pinned raw dataset, leg by leg, independently of the Phase 31.1 simulator, and are the observed losses consistent with the strategy's actual intraday payoff mechanics?

## Why this phase exists
Phase 31.1 was reported as retired after Base/Stress testing. A post-result source/code review found an implementation/report inconsistency: the current Phase 31.1 source aggregates a nonexistent costs column, while the persisted weekly report contains such a column. The numerical result therefore must be reconciled before it is treated as final evidence.

This phase does not optimize the strategy and does not change any strategy parameter.

## Frozen strategy under audit
- NIFTY index options.
- Entry reference 09:30 IST.
- ATM = nearest ₹50 strike under the Phase 31.1 convention.
- Buy 2 lots ATM+200 CE.
- Buy 2 lots ATM-200 PE.
- Sell 1 lot ATM-400 PE.
- Exit reference 15:10 IST.
- Nearest available expiry on/after the trading date.
- Date-aware NIFTY lot-size schedule already frozen in Phase 31.1.
- Base slippage ₹0.20/order; Stress ₹0.40/order.
- Existing date-aware transaction-cost model is reconciled, not re-optimized.

## Audit stages

### A. Artifact/code consistency
1. Hash/read the Phase 31.1 source and tests.
2. Verify the persisted Base/Stress report schema.
3. Check that the current source can actually reproduce its persisted report schema.
4. Record any mismatch as an engineering defect; do not silently repair it.

### B. Independent trade-ledger reconciliation
Use the pinned thetrademarkk/india-index-options-1m revision 51ca58c, independently loaded by this audit script.
For a deterministic stratified sample of executed days spanning the full study period:
1. Derive the 09:30 NIFTY spot directly from raw index data.
2. Derive ATM and all three strikes.
3. Derive the selected expiry independently from expiry filenames.
4. Re-read each leg's raw 09:30 and 15:10 prices.
5. Recompute raw leg P&L, slippage-adjusted leg P&L, transaction costs and net P&L.
6. Compare every material value against the persisted Phase 31.1 trade ledger within explicit numerical tolerances.
7. Independently recompute weekly aggregation and compare against the persisted weekly report and summary.

### C. Coverage and data-integrity checks
- Exact 09:30 and 15:10 timestamps.
- Index/option timezone normalization.
- No duplicate reference trade dates.
- Correct expiry selection.
- Correct lot size.
- Correct 2:2:1 quantities.
- Correct strike arithmetic.
- No missing leg quote in audited trades.
- No mismatch between raw and execution P&L accounting.
- Missing-day list reconciles with the reference ledger.

### D. Payoff/loss-region diagnostics
For every audited executable day:
- compute entry net debit in points;
- record the central expiry zero-intrinsic band [ATM-200, ATM+200];
- obtain 15:10 NIFTY spot directly from the index series;
- compute the 09:30→15:10 move;
- report how often the exit spot remains inside the central band;
- compare that empirical frequency with daily P&L signs and magnitudes.

This is a diagnostic, not a new trading rule.

### E. Decision gates
VALIDATED: independent sample reconciles, aggregate ledger mathematics reconciles, and no unresolved material implementation defect remains.

QUARANTINED: any material leg/price/expiry/quantity mismatch, or an unresolved code/report mismatch that prevents provenance of the published result.

INVALIDATED: independent raw-data recomputation contradicts the published P&L materially enough to change the research conclusion.

No optimization, WFA, holdout promotion, or parameter search is allowed in this phase.

## Outputs
- reports/phase31_2/forensic_audit.json
- reports/phase31_2/sample_reconciliation.csv
- reports/phase31_2/payoff_diagnostics.csv
- reports/phase31_2/final_result.md
- cached-input manifest/checksum information
- tests and workflow
- error-log and research-status updates

## Stop rule
After the audit gates are resolved, freeze the Phase 31.1 conclusion as validated/quarantined/invalidated. Do not let this phase expand into parameter optimization. If invalidated, open a separately preregistered corrected reproduction phase rather than silently editing Phase 31.1.

## Final disposition
The audit gates are complete. The persisted Phase 31.1 accounting is reproducible, but the currently checked-in simulator has different slippage semantics. The phase is therefore quarantined rather than validated. The measured persisted slippage is ₹130,750.00 and the friction-corrected Base total is -₹667,847.06. The stop rule is active: the next phase must freeze one accounting definition before any optimization.
