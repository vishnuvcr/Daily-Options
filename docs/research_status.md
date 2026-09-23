# Research Status

Last updated: 2026-09-24

## Overall
Phase 4 — WALK-FORWARD VALIDATION COMPLETE; CANDIDATE FAILED PRELIMINARY PROMOTION

## Step log

### 2026-09-24 — Step 4.4 Phase 4 nested walk-forward result
- GitHub Actions run: 35912159508; commit: 05c2ce40d4bafbb07baa64298c46eb64439e5058.
- Unit tests passed and the complete multi-year data cache was acquired/reused successfully.
- Observations: 7,331; core trade rows: 131,958; expanded trade rows: 852,750.
- Core variants: 54; regime-filter variants: 8; total parameter variants: 432.
- Walk-forward windows: 14; selected test windows: 22; positive test windows: 8; target-qualified test windows: 0.
- Mean selected test-window net: Rs -64.23/lot; median: Rs -43.69/lot.
- Mean test positive-day rate: 47.65%.
- No selected-test bootstrap 95% lower bound was positive across the run.
- Gate: FAIL_PRELIMINARY.
- Decision: the intraday ATM short-straddle family is not promoted and is retired as a lead candidate. This is consistent with recent NIFTY short-volatility research showing that positive VRP does not necessarily translate into positive net returns once tail risk and implementation are included.
- Next research: a bounded Phase 3G hypothesis using dynamic intraday price-structure breaks as the primary event and option OI repositioning only as post-break confirmation, expressed through a defined-risk debit spread.

## Current blockers
- Historical bid/ask/depth data may require licensed or broker-authenticated sources.
- Some public datasets have close/market-price bars without executable quotes.
