# Phase 35 — Global Overnight Shock × India-Local Volatility State

## Status
CLOSED DATA-LIMITED — authoritative run 36378249952.

The frozen gate failed because both LOW_VOL_STATE true cells had 0% execution quote coverage (1 candidate day each). Per preregistration, no P&L is accepted and no retuning is permitted.

## Research question
Does a large prior-session global equity shock become more or less monetizable in NIFTY depending on the prior-day India-local implied-volatility state, after realistic costs?

## Hypothesis
Global-return direction alone failed Phase 31.8. Phase 35 therefore tests an interaction: the same global shock may have different next-session option behavior when India-local volatility is unusually low or high.

This is not a retuning of Phase 31.8. The global shock threshold, local-volatility state and option structure are independently frozen before results.

## Frozen signal variables

### Global shock
Use the Phase 31.8 six-index GLOBAL_LEAD construction and strict prior-date barrier.

Trigger:
- absolute GLOBAL_LEAD z >= 1.0

Direction:
- positive GLOBAL_LEAD -> bullish structure
- negative GLOBAL_LEAD -> bearish structure

### India-local volatility state
Use prior-session NIFTY ATM implied volatility and 20-session realized volatility, both measured strictly before the trade date.

Define:
- IV_RV_GAP = ATM IV (annualized %) minus 20-session realized volatility (%).
- IV_RV_Z = prior-only 60-session standardized IV_RV_GAP.

Two frozen states:
- LOW_VOL_STATE: IV_RV_Z <= -0.75
- HIGH_VOL_STATE: IV_RV_Z >= +0.75

Neutral days are no-trade.

## Frozen option structures

The family deliberately tests the interaction with two defined-risk structures:

1. LOW_VOL_STATE:
   - directional 200-point debit spread in the GLOBAL_LEAD direction.

2. HIGH_VOL_STATE:
   - same-direction 200-point debit spread, but only when the global shock and high-vol state agree.

No credit structures, reverse direction, strike retuning, or post-result structure switching.

## Frozen grid

- Signal: |GLOBAL_LEAD| >= 1.0
- Local state: LOW_VOL_STATE / HIGH_VOL_STATE
- Exit: 10:30 / 15:10 IST
- Structure: one 200-point debit spread
- Total true cells: 4
- Null seeds: 101, 202, 303, 404, 505
- Nulls permute the complete GLOBAL_LEAD series before thresholding while leaving the local-vol state unchanged.

## Information barrier

For trade date t:
- global inputs must come from sessions strictly before t;
- prior-day NIFTY option IV must be measured at the latest option observation on or before the prior-session NIFTY close;
- 20-session realized volatility uses only prior completed NIFTY closes;
- the 60-session IV_RV standardization uses only observations earlier than the current signal;
- entry 09:31 option open;
- exit 10:30 or 15:10 option close.

## Data gate

Require:
- >=95% of feature-eligible sessions with both GLOBAL_LEAD and IV_RV_Z;
- zero prior-information violations;
- >=95% execution quote coverage in every true cell;
- sufficient option IV reconstruction coverage;
- deterministic expiry/strike/lot mapping.

If the gate fails, close DATA-LIMITED.

## Costs

Use the established date-aware NIFTY lot-size and Paytm Money/NSE/statutory charge model.

Base slippage: ₹0.20 per option-price unit/order.
Stress: ₹0.40.

Accounting must reconcile raw gross - slippage - transaction costs = net.

## Promotion gate

In both Base and Stress:
- mean weekly net >= ₹5,000;
- median weekly net >= ₹5,000;
- positive-week rate >=70%.

No WFA/OOS unless all four true cells are evaluated and at least one cell clears the frozen discovery gate.

## Stop rule

No post-result:
- threshold changes;
- additional volatility thresholds;
- alternative global indices;
- alternate IV lookbacks;
- structure switching;
- strike optimization.

If all cells fail, retire Phase 35 and move to the next materially distinct family.

## Deliverables

Plan, literature review, source manifest, implementation, tests, manual workflow, data gate, Base/Stress ledgers, null controls, accounting reconciliation, final manuscript, error log and main-status update.
