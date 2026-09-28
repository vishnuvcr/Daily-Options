# Phase 38 — NIFTY Opening Volatility / Price-Structure

## Status
PREREGISTERED / READY FOR NUMERICAL EXECUTION.

## Research question
Can a NIFTY-specific early-session volatility regime, measured from the first 15 minutes and conditioned on the opening directional move, identify a short-horizon directional option-spread edge after realistic trading costs?

## Literature basis
The opening interval is documented as a distinct volatility regime in Indian equity markets, and opening-range breakout research provides a testable mechanism for continuation after early-session expansion. Recent cost-aware preregistered ORB evidence also motivates an explicit friction gate rather than accepting gross-return patterns. See `docs/phase38_literature_review.md`.

## Frozen feature construction
Study window: 2021-07-01 through 2026-08-31 on the pinned exact-expiry NIFTY 1-minute source.

For each NIFTY trading session:
1. Use 09:15 bar open as the session-opening reference.
2. Use only bars timestamped 09:15:00 through 09:29:00 to construct the opening 15-minute range.
3. `early_range_pct = (max(high)-min(low)) / open_0915`.
4. `early_return = (close_0929-open_0915)/open_0915`.
5. Compute a 60-session strictly-prior rolling mean and sample standard deviation of `early_range_pct`.
6. `RANGE_Z = (early_range_pct-current_prior_mean)/current_prior_std`.
7. Signal states:
   - HIGH_VOL: RANGE_Z >= +0.75
   - LOW_VOL: RANGE_Z <= -0.75
   - otherwise no trade.
8. Direction is the sign of `early_return`; zero is no trade.

The 09:30 NIFTY close remains the authoritative ATM reference for the option structure, matching the established execution contract.

## Frozen direction mappings
Both mappings are tested without choosing between them after seeing results:
- CONTINUE: trade in the sign of `early_return`.
- FADE: trade opposite the sign of `early_return`.

## Frozen option execution
- One-lot 200-point debit spread.
- ATM strike = nearest ₹50 to NIFTY 09:30 bar close.
- Bullish signal = long ATM CE / short CE at ATM+₹200.
- Bearish signal = long ATM PE / short PE at ATM-₹200.
- Entry = 09:31 option open using local trading time.
- Exit = 10:30 or 15:10 option close using local trading time.
- Nearest available NIFTY expiry on or after the trade date.
- Historical NIFTY lot sizes.
- No stops, targets, adjustments, leverage, or discretionary exclusions.

## Frozen discovery matrix
8 true cells:
- HIGH_VOL × CONTINUE × 10:30
- HIGH_VOL × CONTINUE × 15:10
- HIGH_VOL × FADE × 10:30
- HIGH_VOL × FADE × 15:10
- LOW_VOL × CONTINUE × 10:30
- LOW_VOL × CONTINUE × 15:10
- LOW_VOL × FADE × 10:30
- LOW_VOL × FADE × 15:10

## Null controls
Five fixed seeds: 101, 202, 303, 404, 505.

For each seed, jointly permute the prior-only RANGE_Z values across NIFTY trading dates while holding the same-day early_return fixed. Recompute HIGH_VOL/LOW_VOL state from the permuted RANGE_Z. Execution, costs, expiry and option prices remain unchanged.

The nulls are diagnostic falsification controls, not a post-hoc selection device.

## Data and integrity gates
PASS requires:
- at least 95% of NIFTY sessions eligible after the 60-session prior-only warm-up have valid RANGE_Z and early_return;
- zero prior-information violations;
- at least 95% execution quote coverage for every true cell;
- deterministic expiry/strike/lot mapping;
- accounting reconciliation for every friction run.

A failed gate closes the phase as DATA-LIMITED with no economic interpretation.

## Cost model
Use the established Paytm Money/NSE/statutory model:
- Paytm Money brokerage ₹20 per order;
- date-aware option-sale STT;
- exchange transaction charge;
- SEBI turnover fee;
- stamp duty on buys;
- GST on applicable services;
- Base slippage ₹0.20 per option-price unit per order;
- Stress slippage ₹0.40.

Historical lot sizes are applied by expiry date.

## Statistical analysis
Primary:
- weekly net P&L;
- mean weekly net;
- median weekly net;
- positive-week fraction;
- execution coverage.

Secondary:
- total net;
- worst trade/week;
- maximum drawdown;
- raw gross P&L;
- slippage cost;
- transaction/statutory costs;
- null-control distributions;
- yearly and regime counts.

## Promotion gate
A true cell is promotable only if, in BOTH Base and Stress:
- mean weekly net >= ₹5,000;
- median weekly net >= ₹5,000;
- positive-week rate >= 70%.

No WFA/OOS is authorized unless the frozen discovery gate clears.

## Stop rule
No post-result change to:
- 15-minute interval;
- 60-session lookback;
- ±0.75 RANGE_Z thresholds;
- CONTINUE/FADE mappings;
- 09:31 entry;
- 10:30/15:10 exits;
- 200-point spread width;
- expiry rule;
- cost model.

## Deliverables
Plan, literature review, tests, workflow, source manifest, data gate, Base/Stress ledgers, null controls, price coverage, accounting reconciliation, final manuscript, status update and error-log update.
