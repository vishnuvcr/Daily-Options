# Phase 50 — Opening Location Relative to Prior Range × Gap Direction

## Research question

Does the structural location of the 09:15 NIFTY open relative to the prior completed session's high-low range distinguish continuation versus reversal outcomes after realistic option trading costs?

## Literature rationale

Gap research distinguishes partial gaps, where the open remains inside the previous day's range, from full gaps that open beyond the prior high or low. A 2023 empirical study explicitly separates full and partial gaps and reports different subsequent price adjustment behavior. Recent practitioner research also classifies gap openings as inside-range versus outside-range and then studies acceptance/rejection. These sources motivate the classification only; no external profitability result is imported.

Sources:
- https://pmc.ncbi.nlm.nih.gov/articles/PMC10017064/
- https://www.tradefirm.in/blogs/gap-up-gap-down-index-plan
- https://doi.org/10.1002/9781119202622.ch20

## Frozen feature construction

For current date t:
- Prior completed session high = prior 15:10 high.
- Prior completed session low = prior 15:10 low.
- Prior completed session close = prior 15:10 close.
- Current 09:15 opening location:
  - ABOVE_RANGE if open > prior high.
  - BELOW_RANGE if open < prior low.
  - INSIDE_RANGE if prior low <= open <= prior high.
- Current opening gap direction = sign(current 09:15 open / prior 15:10 close - 1).
- Exactly zero opening gap = NO_TRADE.
- No magnitude threshold is used.
- All state inputs are known before the current session begins.

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

3 location states × 2 gap mappings × 2 exits = 12 true cells.

Five fixed state-permutation null seeds 101/202/303/404/505. Only the prior-only location labels are permuted across eligible dates; same-day gap direction and execution prices stay unchanged.

## Data gates

- >=95% feature eligibility.
- >=95% deterministic expiry mapping.
- Zero prior-information violations.
- >=95% execution coverage in every true cell.
- Full Base/Stress accounting reconciliation.

## Promotion gate

Both Base and Stress must meet:
- mean weekly net >= ₹5,000;
- median weekly net >= ₹5,000;
- positive-week rate >=70%;
- execution coverage >=95%;
- clean accounting.

No WFA/OOS unless a frozen true cell clears the complete gate in both friction regimes.

## Stop rule

No post-result modification to location definitions, gap direction, execution, spread width, expiry, costs or slippage.
