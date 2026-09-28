# Phase 40 Status

## Final state
**CLOSED — NEGATIVE DISCOVERY. No WFA/OOS or promotion.**

Authoritative clean workflow: **36466313849**  
Branch: `phase-40-overnight-gap-implied-move-v1`

## Frozen experiment
- Prior-session NIFTY 15:10 close and ATM CE/PE IV.
- Overnight gap at next 09:15 open.
- One-session implied move scaled by sqrt(1/252).
- GAP_RATIO = absolute overnight gap / implied one-session move.
- Strictly prior 60 valid GAP_RATIO observations; no imputation/forward-fill.
- Prior RV20 excludes the current signal day.
- HIGH_GAP_DISLOCATION / LOW_GAP_DISLOCATION at ±0.75.
- CONTINUE / FADE mappings.
- 09:31 entry, 10:30/15:10 exits, one-lot 200-point debit spread.
- Historical lot sizes, frozen cost model, Base/Stress slippage ₹0.20/₹0.40.
- Five fixed permutation null seeds.

## Data and integrity
- Raw sessions: 1,234.
- Post-warm-up sessions: 1,174.
- Feature-eligible: 1,148 / 1,174 = **97.79%**.
- Prior-day IV coverage: **98.38%**.
- Overnight-gap coverage: **98.64%**.
- Expiry mapping: **100%**.
- Prior-information violations: **0**.
- Minimum execution coverage: **98.45%**.
- Accounting reconciliation: **passed in all 8 Base and 8 Stress cells**.

## Economic result
**0/8 Base** and **0/8 Stress** cells passed the frozen discovery gate.

Best true cell in both frictions:
**LOW_GAP_DISLOCATION × FADE × 15:10**
- Base: 233 trades; 151 weeks; total net **−₹6,560.66**; mean weekly **−₹43.45**; median weekly **−₹266.89**; positive-week rate **43.71%**; PF **0.964**; max drawdown **−₹32,888.78**.
- Stress: 233 trades; 151 weeks; total net **−₹15,956.66**; mean weekly **−₹105.67**; median weekly **−₹313.28**; positive-week rate **41.06%**; PF **0.915**; max drawdown **−₹39,724.78**.

No other true cell had a positive mean-weekly result. All 16 true cells failed at least one economic criterion by a wide margin.

## Null controls
Five fixed permutation null seeds were evaluated for all cells under Base and Stress.
- One Base cell (LOW_GAP_DISLOCATION × CONTINUE × 10:30) and the corresponding Stress cell exceeded all five null means, but both true means remained negative (−₹141.37 Base; −₹203.66 Stress) and therefore did not support promotion.
- The best true cell did not beat all five nulls in either friction regime.

Null controls are diagnostic only and were not used for tuning.

## Statistical disposition
No WFA/OOS was authorized because 0/8 cells cleared the discovery gate in either friction regime. No threshold, lookback, RV window, expiry, timing, spread-width or cost tuning is authorized.

## Final conclusion
**Phase 40 is RETIRED — NEGATIVE DISCOVERY.** The prior-day implied-volatility / overnight-gap dislocation family did not provide the required ₹5,000/week edge after realistic costs and doubled slippage.

## Reproducibility
- `docs/phase40_plan.md`
- `docs/phase40_status.md`
- `docs/phase40_error_log.md`
- `research/phase40_overnight_gap_implied_move.py`
- `research/phase40_source_diagnostic.py`
- `tests/test_phase40_overnight_gap_implied_move.py`
- `.github/workflows/phase-40-overnight-gap-implied-move.yml`
- `reports/phase40/`
