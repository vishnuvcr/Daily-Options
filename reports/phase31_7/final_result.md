# Phase 31.7 — OI/Volume Microstructure Discovery: Final Result

## Decision

**CLOSED — no promotion to WFA/OOS.**

Authoritative numerical run: **GitHub Actions run 36251189770**. The run passed unit tests, the data gate, raw execution-row probe, Base discovery, Stress discovery, and the frozen 12-cell / null-control validation. The uploaded artifact is retained as **artifact 10909111158**.

A separate post-run accounting audit confirmed the correct identity for every executed trade:
**raw gross P&L − slippage cost − transaction/statutory costs = net P&L**, with maximum absolute residual below 2e-12 in both Base and Stress.

## Research question

Can lagged NIFTY option volume and open-interest microstructure at the completed 09:30 IST bar identify a same-day defined-risk directional debit spread whose weekly performance survives realistic costs and conservative slippage?

## Frozen methodology

- Study window: 2021-07-01 through 2026-08-31.
- Signal information: only 09:25 and 09:30 option observations.
- Features: ATM CE/PE volume imbalance, 09:25→09:30 OI-change imbalance, and a fixed 50/50 joint score.
- Thresholds: absolute score 0.20 and 0.40.
- Expiry buckets: nearest and next NIFTY expiry on/after trade date.
- Direction: positive signal → 1-lot long ATM CE 200-point debit spread; negative signal → 1-lot long ATM PE 200-point debit spread.
- Entry: 09:31 option open.
- Exit: 15:10 same-day option close.
- ATM: nearest ₹50 strike.
- No stops, targets, adjustments, leverage or discretionary overrides.
- Historical lot sizes retained.
- Base slippage: ₹0.20/order.
- Stress slippage: ₹0.40/order.
- Frozen project transaction/statutory charge model carried from the prior friction-corrected research.
- Five deterministic null controls per true cell: seeds 101, 202, 303, 404, 505, with feature values permuted across the complete eligible panel before reapplying the same threshold.

## Data gate

The pinned NIFTY cache passed:
- 1,228 eligible 09:30 sessions.
- Volume and open-interest fields present.
- Nearest-expiry feature coverage: **98.13%**.
- Next-expiry feature coverage: **72.39%**.
- Required gate: 70% / 50%.

The raw execution probe also confirmed exact 09:31 and 15:10 option rows existed for the first qualifying sample. Final executable price coverage averaged **98.54%** across the declared signal cells, with a minimum of **95.74%**.

## Numerical result

All 12 Base cells and all 12 Stress cells had negative total net P&L. **0/12** cells met the discovery promotion gate in Base or Stress.

Promotion gate:
- mean weekly net ≥ ₹5,000;
- median weekly net ≥ ₹5,000;
- positive-week rate ≥ 70%.

| Feature | Threshold | Expiry bucket | Trades | Base total net | Base mean weekly | Base median weekly | Base positive weeks | Stress total net | Stress mean weekly | Stress median weekly | Stress positive weeks |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| VOL_IMB | 0.20 | 0 | 514 | -155,443.73 | -650.39 | -951.13 | 36.82% | -177,829.73 | -744.06 | -1,031.09 | 35.98% |
| VOL_IMB | 0.20 | 1 | 365 | -120,665.00 | -569.17 | -558.48 | 32.55% | -136,033.50 | -641.67 | -632.23 | 30.19% |
| VOL_IMB | 0.40 | 0 | 119 | **-18,566.48** | **-191.41** | **-942.75** | **42.27%** | **-23,821.47** | **-245.58** | **-974.92** | **42.27%** |
| VOL_IMB | 0.40 | 1 | 116 | -36,145.29 | -350.93 | -456.94 | 33.98% | -41,078.86 | -398.82 | -476.93 | 33.01% |
| OI_CHANGE_IMB | 0.20 | 0 | 660 | -170,320.28 | -689.56 | -1,138.07 | 34.82% | -196,991.14 | -797.53 | -1,186.68 | 34.01% |
| OI_CHANGE_IMB | 0.20 | 1 | 535 | -151,010.19 | -671.16 | -663.12 | 32.00% | -172,391.73 | -766.19 | -729.15 | 30.67% |
| OI_CHANGE_IMB | 0.40 | 0 | 334 | -88,544.89 | -494.66 | -980.10 | 33.52% | -101,424.35 | -566.62 | -1,000.09 | 32.40% |
| OI_CHANGE_IMB | 0.40 | 1 | 337 | -76,773.72 | -443.78 | -493.19 | 32.37% | -89,723.37 | -518.63 | -574.37 | 30.06% |
| JOINT | 0.20 | 0 | 450 | -102,864.34 | -476.22 | -904.01 | 36.11% | -121,093.16 | -560.62 | -951.41 | 34.72% |
| JOINT | 0.20 | 1 | 378 | -114,291.66 | -580.16 | -628.42 | 32.49% | -129,284.34 | -656.27 | -690.64 | 29.95% |
| JOINT | 0.40 | 0 | 110 | -58,571.75 | -705.68 | -864.88 | 34.94% | -62,945.91 | -758.38 | -904.86 | 33.73% |
| JOINT | 0.40 | 1 | 142 | -44,128.10 | -408.59 | -503.87 | 29.63% | -49,729.36 | -460.46 | -567.52 | 26.85% |

### Best observed cell

The highest mean weekly net cell was **VOL_IMB, threshold 0.40, nearest expiry**.

Base:
- 119 trades.
- Total net: **-₹18,566.48**.
- Mean weekly net: **-₹191.41**.
- Median weekly net: **-₹942.75**.
- Positive weeks: **42.27%**.
- Worst trade: **-₹5,184.00**.
- Worst week: **-₹5,184.00**.
- Max weekly-equity drawdown: **-₹41,780.75**.
- Trade win rate: **39.50%**.
- Raw gross before costs: approximately **+₹11.00**.
- Slippage cost: **₹5,337.50**.
- Transaction/statutory costs: **₹13,239.98**.

Stress:
- Total net: **-₹23,821.47**.
- Mean weekly net: **-₹245.58**.
- Median weekly net: **-₹974.92**.
- Positive weeks: **42.27%**.
- Worst trade: **-₹5,243.97**.
- Worst week: **-₹5,243.97**.
- Max weekly-equity drawdown: **-₹45,227.85**.
- Trade win rate: **38.66%**.
- Raw gross remains approximately **+₹11.00**.
- Slippage cost: **₹10,595.00**.
- Transaction/statutory costs: **₹13,237.47**.

The result therefore does not show a gross trading edge that merely disappears at the margin: the best cell's raw gross is approximately flat, while the declared friction model turns it clearly negative.

## Null-control robustness

There were 5 placebo seeds for every one of the 12 true cells in each friction regime: **60 null summaries per regime**.

No true cell had a mean weekly net greater than all five null controls.

For the best true cell (VOL_IMB, 0.40, nearest expiry):
- Base true mean weekly net: **-₹191.41**.
- Base mean across five null controls: **-₹3.81/week**.
- Stress true mean weekly net: **-₹245.58**.
- Stress mean across five null controls: **-₹51.23/week**.

These placebo comparisons are diagnostic only; five randomizations per cell are insufficient for a formal significance claim. They nevertheless provide no robustness signal in favor of the true date-linked microstructure feature.

## Aggregate execution counts

Across the 12 research cells, not a portfolio:
- 4,060 executable true trade records in Base.
- 4,060 executable true trade records in Stress.
- 1,000 unique signal days.
- 4,107 qualifying signal observations before execution-leg filtering.
- 4,060 complete-price executions, with 47 signal observations lacking complete executable legs.
- The 12 cells overlap in dates and must not be summed as a single trading portfolio.

## Accounting and friction audit

For both Base and Stress:
**raw gross − slippage − transaction/statutory costs = net P&L**.

The maximum absolute row-level reconciliation residual was approximately **2×10^-12**, consistent with floating-point arithmetic.

The transaction model is the project's frozen friction model used in prior research: date-aware option STT, exchange transaction charge, SEBI charge, stamp duty on buys, GST on applicable components, and fixed brokerage. The execution model separately applies the declared per-order slippage at entry and exit.

## Strengths

- Finite preregistered grid with no result-driven parameter expansion.
- Exact Base/Stress friction comparison.
- Historical lot sizes retained.
- Strict information barrier at 09:30 and execution at 09:31.
- Raw execution-row probe independently confirmed source availability.
- Canonical key normalization removed date/expiry type ambiguity.
- True and placebo calculations use the same execution and cost engine.
- 5-seed null controls are deterministic and generated from the complete feature panel.
- Explicit accounting reconciliation.

## Limitations

- Daily microstructure is based on ATM CE/PE volume and OI changes from 09:25→09:30; deeper strike-surface information and order-book imbalance are not used.
- The signal is evaluated on one-minute option bars with exact timestamps, so source-quality gaps can still remove some executions.
- The defined-risk wing is fixed at 200 points; no optimization is allowed in discovery.
- Five null seeds are diagnostic rather than a formal randomization test.
- The discovery result is not independent OOS evidence; because no cell cleared the discovery gate, WFA/OOS promotion is not authorized.
- The project cost model is a conservative frozen model rather than a reconstruction of every live Paytm Money execution-path detail.

## Conclusion

The preregistered NIFTY OI/volume microstructure hypothesis **does not clear the project's discovery gate**. Every one of the 12 true cells is negative in both Base and Stress, and the best cell is approximately **-₹191/week Base** and **-₹246/week Stress**, far below the target of ₹5,000/week and below the 70% positive-week criterion.

No Phase 31.7 strategy should be promoted, optimized or carried into WFA/OOS.

## Next direction

The next bounded family will test **global overnight cross-market transmission into the NIFTY open**, using a separate daily global-index dataset and an independent finite hypothesis. This follows an NSE working-paper framework that decomposes NIFTY and NASDAQ returns into daytime and overnight components to study information transmission across non-overlapping markets. The next phase will be data-gated before any P&L is accepted. 

## Reproducibility

- Authoritative workflow: 36251189770
- Artifact: 10909111158
- Plan: docs/phase31_7_plan.md
- Engine: research/phase31_7_oi_volume_microstructure.py
- Execution probe: research/phase31_7_execution_probe.py
- Tests: tests/test_phase31_7_oi_volume_microstructure.py
- Core artifact summaries retained in the workflow artifact.

## External evidence

- NSE working paper on NIFTY/NASDAQ overnight and daytime return decomposition: https://nsearchives.nseindia.com/content/research/Paper39.pdf
- GitHub public-markets dataset catalogue: https://github.com/Pubmarks/datasets
- Finance Dataset Pipeline with global index/data categories: https://github.com/benjaminpo/finance-dataset
