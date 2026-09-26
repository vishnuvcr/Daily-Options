# Phase 31.2 forensic audit result

Decision: **QUARANTINED**

Audited sample: 30 executed days; exact raw-data reconciliation matches: 30; mismatches: 0.

Reference Base total net: ₹-537,097.06; reference Base mean weekly net: ₹-2,065.76.
Reference Stress total net: ₹-537,032.22; reference Stress mean weekly net: ₹-2,065.51.

Persisted Base slippage identified in leg records: ₹130,750.00; slippage-adjusted total net: ₹-667,847.06; slippage-adjusted mean weekly net: ₹-2,568.64; slippage-adjusted positive-week rate: 25.38%.

The persisted artifact reconciles to raw gross P&L minus transaction/statutory costs. The current checked-in simulator instead applies slippage inside execution gross. This semantic/provenance difference is why the Phase 31.1 result remains quarantined.
The audit is diagnostic and does not tune parameters. The central expiry loss band is not treated as equivalent to the 15:10 mark-to-market outcome.

See forensic_audit.json, sample_reconciliation.csv, and payoff_diagnostics.csv.
