# Phase 57 — 09:15–09:30 Opening-Range Volatility Regime × Opening-Gap Direction

## Research question

Does the volatility/range of NIFTY's first 15-minute opening window condition whether the current opening gap continues or reverses strongly enough to produce at least ₹5,000 net per completed trading week after realistic costs?

## Literature rationale

Indian market research documents unusually high volatility and price discovery in the first 15–30 minutes after the open. Sampath and ArunKumar find elevated NIFTY volatility during the opening 30 minutes and a U-shaped intraday pattern. citeturn761831search1turn761831search10

NSE research on opening call auctions finds that a large fraction of price discovery still occurs in the first 15 minutes of continuous trading, supporting a preregistered opening-range state test. citeturn761831search2

International intraday-momentum research also reports that first-half-hour volatility conditions the predictability of later returns, while option-market studies show information arriving immediately after the open can have intraday implications. citeturn761831search8turn761831search3

These studies motivate the hypothesis only. They do not establish a profitable NIFTY options strategy after costs.

## Frozen feature construction

For current trading date t:

1. Opening-range window = NIFTY one-minute bars from **09:15:00 through 09:29:00 inclusive**. The 09:30 close is not used in the range feature.
2. Opening-range high = maximum high over those bars.
3. Opening-range low = minimum low over those bars.
4. Opening-range size = high − low.
5. **OPEN_RANGE_PCT = (opening-range high − opening-range low) / 09:15 open**.
6. Build a strictly prior empirical distribution from the last 60 valid OPEN_RANGE_PCT observations.
7. State:
   - LOW_OR_VOL: below empirical 33.333rd percentile.
   - MID_OR_VOL: 33.333rd to below 66.667th percentile.
   - HIGH_OR_VOL: at or above 66.667th percentile.
8. Opening direction = sign(current 09:15 open / prior completed 15:10 close − 1).
9. Zero opening gap = NO_TRADE.

All feature values are available before the 09:31 execution decision. No current-day information after 09:29 enters the volatility state.

## Frozen execution

- FOLLOW_OPEN and FADE_OPEN.
- Entry 09:31 IST option open.
- Exits 10:30 and 15:10 IST option close.
- One-lot 200-point ATM directional debit spread.
- ATM = nearest ₹50 strike to 09:30 NIFTY close.
- Execution expiry = nearest NIFTY expiry on/after current trading date.
- Historical NIFTY lot sizes.
- Existing Paytm Money/NSE/statutory charges.
- Base slippage ₹0.20; Stress ₹0.40 per option-price unit/order.

## Discovery matrix and controls

3 opening-range volatility states × 2 mappings × 2 exits = 12 true cells.

Five fixed state-permutation null seeds: 101/202/303/404/505. Nulls permute only the prior-only opening-range volatility state labels across feature-eligible dates; same-day opening direction and all execution prices remain unchanged.

## Data gates

- ≥95% post-warm-up feature eligibility.
- ≥95% opening-range OHLC completeness.
- ≥95% deterministic expiry mapping.
- Zero prior-information violations.
- ≥95% execution coverage in every true cell.
- Full Base/Stress accounting reconciliation.

## Promotion gate

Both Base and Stress:
- mean weekly net ≥ ₹5,000;
- median weekly net ≥ ₹5,000;
- positive-week rate ≥70%;
- execution coverage ≥95%;
- clean accounting.

No WFA/OOS unless at least one frozen true cell clears the full gate in both friction regimes.

## Stop rule

No post-result changes to opening-range window, range normalization, 60-session history, state boundaries, opening-direction mapping, entry, exits, spread width, expiry rule, or cost model.
