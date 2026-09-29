# Phase 53 — Same-Session 09:30 Near-ATM IV Skew × Opening Direction

## Research question

Does the contemporaneous 09:30 NIFTY near-ATM implied-volatility skew condition whether the current opening gap continues or reverses strongly enough to generate at least ₹5,000 net per completed trading week after realistic option-trading costs?

## Literature rationale

Option-implied volatility skew contains information about the relative pricing of downside and upside tails. Research on index-option skew and volatility risk premia motivates using skew as a state variable rather than absolute IV level alone.

The current research frontier deliberately uses a simple near-ATM skew measure rather than reopening the already-tested full smile/dislocation family.

Sources:
- https://www.sciencedirect.com/science/article/pii/S0304405X16000052
- https://www.sciencedirect.com/science/article/pii/S0304407610000758
- https://www.sciencedirect.com/science/article/pii/S0165188917301434
- https://www.sciencedirect.com/science/article/pii/S1062940820300747

## Frozen feature construction

For trading date t:

1. Current 09:30 NIFTY close is the reference spot.
2. ATM strike = nearest ₹50 using deterministic half-up rounding.
3. Near-ATM put strike = ATM − ₹50.
4. Near-ATM call strike = ATM + ₹50.
5. Reference expiry = nearest NIFTY expiry on or after current trade date t.
6. Obtain 09:30 closes for the near-ATM put and near-ATM call.
7. Invert both premiums to Black-Scholes implied volatility using the 09:30 spot, corresponding strike and time-to-expiry.
8. RAW_SKEW = put IV − call IV, measured in volatility percentage points.
9. Build the state distribution from the last 60 valid RAW_SKEW observations from dates strictly before t:
   - LOW_SKEW: below 33.333rd empirical percentile
   - MID_SKEW: 33.333rd to below 66.667th percentile
   - HIGH_SKEW: at or above 66.667th percentile
10. Opening-gap direction = sign(09:15 NIFTY open / prior 15:10 close − 1).
11. Zero opening gap = NO_TRADE.

The skew state is fully known by 09:30 and the registered execution is 09:31. No 09:31+ information enters the state.

## Frozen execution

- FOLLOW_GAP and FADE_GAP.
- Entry: 09:31 IST option open.
- Exits: 10:30 and 15:10 IST option close.
- One-lot 200-point ATM directional debit spread.
- Execution ATM = 09:30 NIFTY close.
- Nearest NIFTY expiry on/after current trade date.
- Historical NIFTY lot sizes.
- Existing Paytm Money/NSE/statutory charges.
- Base slippage ₹0.20 and Stress ₹0.40 per option-price unit/order.

## Discovery matrix and controls

3 skew states × 2 gap mappings × 2 exits = 12 true cells.

Five fixed state-permutation null seeds: 101, 202, 303, 404, 505. Nulls permute only the prior-only skew-regime labels across eligible dates while preserving current-session gap direction and all execution prices.

## Data gates

- ≥95% post-warm-up feature eligibility.
- ≥95% valid near-ATM put/call IV coverage.
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
- maximum drawdown and worst trade/week;
- execution coverage;
- Base-to-Stress degradation.

Secondary:
- LOW/MID/HIGH skew differences;
- FOLLOW versus FADE;
- matched permutation-null comparison;
- calendar-year descriptive stability.

## Stop rule

No post-result change to the 60-valid-observation lookback, percentile boundaries, skew definition, near-ATM strike offsets, expiry rule, gap mapping, entry, exits, spread width or cost model.
