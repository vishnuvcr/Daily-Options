# Phase 30.7 — Bear Put weekly numerical research

## Research question
Do any source-faithful interpretations of the Equity Income Bear Put spread generate a consistent, cost-adjusted weekly net result of at least ₹5,000 under both Base and Stress friction?

## Source-interpretation boundary
Phase 30.3 full-transcript review resolved the spread structure and adjustment narrative but did not resolve a mathematical resistance rule, exact trigger threshold, stop-loss, or fixed target. Phase 30.6 therefore registered 54 explicit resistance/crack/gap-down interpretations and found 45 with signals in at least 20 of the 53 weeks in the registered Sep-2025→Aug-2026 window.

Only those **45 feasibility-eligible definitions** advance. This is a feasibility filter, not a performance winner selection.

## Frozen numerical grid
For each eligible signal definition:
- Long-put construction: **ATM** or **one strike OTM**.
- Vertical width: **50 points** or **100 points**.
- Gap-up adjustment threshold: **+200 points** or **+300 points** above prior-session close, and above the source-defined resistance.
- Expiry: **nearest weekly NIFTY expiry on/after the signal date**, using the current Tuesday weekly-expiry framework. NSE states NIFTY weekly options expire Tuesday and current weekly/monthly strike interval is 50 points. citeturn535028search0turn535028search2
- Adjustment waiting convention: **60 minutes after the next trading session opens**. This is a pre-registered operational interpretation of the source's "do not rush" instruction; it is not selected from P&L.
- If, at the 60-minute check, the market remains above resistance after the qualifying gap-up, add **one additional short put at the original short strike**.
- If the market subsequently closes back below resistance, close only that additional short put on the next available minute-open; the original bear-put spread remains.
- Otherwise close all remaining legs at **15:15 IST on the weekly expiry day**, avoiding expiry settlement.
- No independent hard stop or profit target is invented. The base bear-put vertical has defined debit risk; the additional naked short creates extra downside exposure, which is reported separately rather than converted into an invented broker-margin figure.

This gives **45 × 2 × 2 × 2 = 360 frozen cells** per friction regime.

## Execution conventions
- Signal detection uses only spot bars strictly before the signal minute.
- One position per signal definition per weekly expiry: the first qualifying signal for that expiry is used; later signals for the same expiry are ignored.
- Entry is one minute after the signal, at the exact next-minute option open.
- Adjustment uses the next trading day's spot open and the 60-minute persistence test; the added short is executed one minute after the check.
- Reversal exit for the added short is one minute after the first subsequent spot close below resistance.
- Missing required option bars mean no-trade / incomplete execution; no forward-fill is permitted for execution prices.
- All historical lot sizes use the registered dated schedule: 75 through 2025-12-30 and 65 from 2026-01-06.
- Brokerage: ₹10 per executed order.
- Base slippage: 0.20 premium points per option per side.
- Stress slippage: 0.40 premium points per option per side.
- Exchange, SEBI, STT, stamp duty and GST follow the same date-aware cost model already audited in Phase 30.2.

## Promotion gate
A cell is promoted only if it satisfies all:
1. mean weekly net >= ₹5,000;
2. median weekly net >= ₹5,000;
3. profitable-week rate >=70%;
4. >=20 completed weeks;
5. execution coverage >=80%.

No post-result tuning is allowed inside Phase 30.7.

## Capital reporting
Report:
- initial debit cash per trade;
- average initial debit capital;
- maximum initial debit capital;
- conservative adjusted-position theoretical loss at NIFTY=0 before/after costs.

Actual broker SPAN/exposure margin for the extra naked short is **not** substituted with a guessed value.

## Advancement
- If zero cells pass the gate in Base or Stress: retire this Bear Put interpretation family and proceed to the next distinct source candidate.
- If cells pass: run Phase 30.8 nested walk-forward / later-period OOS on the preregistered passing set only.
- Phase 30.8 is the terminal validation phase for this candidate; no additional in-sample tuning is planned after it.
