# Phase 52 — Same-Session 09:30 ATM IV Level Regime × Opening-Gap Direction

## Research question

Does the NIFTY ATM implied-volatility level observed at 09:30 on the current session condition whether the opening gap continues or reverses strongly enough to generate at least ₹5,000 net per completed trading week after realistic option-trading costs?

## Motivation

Phase 51 tested prior-session ATM IV but was DATA-LIMITED because valid prior-session ATM IV coverage was 94.01%. Phase 52 deliberately changes only the information timing: the IV state is measured from the current session's 09:30 ATM CE/PE closes, and the trade is entered at 09:31. This is valid because the state is available before the registered execution timestamp.

The state is still normalized against a strictly prior 60-valid-observation distribution. No same-day information after 09:30 enters the signal.

## Frozen feature construction

For trading date t:

1. Current 09:30 NIFTY close is the reference spot.
2. ATM strike = nearest ₹50 using deterministic half-up rounding.
3. Execution/reference expiry = nearest NIFTY expiry on or after trading date t.
4. Obtain 09:30 ATM CE and PE closes for that expiry.
5. Invert each premium to Black-Scholes implied volatility using the 09:30 spot, strike and time-to-expiry.
6. Same-session ATM IV = simple mean of valid CE and PE IV, expressed in percentage points.
7. State thresholds use the last 60 valid same-session ATM IV observations from dates strictly before t:
   - LOW_IV: below 33.333rd empirical percentile
   - MID_IV: 33.333rd to below 66.667th percentile
   - HIGH_IV: at or above 66.667th percentile
8. Opening-gap direction = sign(09:15 NIFTY open / prior 15:10 close − 1).
9. Zero opening gap = NO_TRADE.

No 09:31 or later price, option premium, or future information is used to create the state.

## Frozen execution

- FOLLOW_GAP and FADE_GAP.
- Entry: 09:31 IST option open.
- Exits: 10:30 and 15:10 IST option close.
- One-lot 200-point ATM directional debit spread.
- ATM for execution = 09:30 NIFTY close.
- Nearest NIFTY expiry on/after current trade date.
- Historical NIFTY lot sizes.
- Existing Paytm Money/NSE/statutory charges.
- Base slippage ₹0.20 and Stress ₹0.40 per option-price unit/order.

## Discovery matrix and controls

3 IV states × 2 gap mappings × 2 exits = 12 true cells.

Five fixed state-permutation null seeds: 101, 202, 303, 404, 505. Nulls permute only the prior-only regime labels across eligible dates, while same-day gap direction and execution prices remain unchanged.

## Data gates

- ≥95% post-warm-up feature eligibility.
- ≥95% valid same-session ATM IV CE/PE coverage.
- ≥95% deterministic expiry mapping.
- Zero prior-information violations.
- ≥95% execution coverage in every true cell.
- Full Base/Stress accounting reconciliation.

## Promotion gate

In both Base and Stress:
- mean weekly net ≥₹5,000;
- median weekly net ≥₹5,000;
- positive-week rate ≥70%;
- execution coverage ≥95%;
- clean accounting.

No WFA/OOS unless at least one frozen true cell clears the full gate in both friction regimes.

## Statistical analysis

Primary:
- weekly mean/median net;
- positive-week rate;
- total net P&L;
- max drawdown and worst trade/week;
- execution coverage;
- Base-to-Stress degradation.

Secondary:
- LOW/MID/HIGH IV differences;
- FOLLOW versus FADE;
- matched permutation-null comparison;
- calendar-year descriptive stability;
- feature eligibility by expiry and year.

## Stop rule

No post-result change to the 60-valid-observation lookback, percentile boundaries, same-session IV construction, expiry rule, gap mapping, entry, exits, spread width, or cost model.
