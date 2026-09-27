# Phase 34 Status

**Branch:** `phase-34-multi-expiry-vol-term-structure-v1`

**State:** PREREGISTERED — implementation/unit-test gate.

**Frozen family:** two-expiry NIFTY IV term structure.

**Frozen grid:** 2 features × 2 thresholds × 2 exits = 8 true cells.

**Nulls:** 5 complete-panel seeds per cell and friction.

**Execution:** long-back/short-front double calendar only; positive-debit admissibility; 8 execution orders per completed trade.

**Costs:** historical NIFTY lots, existing date-aware Paytm Money/NSE/statutory charge model, Base/Stress slippage ₹0.20/₹0.40.

**Current checkpoint:** engine and unit-test implementation. No P&L accepted.


## Run 1 closure
Run **36341124742** stopped during Python test collection on E0448. No data acquisition or P&L ran. The SQL string is corrected; run 2 is the next authoritative attempt.
