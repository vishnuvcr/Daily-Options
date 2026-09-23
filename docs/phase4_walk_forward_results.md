# Phase 4 Nested Walk-Forward Results

## Provenance
GitHub Actions run 35912159508 on phase-4-walk-forward-selection-v2.

## Computation
- Observations: 7,331
- Core trade rows: 131,958
- Expanded trade rows: 852,750
- Core variants: 54
- Regime-filter variants: 8
- Total parameter variants: 432
- Walk-forward windows: 14
- Selected test windows: 22

## Result
- Positive test windows: 8/22
- Target-qualified test windows: 0/22
- Mean selected test-window net: Rs -64.23/lot
- Median selected test-window net: Rs -43.69/lot
- Mean selected-test positive-day rate: 47.65%
- All selected-test bootstrap lower 95% bounds positive: No
- Gate: FAIL_PRELIMINARY

## Decision
The candidate ATM intraday short-straddle family is not promoted. Do not run another unconstrained straddle parameter sweep.

The finding is consistent with a 2026 NIFTY short-volatility study reporting negative net returns for several systematic short-volatility implementations after implementation and tail risk, despite positive VRP evidence.

Source:
https://papers.ssrn.com/sol3/Delivery.cfm/6876580.pdf?abstractid=6876580&mirid=1&type=2

Next bounded hypothesis:
Dynamic price-structure break + post-break OI confirmation + defined-risk debit spread.
