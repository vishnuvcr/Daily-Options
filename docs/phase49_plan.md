# Phase 49 — Prior-Session Range Regime × Opening-Gap Direction

## Research question

Does the volatility regime of the immediately preceding NIFTY session—classified from its range relative to a strictly prior 60-session range distribution—condition whether the next session's opening gap continues or reverses strongly enough to generate at least ₹5,000 net per completed trading week after realistic costs?

## Literature rationale

Research on opening gaps shows that gap behavior is not independent of volatility context. Gap-size studies normalize gaps by prior-day range to remove changing volatility effects, while research on contraction/expansion regimes motivates testing whether prior calm versus expansion states alter subsequent intraday opportunity.

Useful references:
- Steenbarger, gap size normalized by prior day's high-low range: https://traderfeed.blogspot.com/2006/11/do-opening-gaps-tend-to-fill.html
- Häggström et al., opening-range breakout and contraction-expansion principle: https://www.sciencedirect.com/science/article/pii/S1544612312000438
- Plastun et al., gap anomaly and continuation/reversal: https://www.sciencedirect.com/science/article/pii/S1062940820300747
- Stocks Opening Price Gaps and Adjustments to New Information: https://pmc.ncbi.nlm.nih.gov/articles/PMC10017064/
- 2026 global-index opening-gap research documenting heavy tails and volatility clustering: https://www.sciencedirect.com/science/article/pii/S2214845026000918

These sources motivate the hypothesis only; no external profitability result or threshold is imported.

## Frozen feature construction

For current trading date t:
- Prior completed NIFTY session range percentage = (prior-session 15:10 high - prior-session 15:10 low) / prior-session 15:10 close.
- Build the empirical distribution from the **60 completed range observations strictly before the prior session**.
- LOW_RANGE_REGIME: current prior-session range is below the rolling 33.333rd percentile.
- MID_RANGE_REGIME: between the rolling 33.333rd and 66.667th percentiles.
- HIGH_RANGE_REGIME: at or above the rolling 66.667th percentile.
- A zero or invalid range is excluded.
- Current opening gap = current 09:15 open / prior-session 15:10 close - 1.
- Zero gap = no trade.
- All state inputs are known before the current market opens.

The rolling percentiles are calculated separately for each date using only preceding observations. No current-day or future data enters the regime state.

## Frozen execution

- FOLLOW_GAP and FADE_GAP.
- Entry 09:31 IST option open.
- Exits 10:30 and 15:10 IST option close.
- One-lot 200-point ATM directional debit spread.
- ATM = nearest ₹50 strike to 09:30 NIFTY close using deterministic half-up rounding.
- Nearest NIFTY expiry on/after current trade date.
- Historical NIFTY lot sizes.
- Existing Paytm Money/NSE/statutory charges.
- Base slippage ₹0.20; Stress ₹0.40 per option-price unit/order.

## Discovery matrix and controls

3 volatility states × 2 gap mappings × 2 exits = 12 true cells.

Five fixed state-permutation null seeds 101/202/303/404/505. Only the prior-only regime labels are permuted across feature-eligible dates; same-day gap direction and execution prices remain unchanged.

## Data gates

- >=95% post-warm-up feature eligibility.
- >=95% prior-range validity and rolling-regime coverage among eligible dates.
- Zero prior-information violations.
- >=95% deterministic expiry mapping.
- >=95% execution coverage in every true cell.
- Full accounting reconciliation in Base and Stress.

## Promotion gate

In both Base and Stress:
- mean weekly net >= ₹5,000;
- median weekly net >= ₹5,000;
- positive-week rate >=70%;
- execution coverage >=95%;
- clean accounting.

No WFA/OOS unless at least one frozen true cell clears the complete gate in both friction regimes.

## Statistical analysis

Primary:
- mean/median weekly net;
- positive-week rate;
- total net P&L;
- worst week/trade;
- maximum drawdown;
- execution coverage;
- Base-to-Stress degradation.

Secondary:
- low/mid/high regime differences;
- FOLLOW versus FADE within each regime;
- true-cell versus matched permutation-null means;
- calendar-year descriptive stability.

## Stop rule

No post-result adjustment to the 60-session history length, percentile boundaries, regime definition, gap mapping, entry, exits, spread width, expiry rule, or cost model.
