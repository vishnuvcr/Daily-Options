# Phase 31.10 — Institutional Futures Positioning × NIFTY Opening-Gap Translation

## FINAL STATUS
PREREGISTERED — data gate pending. No numerical result is accepted before source validation, unit tests, execution coverage, Base/Stress validation and null-control audit.

## Research question
Does prior-session participant-wise NIFTY index-futures positioning — especially FII/DII net long-vs-short positioning — contain enough directional information to improve same-day defined-risk NIFTY option-spread expectancy after realistic brokerage, statutory costs and Base/Stress slippage?

A secondary question is whether any positioning signal behaves differently after a positive versus negative NIFTY opening gap. Gap state is a registered diagnostic/stratification variable, not a result-driven filter.

## Aims
1. Quantify the incremental information in participant-wise F&O positioning for next-session NIFTY direction.
2. Separate FII, DII and FII-vs-DII positioning information using prior-only standardized features.
3. Measure whether any signal survives exact option execution, historical lot sizes, Paytm Money/NSE transaction charges and doubled slippage.
4. Examine whether observed positioning effects are associated with opening-gap direction without introducing a second unregistered selection layer.
5. Close the family after the finite grid if the economic gate is not reached; do not tune thresholds after seeing results.

## Objectives
- Acquire the complete participant-wise NSE F&O open-interest archive for the study window.
- Parse FII, DII, Pro and Client index-futures long/short positions.
- Construct three prior-only standardized features.
- Freeze a 12-cell discovery grid before numerical execution.
- Run five complete-panel null permutations per cell and friction regime.
- Reuse the audited pinned NIFTY option/index source and frozen project cost model.
- Report gap-aligned versus gap-opposed diagnostics without using them to select a discovery winner.
- Persist raw-source manifests, daily feature ledger, trades, weekly ledgers, summaries, coverage, accounting reconciliation and final manuscript inputs.

## Study window
2021-07-01 through 2026-08-31, subject to the exact data gate. The window is frozen before acquisition and will not be shortened because of the amount of data obtained.

## Primary data
### Official NSE participant-wise F&O OI
Source family:
- `https://nsearchives.nseindia.com/content/nsccl/fao_participant_oi_DDMMYYYY.csv`
- Official NSE F&O historical reports page: `https://www.nseindia.com/all-reports-derivatives#cr_deriv_equity_archives`

The report contains participant categories Client, DII, FII and Pro, with futures/options long/short fields. Only **index-futures** long/short fields are used in the registered feature grid.

The static archive is treated as the source of record. Every retrieved file is hashed and stored in the repository cache. 404/non-published dates are recorded rather than silently dropped.

### Auxiliary FII/DII cash activity
NSE's `fiidiiTradeReact` endpoint is probed and recent cash FII/DII data are cached when available. Because the public endpoint is current-day oriented and public historical mirrors have incomplete/rolling coverage, cash-flow history is **not** used in the frozen 12-cell true grid. It is retained as an auxiliary provenance/cross-check dataset only, with its actual coverage reported. This avoids fabricating a historical daily series.

## Frozen feature construction
For each NIFTY trade date t, only participant OI from the immediately preceding completed trading date t-1 is eligible.

For each participant p:
`IDX_NET_RATIO_p = (FUTIDX_LONG_p - FUTIDX_SHORT_p) / (FUTIDX_LONG_p + FUTIDX_SHORT_p)`

Three feature families:
1. **FII_IDX_NET_Z** — 60-observation prior-only z-score of the FII index-futures net ratio.
2. **DII_IDX_NET_Z** — 60-observation prior-only z-score of the DII index-futures net ratio.
3. **FII_DII_DIVERGENCE_Z** — 60-observation prior-only z-score of (FII index-futures net ratio − DII index-futures net ratio).

The z-score for date t uses only observations strictly earlier than the selected t-1 positioning observation. No current-day market data enters the feature.

## Frozen execution and signal mapping
- Signal is evaluated after the prior-session participant OI is known and before the current NIFTY open.
- Positive signal values map to a long ATM NIFTY call debit spread.
- Negative signal values map to a long ATM NIFTY put debit spread.
- Thresholds: |z| >= 0.50 and |z| >= 1.00.
- Entry: 09:31 option open.
- Exit horizons: 10:30 option close and 15:10 option close.
- Expiry: nearest NIFTY expiry on/after trade date.
- ATM: nearest ₹50 strike.
- Structure: 1-lot, 200-point directional debit spread.
- Historical lot sizes.
- No stops, targets, leverage, adjustment, discretion or result-specific filters.

Grid size = 3 features × 2 thresholds × 2 exit horizons = **12 true cells**.

## Opening-gap diagnostic
For each trade date:
`GAP_PCT = (09:30 NIFTY price - previous completed NIFTY close) / previous close`

The feature sign and gap sign are cross-tabulated after the frozen run:
- positioning-aligned gap;
- positioning-opposed gap;
- positive/negative gap;
- gap magnitude buckets.

These diagnostics are descriptive and cannot be used to remove trades, add thresholds or select a cell after seeing P&L.

## Null controls
For each feature, permute the complete feature series across feature-eligible NIFTY dates using seeds:
101, 202, 303, 404, 505.

Permutation occurs **before thresholding and execution**. The empirical distribution remains unchanged while date-level association is destroyed. Nulls are diagnostic only and cannot be promoted.

## Data gates
The phase may enter Base/Stress only if:
1. participant-wise OI files are available for at least 95% of feature-eligible study dates;
2. FII and DII index-futures long/short fields are present and numerically parseable;
3. the prior-date barrier has zero violations;
4. at least 60 prior positioning observations exist for each standardized feature before the first eligible signal;
5. duplicate source rows are resolved deterministically and logged;
6. official source hashes/manifest are complete;
7. every true cell has at least 95% complete execution-price coverage;
8. the pinned NIFTY cache passes its existing data-integrity tests.

If the gate fails, the phase closes DATA-LIMITED without changing the study dates or inventing substitutes.

## Costs and execution
Use the frozen project charge model from Phases 31.7–31.9:
- historical lot sizes;
- brokerage;
- STT;
- exchange charges;
- SEBI charges;
- stamp duty;
- GST;
- Base slippage ₹0.20 per option price unit per order;
- Stress slippage ₹0.40 per option price unit per order.

Accounting must satisfy:
`net P&L = raw gross - slippage cost - transaction/statutory costs`

## Statistical analysis
For every true/null cell:
- trades, eligible weeks and executed-week coverage;
- total, mean and median weekly net;
- positive-week rate;
- worst trade and worst week;
- max drawdown;
- raw gross, slippage and transaction/statutory costs;
- year/regime/gap-state breakdown;
- true-versus-null comparisons;
- bootstrap intervals only after discovery completion;
- cost/slippage sensitivity as a diagnostic, never as a post-result tuning mechanism.

## Promotion gate
A true cell is eligible for WFA/OOS only if it satisfies in both Base and Stress:
- mean weekly net >= ₹5,000;
- median weekly net >= ₹5,000;
- positive-week rate >= 70%;
- execution coverage >= 80%;
- no result-specific parameter change.

If no cell qualifies, Phase 31.10 closes without WFA/OOS.

## Literature/evidence basis
Institutional-flow research is mixed: published work reports relationships between FII activity, NIFTY returns and volatility, but strength and direction can vary by horizon and specification. The phase therefore treats institutional positioning as a falsifiable hypothesis rather than an established edge.

NSE's current historical-reports/data-sharing documentation identifies FII/FPI and DII trading activity and equity-derivatives archives as available market-data families. Public implementations also document the participant-wise OI archive and its participant categories. References and provenance are collected in `docs/phase31_10_literature_review.md`.

## Stop rule
Close after the frozen 12 true cells plus 60 null summaries per friction. No new participant type, threshold, lookback, horizon, structure, gap filter or source is introduced because of observed P&L.

## Required outputs
- source manifest and SHA-256 hashes;
- participant-OI raw cache;
- auxiliary FII/DII cash coverage report;
- daily positioning feature ledger;
- true and null trade ledgers;
- weekly ledgers;
- Base/Stress true-cell summaries;
- null-control summaries;
- execution coverage;
- gap-state diagnostic tables;
- accounting reconciliation;
- final research manuscript with graphs, tables, appendices and reproducibility notes.
