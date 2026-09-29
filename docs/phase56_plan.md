# Phase 56 — Prior-Session Candle Conviction Regime × Opening-Gap Direction

## Research question

Does the directional conviction of the immediately preceding NIFTY session, measured by the prior candle body relative to its high-low range, condition whether the next session's opening gap continues or reverses strongly enough to produce at least ₹5,000 net per completed trading week after realistic costs?

## Literature rationale

Gap-opening research distinguishes different gap contexts and post-gap adjustments rather than treating every opening discontinuity identically. Price-action literature also treats the prior bar's body and range as measures of directional conviction, while empirical OHLC research emphasizes that simple candle structure can contain information but may be too small to overcome trading friction.

Sources:
- https://pmc.ncbi.nlm.nih.gov/articles/PMC10017064/
- https://doi.org/10.1002/9781119202622.ch20
- https://www.researchgate.net/publication/404476167_Structural_Limits_of_OHLCV-Based_Intraday_Signals_in_MNQ_Futures_A_Systematic_Falsification_Study

These sources motivate the hypothesis only; no external profitability result or threshold is imported.

## Frozen feature construction

For current date t:
- Prior session open = prior 09:15 NIFTY open.
- Prior session high/low = prior 15:10 high/low.
- Prior session close = prior 15:10 close.
- BODY_RATIO = abs(prior close − prior open) / (prior high − prior low).
- BODY_DIRECTION = sign(prior close − prior open), stored descriptively but not used for state selection.
- State distribution is built from the last 60 valid BODY_RATIO observations strictly before t:
  - LOW_CONVICTION: below empirical 33.333rd percentile.
  - MID_CONVICTION: 33.333rd to below 66.667th percentile.
  - HIGH_CONVICTION: at or above 66.667th percentile.
- Current opening direction = sign(current 09:15 open / prior 15:10 close − 1).
- Zero opening gap = NO_TRADE.

All state inputs are known before the current session opens. No current-day information after 09:15 enters the state.

## Frozen execution

- FOLLOW_OPEN and FADE_OPEN.
- Entry 09:31 IST option open.
- Exits 10:30 and 15:10 IST option close.
- One-lot 200-point ATM directional debit spread.
- ATM = nearest ₹50 strike to 09:30 NIFTY close.
- Execution expiry = nearest NIFTY expiry on/after current trading date.
- Historical NIFTY lot sizes.
- Existing Paytm Money/NSE/statutory costs.
- Base slippage ₹0.20; Stress ₹0.40 per option-price unit/order.

## Discovery matrix and controls

3 conviction states × 2 mappings × 2 exits = 12 true cells.

Five fixed state-permutation null seeds: 101, 202, 303, 404, 505. Nulls permute only the prior-only conviction labels across eligible dates while preserving same-day opening direction and all execution prices.

## Data gates

- ≥95% post-warm-up feature eligibility.
- ≥95% prior-session OHLC/range completeness.
- ≥95% deterministic expiry mapping.
- Zero prior-information violations.
- ≥95% execution coverage in every true cell.
- Full Base/Stress accounting reconciliation.

## Promotion gate

Both Base and Stress:
- mean weekly net ≥₹5,000;
- median weekly net ≥₹5,000;
- positive-week rate ≥70%;
- execution coverage ≥95%;
- clean accounting.

No WFA/OOS unless at least one frozen cell clears the full gate in both friction regimes.

## Stop rule

No post-result change to the body-ratio definition, 60-session history, tercile boundaries, body direction treatment, gap mapping, execution timing, spread width, expiry rule, or cost model.
