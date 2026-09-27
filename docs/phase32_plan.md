# Phase 32 — Options Skew / Smile Dislocation

## Status
PREREGISTERED — implementation and data-gate tests must pass before any P&L is accepted.

## Research question
Does the shape of the NIFTY option-implied-volatility surface at 09:30 IST — specifically downside-vs-upside skew and near-ATM smile curvature — contain enough short-horizon mean-reversion information to produce a defined-risk, cost-aware strategy that can clear the project's ₹5,000 net-per-week target?

This is a materially distinct family from the retired ORB, OI/volume, global overnight, India-VIX/RV, and institutional-positioning families. It uses option prices themselves to infer the surface state.

## Aims
1. Measure prior-normalized NIFTY skew and smile curvature from executable option prices.
2. Test whether extreme surface states are associated with subsequent option-spread mean reversion.
3. Express the signal only through bounded-risk four-leg structures with deterministic strikes and no discretionary adjustment.
4. Quantify the effect of brokerage, statutory charges and doubled slippage.
5. Close the family after the finite discovery grid if the economic gate is not reached.

## Objectives
- Reuse the pinned NIFTY/index-options dataset already audited for earlier phases.
- Infer single-option Black-Scholes IV from 09:30 option closes with q=0 and r=0, matching the project's existing IV convention.
- Use the strictly next available NIFTY expiry (expiry date > trade date) to avoid same-day expiry IV singularity and keep the surface horizon stable.
- Construct:
  - SKEW_VOLPTS = IV(ATM-100 PE) - IV(ATM+100 CE)
  - SMILE_VOLPTS = 0.5 × [IV(ATM-100 PE) + IV(ATM+100 CE)] - 0.5 × [IV(ATM CE) + IV(ATM PE)]
- Convert each raw feature to a 60-session prior-only z-score.
- Freeze thresholds |z| >= 1.0 and |z| >= 1.5.
- Freeze exits at 10:30, 13:30 and 15:10 IST.
- Run five full-panel null permutations per feature and friction regime.
- Use historical NIFTY lot sizes and the existing Paytm Money/NSE cost model.
- Persist feature, quote, trade, weekly, coverage, null, bootstrap and manuscript artifacts.

## Study window
2021-07-01 through 2026-08-31, subject to the pinned source's actual coverage. The window is not shortened because of missing data; the data gate reports any shortfall explicitly.

## Primary data
Pinned source already used by the project:
- Hugging Face dataset: `thetrademarkk/india-index-options-1m`
- Revision: `51ca58c`
- Index cache: `index/NIFTY.parquet`
- Options cache: `options/NIFTY/*.parquet`

Secondary provenance/validation sources:
- NSE option chain and historical derivatives reports.
- Zenodo NIFTY spot/futures/options 1-minute archive (2017–2020) for independent methodological/data-source corroboration only.
- Public NIFTY volatility-surface implementations for schema/methodology reconnaissance only.

## Signal construction
At 09:30 IST:
1. Read the 09:30 NIFTY close and round to the nearest ₹50 strike.
2. Select the next available NIFTY expiry strictly after the trade date.
3. Read 09:30 closes for ATM CE, ATM PE, ATM-100 PE and ATM+100 CE.
4. Invert each option price to IV using Black-Scholes with q=0, r=0.
5. Compute the two raw surface features above.
6. Standardize using only the previous 60 completed signal-session observations of the same raw feature.
7. A signal may be generated only at 09:30 close and is executed at 09:31 open.

No 09:31 or later price, OI, volume, or outcome enters the feature.

## Frozen strategy expressions

### SKEW_Z
High positive skew z-score means downside IV is rich relative to upside IV:
- z >= threshold: BUY CE(ATM+50), SELL CE(ATM+100), SELL PE(ATM-100), BUY PE(ATM-50).
- z <= -threshold: reverse every leg.
This is a four-leg capped risk-reversal / wing spread.

### SMILE_Z
High positive smile z-score means near-ATM wings are rich relative to ATM:
- z >= threshold: SELL PE(ATM-50), BUY PE(ATM-100), SELL CE(ATM+50), BUY CE(ATM+100).
- z <= -threshold: reverse every leg.
This is a bounded short/long iron-condor pair. It is intentionally symmetric and has no directional selection.

Each structure is one NIFTY lot. No stops, targets, leverage, rolling, adjustments or discretion are allowed.

## Frozen grid
- Features: SKEW_Z, SMILE_Z (2)
- Thresholds: |z| >= 1.0, |z| >= 1.5 (2)
- Exits: 10:30, 13:30, 15:10 (3)
- True cells: 2 × 2 × 3 = 12
- Null seeds: 101, 202, 303, 404, 505

A cell is not reparameterized from its observed outcome.

## Data gates
The phase may enter Base/Stress discovery only if:
1. The pinned NIFTY cache passes the existing integrity tests.
2. A strictly-next expiry file exists for at least 95% of warm-up-complete signal sessions.
3. All four 09:30 surface quotes (ATM CE, ATM PE, ±100 wings) are present and positive for at least 95% of warm-up-complete sessions.
4. IV inversion succeeds for at least 95% of required surface quotes and produces finite positive values.
5. The 60-session prior-only barrier has zero violations.
6. All 12 true cells have >=95% complete execution-price coverage across all four legs and both timestamps for their own signals.
7. The pinned source revision and file manifest are recorded.

If a gate fails, the phase is DATA-LIMITED; no substitute data or relaxed gate is introduced after inspection.

## Costs and execution
Retain the audited project model:
- historical NIFTY lot sizes;
- Paytm Money brokerage;
- option STT and other date-aware statutory/exchange charges;
- Base slippage ₹0.20 per option-price unit per order;
- Stress slippage ₹0.40 per order.

Accounting identity:
net P&L = raw gross P&L - slippage cost - transaction/statutory costs.

Signal at 09:30 is filled at 09:31 open. Exit is at the next declared minute close.

## Statistical analyses
For every true and null cell:
- total trades and active weeks;
- total/mean/median weekly net;
- profitable-week rate;
- executed-week coverage;
- worst trade/week;
- max drawdown;
- raw gross, slippage and transaction/statutory costs;
- annual/regime breakdown;
- true-vs-null comparisons;
- bootstrap 95% interval for mean weekly net;
- cost/slippage sensitivity diagnostics.

The bootstrap uses weekly net P&L as the resampling unit and is descriptive, not a license to tune the grid.

## Promotion gate
A true cell advances only if, in both Base and Stress:
- mean weekly net >= ₹5,000;
- median weekly net >= ₹5,000;
- positive-week rate >= 70%;
- execution coverage >= 80%;
- no test-period parameter or structure change.

If no cell qualifies, no WFA/OOS is opened.

## Stop rule
Phase 32 stops after:
- data gate;
- frozen 12-cell Base discovery;
- frozen 12-cell Stress discovery;
- 60 null summaries per friction;
- independent artifact validation;
- final manuscript update.

No new thresholds, strike offsets, DTE rules, exits, structures or surface definitions are introduced from observed P&L.

## Required outputs
- source manifest;
- surface quote/IV ledger;
- feature panel;
- true and null signal ledgers;
- Base/Stress trade ledgers;
- weekly summaries;
- execution coverage;
- bootstrap intervals;
- null-control summaries;
- plots;
- final manuscript with abstract, background, methodology, results, inference, discussion, strengths, limitations, conclusion, future directions, references and reproducibility notes.
