# Phase 42 — NIFTY Option Day–Night Return Asymmetry × Opening-Gap Direction

## Research question
Does the prior completed NIFTY session's ATM option day–night return asymmetry condition whether the next session's opening gap continues or reverses strongly enough to generate at least ₹5,000 net per completed trading week after realistic costs?

## Literature basis
Bhat, Pandey & Nageswara Rao (Journal of Futures Markets, 2024) document day–night asymmetry in NIFTY option returns: positive overnight option returns accompanied by negative intraday returns, with weaker asymmetry on large underlying-jump days. The paper's cited public dataset covers NIFTY one-minute spot/futures/options data from 2017–2020. The literature result is treated as a motivation, not as evidence that the proposed trading rule is profitable. A broader US index-options study also documents day/night option-return asymmetry and emphasizes implementation costs.

## Frozen feature
For each completed prior signal session p:
1. Select the nearest NIFTY expiry strictly after p.
2. Select ATM as the deterministic nearest ₹50 strike to p's 15:10 NIFTY close.
3. Construct the ATM straddle price as CE close + PE close at that same strike/expiry.
4. Overnight straddle return = p 09:15 straddle / previous completed session 15:10 straddle − 1.
5. Intraday straddle return = p 15:10 straddle / p 09:15 straddle − 1.
6. DAY_NIGHT_ASYMMETRY = intraday straddle return − overnight straddle return.
7. Standardize only with the strictly prior 60 valid DAY_NIGHT_ASYMMETRY observations.
8. HIGH_ASYMMETRY if z >= +0.75; LOW_ASYMMETRY if z <= −0.75; otherwise no trade.

## Execution
- Current-session gap: 09:15 open / prior-session 15:10 close − 1.
- Zero gap: no trade.
- FOLLOW_GAP and FADE_GAP.
- Entry: 09:31 option open.
- Exits: 10:30 and 15:10 option close.
- One-lot 200-point ATM directional debit spread.
- Current nearest NIFTY expiry on/after trade date.
- Historical NIFTY lot sizes.
- Existing Paytm Money/NSE/statutory transaction-cost model.
- Base slippage ₹0.20 and Stress slippage ₹0.40 per option-price unit/order.

## Discovery
2 asymmetry states × 2 gap mappings × 2 exits = 8 true cells.
Five fixed full-panel permutation null seeds: 101, 202, 303, 404, 505. Nulls permute only prior-session asymmetry z-scores across eligible dates.

## Data gates
- >=95% post-warm-up feature eligibility;
- >=95% input coverage for the three required prior-session option snapshots;
- zero prior-information violations;
- deterministic expiry/strike/lot mapping;
- >=95% execution quote coverage in every true cell;
- accounting reconciliation.

## Promotion gate
Both Base and Stress must have mean weekly net >=₹5,000, median weekly net >=₹5,000, positive-week rate >=70%, >=95% execution coverage and clean accounting.

## WFA/OOS
No WFA/OOS unless both Base and Stress discovery promotion gates pass.

## Stop rule
No post-result change to the 60-observation window, ±0.75 thresholds, straddle definition, expiry rule, ATM rule, gap mapping, entry, exits, spread width, lot sizing or cost/slippage model.
