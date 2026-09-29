# Phase 48 — Prior-Session Return Direction × Opening-Gap Direction

## Research question

Does the direction of the immediately preceding NIFTY session condition whether the next session's opening gap continues or reverses strongly enough to generate economically meaningful weekly net P&L after realistic costs?

## Literature rationale

A published study of TOPIX futures and 10-year JGB futures explicitly evaluates previous one-day return measures together with opening-gap measures as short-horizon predictors, motivating a joint test of prior-session direction and current-session gap direction rather than using either variable alone.

Gap research also indicates that post-gap continuation/reversal varies with the information context and gap direction. This phase therefore tests a simple two-state prior-session directional context without importing external thresholds or profitability claims.

Sources:
- https://www.sciencedirect.com/science/article/abs/pii/S104402830600007X
- https://www.sciencedirect.com/science/article/pii/S1062940820300747
- https://pmc.ncbi.nlm.nih.gov/articles/PMC10017064/

## Frozen feature construction

For trading date t:
- Prior-session return = prior completed NIFTY 15:10 close / the NIFTY 15:10 close from the session immediately before that − 1.
- PRIOR_UP if prior-session return > 0.
- PRIOR_DOWN if prior-session return < 0.
- Exactly zero prior-session return is NO_TRADE for this phase.
- Current opening gap = current 09:15 NIFTY open / prior completed 15:10 close − 1.
- Exactly zero opening gap is NO_TRADE.
- Both features are known before the 09:15 regular session.

## Frozen execution

- CONTINUE: follow the current opening-gap direction.
- FADE: take the opposite direction.
- Entry: 09:31 IST option open.
- Exits: 10:30 and 15:10 IST option close.
- One-lot 200-point ATM directional debit spread.
- ATM: nearest ₹50 strike to 09:30 NIFTY close using deterministic half-up rounding.
- Nearest NIFTY expiry on/after current trade date.
- Historical NIFTY lot sizes.
- Existing Paytm Money/NSE/statutory charges.
- Base slippage ₹0.20; Stress ₹0.40 per option-price unit/order.

## Discovery matrix and nulls

2 prior-session states × 2 gap mappings × 2 exits = 8 true cells.

Five fixed state-permutation nulls per cell, seeds 101/202/303/404/505. Only the prior-session state labels are permuted across eligible dates; current gap direction and execution prices remain unchanged.

## Data gates

- >=95% feature eligibility and prior-return coverage.
- >=95% deterministic expiry mapping.
- Zero prior-information violations.
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
- mean and median weekly net;
- positive-week rate;
- total net P&L;
- worst trade/week;
- maximum drawdown;
- execution coverage;
- Base versus Stress degradation.

Secondary:
- same-direction versus opposite-direction prior/gap combinations;
- true cells versus matched permutation-null means;
- year-level descriptive stability.

## Stop rule

No post-result change to prior-return definition, zero-return handling, state construction, gap mapping, entry, exits, spread width, expiry rule or cost model.
