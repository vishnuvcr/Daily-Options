# Phase 34 — Multi-Expiry Volatility Term Structure

## Status
**PREREGISTERED — numerical testing not yet started.**

## Research question
Does an extreme prior-session NIFTY implied-volatility term-structure inversion between the nearest and second-nearest expiries predict short-horizon mean reversion strongly enough for a defined-risk double-calendar structure to generate ₹5,000 net per completed trading week after Base/Stress costs?

## Aims
1. Measure front-minus-back implied volatility at fixed ATM and wing strikes.
2. Test whether unusually rich near-term volatility mean-reverts over the next trading session.
3. Monetize only through a long-back/short-front double calendar, retaining bounded calendar risk.
4. Quantify brokerage, statutory charges, slippage and execution coverage.
5. Compare signal timing with five complete-panel null permutations.

## Frozen information timing
- Underlying: NIFTY 50.
- Study window: 2021-07-01 through 2026-08-31, subject to pinned-cache coverage.
- Signal observation: exact last available NIFTY index observation of prior trading session.
- Option observation: the latest option bar on or before that exact NIFTY index timestamp.
- Front expiry: nearest NIFTY expiry strictly after the signal date.
- Back expiry: second-nearest NIFTY expiry strictly after the signal date.
- No current-session IV/OI/volume may enter the signal.
- Entry: next trading session 09:31 IST.
- Exits: 10:30 and 15:10 IST.

## Surface definitions

At the prior-session cutoff calculate Black-Scholes IV using r=0 and q=0.

1. **ATM_TERM_SPREAD = IV_front_ATM_avg - IV_back_ATM_avg**, where ATM_avg is the average of CE and PE at the nearest ₹50-rounded ATM strike.

2. **WING_TERM_SPREAD = mean(IV_front_ATM-100_PE, IV_front_ATM+100_CE) - mean(IV_back_ATM-100_PE, IV_back_ATM+100_CE).**

Each raw feature is standardized using only the previous 60 completed signal-session observations of the same raw feature.

## Frozen trading hypothesis

The preregistered economic hypothesis is **one-sided mean reversion of near-term richness**.

A trade is generated only when:
- feature z >= threshold;
- all required front/back quotes are valid;
- the double-calendar opens at a positive net debit.

Position:
- SELL front CE at ATM
- BUY back CE at ATM
- SELL front PE at ATM
- BUY back PE at ATM

One NIFTY lot.

This is a long-back / short-front double calendar. It is deliberately not reversed for negative z-scores, because a reverse calendar would change the risk profile and is outside this preregistered family.

The trade is skipped when the initial calendar value is zero/negative, because the experiment is specifically a debit calendar and does not admit a post-result credit variant.

No adjustments, rolls, stops, targets, leverage changes or strike retuning.

## Frozen discovery grid

- Features: ATM_TERM_Z, WING_TERM_Z
- Thresholds: z >= 0.75 and z >= 1.25
- Exits: 10:30 and 15:10
- True cells: 2 × 2 × 2 = **8**
- Null seeds: **101, 202, 303, 404, 505**
- Base slippage: ₹0.20 per option-price unit per order
- Stress slippage: ₹0.40 per option-price unit per order
- Existing date-aware NIFTY lot-size and Paytm Money/NSE/statutory charge model
- Four entry orders + four exit orders per double-calendar

## Data gates

1. Prior-session front and back expiry availability >=95%.
2. All required front/back ATM and ±100 wing quote/IV inputs >=95% complete for warm-up-complete sessions.
3. Feature-wise non-null coverage >=95% after the prior-only 60-session warm-up.
4. Prior-information barrier violations = 0.
5. Calendar entry and exit quote coverage >=95% for every true cell.
6. Positive-debit calendar coverage is recorded separately; no credit calendar is substituted.

## Promotion gate

In both Base and Stress:
- mean weekly net >= ₹5,000;
- median weekly net >= ₹5,000;
- positive-week rate >=70%;
- execution coverage >=95%;
- no unresolved data-quality violation;
- true-cell result must not be inferior to its matched null-control family.

No WFA/OOS before this gate.

## Statistical analysis
Report:
- trade count, active weeks;
- total, mean, median and percentile weekly net;
- positive-week rate;
- expectancy and profit factor;
- maximum drawdown and ulcer index;
- raw calendar gross P&L;
- brokerage/statutory charges;
- slippage;
- 1,000-draw weekly bootstrap interval;
- true-vs-null differences;
- yearly and volatility-regime breakdowns;
- signal concentration and missingness;
- sensitivity to Base/Stress friction.

## Stop rule
If the data gate fails, close Phase 34 as DATA-LIMITED. If the data gate passes and all 8 cells fail the economic gate, close as negative discovery. No post-result strike/expiry/credit/calendar-direction tuning.

## Deliverables
Preregistration, literature review, source manifest, engine, unit tests, manual workflow, gate artifacts, Base/Stress trade ledgers, null controls, figures, final manuscript and reproducibility appendix.
