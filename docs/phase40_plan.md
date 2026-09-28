# Phase 40 — Prior-Day ATM IV / RV State × Overnight-Gap Implied-Move Dislocation

## Status
PREREGISTERED — ENGINEERING BUILD; NUMERICAL EXECUTION PENDING.

## Research question
Does the next NIFTY session's overnight opening gap become directionally informative when its magnitude is unusually large or small relative to the prior session's ATM option-implied one-session move, conditioned on the prior-day option-implied-volatility versus realized-volatility state?

## Aims and objectives
1. Build a prior-day 15:10 NIFTY ATM IV estimate from the nearest future NIFTY expiry using CE/PE option prices.
2. Compute prior 20-session realized volatility without using any future session.
3. Normalize the next-session overnight gap by the prior-day ATM one-session implied move.
4. Standardize the gap ratio only against the preceding 60 completed signal-day observations.
5. Test fixed continuation and fade mappings with defined-risk debit spreads after realistic transaction costs and slippage.
6. Use fixed permutation null controls and explicit execution/accounting gates before any economic interpretation.

## Frozen information timing
- Prior session = previous completed NIFTY trading session.
- Prior spot reference = prior-session 15:10 NIFTY close.
- Prior ATM strike = deterministic half-up nearest ₹50.
- Signal expiry = nearest NIFTY expiry strictly after the prior session date.
- Prior ATM CE/PE option quote = latest valid positive close at or before 15:10 IST.
- ATM IV = simple mean of CE/PE Black-Scholes IV with r=q=0 and time to expiry-day 15:30 IST.
- Prior RV20 = annualized sample standard deviation of close-to-close returns from the previous 20 completed NIFTY sessions ending on the prior session.
- Current opening gap = 09:15 open / prior 15:10 close − 1.
- One-session implied move = prior ATM IV × sqrt(1/252).
- GAP_RATIO = abs(current opening gap) / one-session implied move.
- GAP_RATIO_Z = current GAP_RATIO standardized against the previous 60 completed signal-day GAP_RATIO observations.
- Current 09:15 open is the first current-session input; no later current-session input enters state construction.

## Frozen state variable
Prior-day IV/RV20 is reported as context and diagnostics. It is not used as a post-result selector. The traded state is the current GAP_RATIO_Z tail.

## Frozen states
- HIGH_GAP_DISLOCATION: GAP_RATIO_Z >= +0.75.
- LOW_GAP_DISLOCATION: GAP_RATIO_Z <= −0.75.
- Otherwise: NO_TRADE.
- Zero overnight gap: NO_TRADE.

## Frozen execution
- CONTINUE: gap up → long ATM CE debit spread; gap down → long ATM PE debit spread.
- FADE: gap up → long ATM PE debit spread; gap down → long ATM CE debit spread.
- Entry: 09:31 option open.
- Exits: 10:30 and 15:10 option close.
- One NIFTY lot.
- 200-point defined-risk debit spread.
- Historical lot sizes by option expiry.

## Discovery matrix
8 true cells: 2 states × 2 mappings × 2 exits.
Five permutation null seeds: 101, 202, 303, 404, 505.

## Data and integrity gates
PASS only if all are satisfied:
- >=95% post-warm-up feature eligibility;
- >=95% prior-day IV input coverage;
- >=95% overnight-gap coverage;
- zero prior-information violations;
- deterministic expiry/strike/lot mapping;
- >=95% execution quote coverage for each true cell;
- accounting reconciliation for each true cell.
A failed gate closes Phase 40 DATA-LIMITED with no Base/Stress economic inference.

## Cost model
- Paytm Money brokerage ₹20 per order.
- Date-aware option-sale STT.
- Exchange transaction charge.
- SEBI turnover fee.
- Stamp duty on buys.
- GST.
- Base slippage ₹0.20 per option-price unit/order.
- Stress slippage ₹0.40 per option-price unit/order.
- Historical lot sizes.

## Promotion gate
In BOTH Base and Stress:
- mean weekly net >= ₹5,000;
- median weekly net >= ₹5,000;
- positive-week rate >=70%;
- execution coverage >=95%;
- accounting reconciliation passes;
- no unresolved data-quality violation.
No WFA/OOS before discovery clears.

## Null controls
For each seed, permute the prior-only GAP_RATIO_Z values across feature-eligible signal dates while keeping the same-session opening-gap direction and all execution prices unchanged. Nulls are diagnostic only.

## Statistical analysis
Weekly net P&L is primary. Report mean, median, positive-week rate, total net, worst week/trade, maximum drawdown, profit factor, bootstrap 95% CI for mean weekly net, trade concentration, yearly summaries, and Base-vs-Stress deltas. Report raw gross P&L, slippage and transaction/statutory costs separately.

## Stop rule
No post-result change to the 20-session RV window, 60-session GAP_RATIO lookback, ±0.75 thresholds, IV construction, one-session scaling, expiry rule, 15:10 prior-day snapshot, gap direction rule, spread width, entry, exit, lot sizing or cost model.