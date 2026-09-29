# Phase 51 — Prior-Session ATM IV Level Regime × Opening-Gap Direction

## Research question

Does the level of NIFTY's prior-session ATM implied volatility condition whether the next session's opening gap continues or reverses strongly enough to generate economically meaningful weekly net P&L after realistic option-trading costs?

## Literature rationale

Academic work finds that implied-volatility dynamics and time-varying volatility risk premia contain information about subsequent asset and option returns. Carr and Wu develop volatility-risk-premium measures from option-implied and expected/realized volatility and find predictive information for future returns; Bollerslev, Gibson and Zhou document time variation in volatility risk premia and predictive content for future stock returns. Research on index-option IV term structure also finds predictive information for future short-dated implied volatility.

These studies motivate testing the **absolute level of prior-session ATM IV** as a market state. They do not establish NIFTY after-cost profitability and are not used to choose a winning state.

Sources:
- https://www.sciencedirect.com/science/article/pii/S0304405X16000052
- https://www.sciencedirect.com/science/article/pii/S0304407610000758
- https://www.sciencedirect.com/science/article/pii/S0927539806000715
- https://www.sciencedirect.com/science/article/pii/S0165188917301434

## Frozen feature construction

For trading date t:

1. Prior completed NIFTY session = immediately preceding available 15:10 session.
2. Prior-session spot = prior session 15:10 NIFTY close.
3. Prior ATM strike = nearest ₹50 strike using deterministic half-up rounding.
4. Reference expiry = nearest NIFTY expiry **strictly after** the prior session date.
5. At prior-session 15:10, obtain ATM CE and ATM PE closes from that expiry.
6. Invert each premium to Black-Scholes implied volatility using prior-session spot, strike and time-to-expiry.
7. Prior ATM IV = simple mean of valid CE and PE IV, expressed in volatility percentage points.
8. For trading date t, classify the prior-session ATM IV using the last **60 valid prior-session ATM IV observations strictly before the prior session**:
   - LOW_IV: below 33.333rd empirical percentile
   - MID_IV: 33.333rd to below 66.667th percentile
   - HIGH_IV: at or above 66.667th percentile
9. Current opening gap direction = sign(current 09:15 NIFTY open / prior 15:10 close − 1).
10. Zero opening gap = NO_TRADE.

No current-day option IV, realized return after the opening, or future information enters the state.

## Frozen execution

- FOLLOW_GAP and FADE_GAP.
- Entry 09:31 IST option open.
- Exits 10:30 and 15:10 IST option close.
- One-lot 200-point ATM directional debit spread.
- ATM = nearest ₹50 strike to 09:30 NIFTY close.
- Nearest NIFTY expiry on/after the current trade date for execution.
- Historical NIFTY lot sizes.
- Existing Paytm Money/NSE/statutory charges.
- Base slippage ₹0.20; Stress ₹0.40 per option-price unit/order.

## Discovery matrix and controls

3 IV states × 2 gap mappings × 2 exits = 12 true cells.

Five fixed state-permutation null seeds: 101/202/303/404/505. Nulls permute only the prior-session IV-regime labels across feature-eligible dates while preserving current-session gap direction and all execution prices.

## Data gates

- ≥95% post-warm-up feature eligibility.
- ≥95% valid ATM IV CE/PE coverage among required prior sessions.
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

No WFA/OOS is authorized unless at least one frozen true cell clears the full gate in both friction regimes.

## Statistical analysis

Primary:
- weekly mean/median net;
- positive-week rate;
- total net P&L;
- maximum drawdown and worst trade;
- execution coverage;
- Base-to-Stress degradation.

Secondary:
- IV state differences;
- FOLLOW versus FADE;
- matched permutation-null comparison;
- annual descriptive stability.

## Stop rule

No post-result change to the 60-valid-observation lookback, percentile boundaries, ATM-IV construction, expiry rule, gap mapping, entry, exits, spread width, or friction model.
