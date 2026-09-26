# Phase 30.11 — Air Defense rolling walk-forward validation

## Preregistration

The Phase 30.10 full-sample matrix produced 31 cells that passed both Base and Stress gates. Those full-sample results are treated as **discovery evidence**, not clean OOS evidence.

Phase 30.11 therefore reruns the **entire 720-cell definition grid** on three rolling training windows and their immediately following OOS windows. No cell is selected from the full-sample result for WFA selection.

### Fold definitions

The study window is partitioned into 52 complete Monday-Sunday weeks beginning 2025-09-01. 2026-08-31 is reserved outside the WFA windows.

- Fold 1: Train weeks 1-20 (2025-09-01 to 2026-01-18); OOS weeks 21-32 (2026-01-19 to 2026-04-12).
- Fold 2: Train weeks 9-28 (2025-10-27 to 2026-03-15); OOS weeks 29-40 (2026-03-16 to 2026-06-07).
- Fold 3: Train weeks 17-36 (2025-12-22 to 2026-05-10); OOS weeks 37-48 (2026-05-11 to 2026-08-02).

Weeks 49-52 (2026-08-03 to 2026-08-30) plus 2026-08-31 are held in reserve for a subsequent final holdout phase and are not used for selection in Phase 30.11.

## Training selection rule

For each fold, a cell is **training-eligible** only if the exact frozen Phase 30.10 gate is passed in both Base and Stress:
- mean weekly net >= ₹5,000;
- median weekly net >= ₹5,000;
- profitable-week rate >=70%;
- >=20 completed weeks;
- execution coverage >=80%.

The same 720 cells are evaluated; no new parameter values are introduced.

## WFA survivor rule

A cell becomes a **WFA survivor** only when:
1. it is training-eligible in at least **2 of the 3 folds**; and
2. when pooling only the OOS weeks from folds in which it was training-eligible, it passes the following descriptive OOS gate separately in Base and Stress:
   - mean weekly net >= ₹5,000;
   - median weekly net >= ₹5,000;
   - profitable-week rate >=70%;
   - execution coverage >=80%.

The OOS pooled sample must contain at least **16 weeks**. The 20-week minimum is not imposed on OOS because the full study window cannot supply 20 OOS weeks per fold while retaining 20 training weeks.

## Statistical outputs

For every fold and stage, preserve the same Phase 30.10 metrics. For each WFA survivor compute:
- pooled OOS mean and median weekly net;
- profitable-week rate;
- profit factor;
- max drawdown;
- 5% weekly quantile and expected shortfall;
- execution coverage;
- average and peak capital proxy;
- total gross P&L, costs and net P&L;
- Base-to-Stress degradation.

## Cost and data controls

The existing date-aware project cost model is retained:
- Paytm Money flat ₹20 brokerage from 2025-01-15 onward;
- NSE option transaction rate ₹3,553 per crore premium each side from 2026-03-01, with ₹3,503 per crore before that;
- STT 0.10% on option sales through 2026-03-31 and 0.15% from 2026-04-01;
- 18% GST on applicable brokerage/exchange/SEBI charges;
- Base slippage ₹0.20/order and Stress ₹0.40/order.

Paytm Money's flat ₹20 pricing is documented by Paytm Money's December 2024 pricing update. citeturn719285view1 NSE's February 27, 2026 transaction-charge circular establishes ₹3,553/crore for equity options from March 1, 2026, and NSE's STT schedule establishes 0.15% option-sale STT from April 1, 2026 versus 0.10% before then. citeturn719285view0turn719285view2

## Closure

- **WFA PASS:** at least one frozen cell satisfies the survivor rule.
- **WFA FAIL:** no cell satisfies the survivor rule.
- **DATA/ENGINE BLOCKED:** any fold/regime cannot complete with audited 720-cell coverage.

A WFA PASS advances only the surviving frozen cells to Phase 30.12 final reserve holdout testing. No parameter tuning is permitted between folds.


## Artifact-audit invariant

Each WFA shard is a single regime artifact containing **3 folds × 2 stages = 6 leaderboards + 6 weekly files**. With 12 definition shards × 2 regimes, the complete run therefore produces **144 leaderboard files and 144 weekly files**, covering **144 × 720 = 103,680 leaderboard rows**. The aggregate workflow must audit these counts before any survivor is accepted.
