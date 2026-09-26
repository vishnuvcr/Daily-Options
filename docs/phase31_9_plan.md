# Phase 31.9 — India VIX × Realized Volatility × NIFTY Opening-Gap Direction

## Status
Preregistered research family. No numerical result is accepted before the data gate, unit tests, Base/Stress validation and artifact audit complete.

## Research question
Does the relationship between the prior-session India VIX close and prior-only NIFTY 20-session realized volatility identify opening-gap regimes in which a simple NIFTY directional debit spread has enough incremental expectancy to reach the project's ₹5,000 net/week promotion threshold after Paytm Money/NSE costs and conservative slippage?

## Aims
1. Quantify whether the prior-day implied-volatility/realized-volatility ratio conditions opening-gap directionality.
2. Test whether following versus fading the opening gap behaves differently across low, neutral and high VIX/RV regimes.
3. Measure whether any apparent directional edge survives real option execution costs and doubled slippage.
4. Reject the family early when the frozen discovery grid cannot meet the economic gate, preventing post-result tuning.

## Objectives
- Reconstruct a no-lookahead daily panel from the pinned NIFTY 1-minute source and official NSE India VIX historical data.
- Compute NIFTY RV20 from completed daily close-to-close returns only.
- Merge prior-day India VIX and prior-only RV20 into each NIFTY session using a strict date barrier.
- Freeze three VIX/RV regimes: LOW (ratio ≤ 0.90), MID (0.90 < ratio ≤ 1.10), HIGH (ratio > 1.10).
- Freeze two gap directions: FOLLOW_GAP and FADE_GAP.
- Freeze two exits: 10:30 and 15:10.
- Evaluate 12 true cells plus 5 fixed full-panel null permutations per cell (60 null summaries per friction regime).
- Include historical expiry and lot-size mappings, slippage, brokerage, exchange/statutory charges and execution coverage.

## Frozen design

### Study window and universe
- Study dates: 2021-07-01 through 2026-08-31.
- Underlying: NIFTY 50.
- Source: pinned TradeMarkk NIFTY 1-minute parquet cache for option/index execution and official NSE India VIX history for VIX closes.
- Entry signal: NIFTY 09:30 opening price compared with the previous completed NIFTY session close.
- Entry execution: 09:31 option bar.
- Exit: 10:30 or 15:10 option close bar.
- Structure: 1-lot ATM directional debit spread, 200-point wing.
- Expiry: nearest on/after trading date.
- Lot size: historical schedule from project cost/contract utility.

### Regime feature
For each NIFTY trading date t:
- RV20_t = annualized standard deviation of the previous 20 completed close-to-close NIFTY log returns, multiplied by sqrt(252).
- IndiaVIX_t = previous completed session's India VIX close.
- RV20 is expressed in percentage points before forming the ratio.
- VIX_RV_RATIO_t = IndiaVIX_t / RV20_t.
- No current-day VIX or current-day close enters the signal.

### Frozen regimes
- LOW: ratio ≤ 0.90
- MID: 0.90 < ratio ≤ 1.10
- HIGH: ratio > 1.10

These cut points are fixed before numerical execution and must not be changed after observing results.

### Direction rules
- FOLLOW_GAP: positive gap -> CALL spread; negative gap -> PUT spread.
- FADE_GAP: positive gap -> PUT spread; negative gap -> CALL spread.
- Zero gap is no trade.

### Frozen grid
3 regimes × 2 direction modes × 2 exits = 12 true cells.

### Null controls
Five fixed seeds: 101, 202, 303, 404, 505.
For each seed, permute the regime label across the complete feature-eligible session panel, then rebuild signals with the same direction and exit rules. Do not permute only already-triggered signals.

## Data and quality gates
- Unit tests must pass before data acquisition.
- India VIX acquisition must validate source response structure, monotonic unique dates, nonempty OHLC/close values, expected study-window coverage and a cryptographic manifest.
- Global/NIFTY panel must pass a strict prior-date barrier.
- 20-session RV warm-up sessions are reported separately and excluded only from the feature-coverage denominator.
- Feature-eligible coverage must be ≥95%.
- Every true cell must have ≥95% complete execution-price coverage before numerical results are accepted.
- Accounting identity must reconcile: net = raw gross − slippage cost − transaction/statutory costs.

## Cost and execution model
Base slippage = ₹0.20 per option price unit per order.
Stress slippage = ₹0.40 per option price unit per order.
Brokerage and date-aware exchange/statutory costs are inherited from the frozen project cost model used in Phases 31.7–31.8.
No hidden scaling, no selective weeks, no lot-size cherry-picking.

## Statistical analysis
For each true and null cell report:
- total and mean/median weekly net P&L;
- positive-week rate;
- trade count and execution coverage;
- worst trade/week and max drawdown;
- raw gross, slippage and transaction/statutory cost totals;
- Base/Stress comparison;
- true-versus-null mean-weekly comparison;
- regime and year/session breakdown;
- bootstrap interval and cost-sensitivity diagnostics in the final manuscript stage.

## Promotion gate
A discovery cell is eligible for WFA/OOS only if, before any OOS tuning:
- mean weekly net ≥ ₹5,000;
- median weekly net ≥ ₹5,000;
- ≥70% positive weeks;
- ≥80% eligible-week execution coverage;
- passes both Base and Stress;
- does not rely on a result-specific parameter change.

If no cell qualifies, Phase 31.9 closes without WFA/OOS.

## Scientific interpretation
A positive discovery result is hypothesis-generating, not proof of tradability. A null-control separation without sufficient absolute P&L is not a promotion. A negative family result should be retired without retuning the regime thresholds.

## Failure/repair discipline
Any engineering error is recorded in `docs/error_log.md`, the phase status is updated, and only then is a corrected run triggered. Frozen signal definitions and cost assumptions are not altered to repair implementation errors.
