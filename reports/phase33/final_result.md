# Phase 33 — Dealer Gamma Exposure Proxies
## Final Research Result

**Status:** CLOSED — DATA-LIMITED; no economic P&L accepted  
**Authoritative data-gate run:** 36340721257  
**Branch:** `phase-33-dealer-gamma-exposure-v1`

### Abstract

Phase 33 tested a preregistered NIFTY dealer-gamma proxy based on prior-session option open interest, Black-Scholes gamma and a fixed conventional call-positive/put-negative inventory sign. The frozen family contained three state variables — aggregate GEX, gamma-flip distance and ATM gamma concentration — with two absolute z-score thresholds and two fixed intraday exits, producing 12 true cells plus five complete-panel null seeds under Base/Stress friction.

The implementation and unit-test gates were ultimately corrected for SQL compatibility, vectorized gamma/IV computation, execution-key mapping, audited transaction costs, debit-spread sign handling and the exact prior-session information barrier. The authoritative run **36340721257** then reached the actual data gate and failed it **before any P&L**.

After a 60-session prior-only warm-up:
- Expected prior-session observations: **1,233**
- Reconstructed gamma snapshots: **1,228**
- Snapshot coverage: **99.59%**
- Prior-information barrier violations: **0**
- GEX_Z feature coverage: **100.00%**
- FLIP_DISTANCE_Z feature coverage: **26.54%**
- ATM_GEX_SHARE_Z feature coverage: **100.00%**
- Frozen signal rows generated before the gate: **3,158**
- Minimum execution-coverage cell: **0.00%** in gate-only output because economic execution was intentionally not authorized after the feature gate failure

The preregistered gate required at least 95% feature coverage for each registered feature. FLIP_DISTANCE_Z therefore failed decisively. No Base/Stress P&L, null-control economics, bootstrap promotion, WFA or OOS result is valid for Phase 33.

### Research question

Can prior-session NIFTY public option/OI data be converted into a stable dealer-gamma regime proxy that predicts next-session opening-gap continuation/reversal strongly enough to support a ₹5,000 net-per-week debit-spread strategy after audited Indian option-trading frictions?

### Frozen hypothesis

The experiment treated:
- negative conventional GEX as a regime favoring gap continuation;
- positive conventional GEX as a regime favoring gap fading;
- extreme gamma-state values as the trade trigger.

The call-positive/put-negative sign was explicitly treated as an **inventory assumption**, not a mathematical property of gamma.

### Method

The signal used only the last NIFTY-session option observation at or before the NIFTY index session close. The fixed chain window was ±1,500 NIFTY points around prior close. Option IV was inverted with Black-Scholes using r=0 and q=0; gamma was calculated from the same inputs and weighted by OI and historical NIFTY lot size.

Registered features:
1. GEX_Z — prior-only 60-session z-score of aggregate signed GEX.
2. FLIP_DISTANCE_Z — prior-only 60-session z-score of spot's signed distance from a zero-GEX root on a fixed 50-point grid.
3. ATM_GEX_SHARE_Z — prior-only 60-session z-score of near-ATM absolute gamma concentration.

The discovery matrix was 3 features × 2 thresholds (0.75, 1.25) × 2 exits (10:30, 15:10) = 12 cells.

### Data-gate result

The experiment failed at the feature-quality gate because the zero-GEX root existed often enough to produce a meaningful diagnostic but far too rarely to satisfy the preregistered 95% feature-completeness requirement.

This is a **data-limitation finding, not an economic rejection** of dealer-gamma information as a whole.

The project therefore must not infer that the gamma hypothesis is profitable or unprofitable from Phase 33. The only supported conclusion is that the frozen three-feature formulation was not sufficiently observable in the pinned NIFTY/OI history to authorize economic testing.

### Engineering audit

The phase also surfaced and closed several pre-P&L implementation defects:
- E0439 — unquoted DuckDB `close` alias in the index loader.
- E0440 — row-wise gamma/IV performance plus incomplete null-state permutation; corrected before accepted P&L.
- E0441/E0443 — exact execution SQL alias defects.
- E0442 — workflow artifact push race; persistence hardened with fetch/rebase retries.
- E0444 — missing audited brokerage/statutory charges and incorrect put-debit-spread sign handling.
- E0445 — prior-session option/OI snapshot not explicitly capped at the exact NIFTY index-session information cutoff.
- Run 36340369225 was quarantined because it predates E0444/E0445.

No economic P&L from any pre-correction run is accepted.

### Strengths

- Explicit preregistration and finite 12-cell grid.
- Strict prior-information timing.
- Historical NIFTY lot sizes.
- Audited brokerage/STT/exchange/SEBI/stamp/GST cost model added before any accepted P&L.
- Base/Stress slippage.
- Complete-panel null design frozen before numerical economics.

### Limitations

1. Public OI does not reveal the true dealer/customer inventory sign.
2. The zero-GEX root is inherently sparse under the fixed ±1,500-point chain and fixed grid.
3. IV inversion and gamma depend on model assumptions and option-price quality.
4. The pinned cache ends before the full nominal study window, although session coverage within the available cache exceeded the 95% prior-session gate.
5. No intraday order-book or dealer inventory data are available.

### Conclusion

**Phase 33 is closed as DATA-LIMITED.**

No trading strategy was promoted. No P&L, null economics, WFA or OOS inference is authorized.

The highest-value next family is the already identified **multi-expiry volatility-surface term structure**, which avoids dependence on a sparse zero-GEX root while remaining materially distinct from Phase 32's single-expiry skew/smile shape.

### Future direction

Phase 34 should test a frozen cross-expiry volatility-term-structure hypothesis using the same pinned option cache, strict prior-session timing, Base/Stress audited costs, null controls and the existing ₹5,000/week economic gate. The new phase should not reuse or tune Phase 33's gamma thresholds.

## Reproducibility

Primary files:
- `docs/phase33_plan.md`
- `docs/phase33_literature_review.md`
- `research/phase33_dealer_gamma_exposure.py`
- `tests/test_phase33_dealer_gamma_exposure.py`
- `.github/workflows/phase-33-dealer-gamma-exposure.yml`
- `reports/phase33/gate/data_gate.json`
- `reports/phase33/gate/gamma_feature_panel.csv`
- `reports/phase33/gate/signals.csv`

