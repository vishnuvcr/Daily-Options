# Phase 34 — Multi-Expiry Volatility Term Structure
## Final Research Manuscript

**Status:** CLOSED — DATA-LIMITED; no economic P&L accepted  
**Authoritative gate run:** 36341535504  
**Branch:** `phase-34-multi-expiry-vol-term-structure-v1`

## Abstract

Phase 34 tested whether a prior-session NIFTY implied-volatility term-structure inversion between the nearest and second-nearest expiries could support a defined-risk long-back/short-front double-calendar that generated at least ₹5,000 net per completed trading week after realistic Indian trading costs.

The preregistered discovery family contained two features (ATM and wing front-minus-back IV spreads), two positive z-score thresholds (0.75 and 1.25) and two exits (10:30 and 15:10 IST), yielding eight true cells plus five complete-panel null seeds. The information cutoff was the exact last NIFTY index observation of the prior session, with option observations selected at or before that timestamp. Base/Stress slippage and the audited Paytm Money/NSE/statutory charge model were frozen before numerical execution.

The authoritative run completed unit tests, restored the pinned one-minute NIFTY/options cache and reconstructed the two-expiry term structure, but the preregistered data gate failed. Only **656 of 1,233 expected prior sessions (53.20%)** produced a complete two-expiry surface after all required ATM/±100 option IV inputs were available. Conditional on surviving sessions, both standardized features were 100% complete after warm-up, but unconditional source/session coverage remained far below the required 95%. Execution/debit admissibility was therefore not eligible to authorize economic discovery.

No Base or Stress P&L, null-control economics, WFA or OOS result is valid for Phase 34.

## 1. Research question

Can extreme prior-session NIFTY front-versus-back implied-volatility structure predict next-session mean reversion that is monetizable with a fixed debit double-calendar after Indian option-trading costs?

## 2. Aims and objectives

### Aim
Test maturity-dimension information that was not captured by Phase 32's single-expiry skew/smile features or Phase 33's gamma-positioning family.

### Objectives
1. Reconstruct front/back NIFTY IV term spreads from historical option prices.
2. Prevent forward leakage through a strict prior-session timestamp barrier.
3. Test a finite eight-cell strategy grid and five full-panel null seeds.
4. Account for historical NIFTY lot sizes, brokerage/statutory costs and Base/Stress slippage.
5. Close the family without post-result tuning when the data gate fails.

## 3. Literature review

Research on volatility predictability, variance-risk pricing and forward variance shows that option-implied information can vary materially across maturities. Term spreads in implied volatility and variance-risk measures have been studied as predictors of broader volatility-risk dynamics. Calendar spreads directly monetize relative maturity pricing, but their economics are sensitive to volatility level, maturity, execution and transaction costs.

The literature also shows that volatility-surface measurement is model-sensitive. Phase 34 therefore used a deliberately simple, fixed-strike, directly observed Black-Scholes IV construction instead of selecting among SVI/SABR/spline models after observing results.

A 2026 NIFTY-specific preliminary paper on double-calendar spreads was treated as contextual evidence rather than as a validated trading rule.

Full references and URLs are preserved in `docs/phase34_literature_review.md`.

## 4. Data and methodology

### Numerical source

- Dataset: `thetrademarkk/india-index-options-1m`
- Revision: `51ca58c`
- Persistent cache: `data/cache/phase31_trademarkk`

### Signal timing

For each prior NIFTY session, the signal used the exact last available NIFTY index observation. For each of the two selected expiries, the option loader took the latest option observation at or before that timestamp.

### Expiries

- Front: nearest NIFTY expiry strictly after signal date.
- Back: second-nearest NIFTY expiry strictly after signal date.

### Features

`ATM_TERM_SPREAD = mean(front ATM CE/PE IV) - mean(back ATM CE/PE IV)`

`WING_TERM_SPREAD = mean(front ATM±100 wing IV) - mean(back ATM±100 wing IV)`

Each raw feature was standardized using only the previous 60 completed signal-session observations.

### Frozen strategy

Only positive z-score extremes were traded:

- SELL front ATM CE
- SELL front ATM PE
- BUY back ATM CE
- BUY back ATM PE

One NIFTY lot; positive initial calendar debit required. Credit calendars and reverse calendars were explicitly excluded.

### Frozen grid

- ATM_TERM_Z / WING_TERM_Z
- z thresholds 0.75 / 1.25
- exits 10:30 / 15:10
- **8 true cells**
- five null seeds
- Base/Stress slippage ₹0.20/₹0.40 per option-price unit per order

## 5. Data-gate result

| Gate item | Result | Requirement |
|---|---:|---:|
| Expected prior sessions | 1,233 | — |
| Complete two-expiry surface sessions | **656 (53.20%)** | ≥95% |
| Warm-up sessions among panel | 596 | — |
| ATM_TERM_Z coverage conditional on panel | 100% | ≥95% |
| WING_TERM_Z coverage conditional on panel | 100% | ≥95% |
| True cells defined | 8 | 8 |
| Prior-information leakage | 0 observed by construction | 0 |
| Economic promotion | Not authorized | — |

The term-structure panel begins on 2021-07-01 and extends to 2026-07-02 in the available cache. The principal limitation is not z-score computation; it is the inability to reconstruct complete front/back ATM/wing surfaces for a sufficiently large fraction of expected sessions.

## 6. Why the phase stops here

The preregistered gate requires ≥95% observability of the two-expiry feature family before any P&L calculation is accepted. With only 53.20% complete surface sessions, running the economic grid would turn a data-quality problem into an implicit sample-selection rule.

No relaxed denominator, alternate expiry pairing, narrower strike set, or post-result missingness rule is being introduced.

The observed gate-stage execution/debit artifacts are not interpreted as economics because the data gate itself was not passed.

## 7. Strengths

1. Preregistered maturity definitions and debit-calendar direction.
2. Strict prior-session information barrier.
3. Finite eight-cell search and five null seeds.
4. Historical lot-size and cost accounting.
5. No result-driven relaxation after observing coverage.

## 8. Limitations

1. The pinned one-minute options history does not support the complete two-expiry surface on ≥95% of expected sessions.
2. The test uses only nearest and second-nearest expiries.
3. Black-Scholes IV inherits model and price-quality assumptions.
4. Historical order-book depth and bid/ask queue information are unavailable.
5. No economic inference can be drawn because the family failed its source-coverage gate.

## 9. Discussion

The Phase 34 question was economically plausible and materially different from prior phases, but the pinned historical source did not provide sufficient continuous coverage for a strict two-expiry term-structure experiment over the intended window.

This is important research evidence: a conceptually attractive option strategy cannot be promoted merely because a partial subset of dates is backtestable. A selective sample could materially change results by preferentially retaining days with liquid simultaneous front/back quotes.

The result therefore supports a **data-limitation conclusion**, not a claim that NIFTY term structure lacks predictive content.

## 10. Conclusion

**Phase 34 is closed as DATA-LIMITED.**

No strategy was promoted. No P&L result was accepted. No WFA/OOS was authorized. No post-result expiry, strike, threshold or calendar-direction tuning is permitted.

## 11. Future direction

The next materially distinct family is **Phase 35 — Global Overnight Shock × Options Structure**, which will combine an independently defined global overnight transmission variable with a frozen NIFTY options structure. The goal is to test whether cross-market information changes the monetizability of a defined-risk NIFTY option trade rather than testing the global return signal alone, which the earlier Phase 31.8 family already failed to promote.

## Appendix A — Reproducibility

Primary files:
- `docs/phase34_plan.md`
- `docs/phase34_literature_review.md`
- `docs/phase34_error_log.md`
- `docs/phase34_status.md`
- `research/phase34_multi_expiry_vol_term_structure.py`
- `tests/test_phase34_multi_expiry_vol_term_structure.py`
- `.github/workflows/phase-34-multi-expiry-vol-term-structure.yml`
- `reports/phase34/gate/term_structure_panel.csv`
- `reports/phase34/gate/signals.csv`

