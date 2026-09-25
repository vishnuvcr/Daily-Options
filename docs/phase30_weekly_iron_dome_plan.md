# Phase 30 — Weekly NIFTY Iron Dome numerical backtest

## Objective

Run the frozen 12-cell Iron Dome formalization from Phase 29.5 on the pinned TradeMarkk NIFTY exact-expiry 1-minute dataset, with date-aware NIFTY lot sizes, Paytm Money/NSE charges and Base/Stress execution friction.

This is the first numerical P&L phase for the Equity Income weekly program.

## Frozen strategy definition

From Phase 29.5:
- NIFTY weekly Iron Fly / Iron Dome.
- Entry candidates: T-4, T-3, T-2 trading sessions before the Tuesday expiry.
- Entry clock: 09:30; option fills use the next minute's open.
- Initial center: one 50-point strike above ATM (source-anchored bearish formalization).
- Four legs, 1:1:1:1:
  - sell CE at center;
  - sell PE at center;
  - buy CE at center + 200;
  - buy PE at center - 200.
- Maximum two adjustments.
- Exit signal: 15:00 on expiry day; fill at the next minute open where available, otherwise the latest available mark.
- No discretionary profit target.
- No discretionary stop-loss outside the registered 60% trigger.

## Trigger formalizations

A. WING_60:
- trigger when NIFTY spot closes at least 120 points from the current short-strike center in the challenged direction;
- trigger is evaluated on 1-minute closes;
- fill occurs on the following minute.

B. RISK_60:
- trigger when mark-to-market loss since the most recent completed adjustment reaches 60% of that position's registered defined maximum-loss budget;
- the loss threshold baseline is reset after each completed adjustment;
- adjustment direction is chosen from the sign of the current NIFTY displacement from the current short-strike center.

## Adjustment formalizations

A. RECENTER_BOTH:
- close all open Iron Fly legs at the trigger's next-minute open;
- choose a new short-straddle center as the nearest 50-point strike to the trigger-time NIFTY spot;
- rebuild a 200-point 1:1:1:1 Iron Fly around that new center;
- all old legs are closed; no leg is left unintentionally naked.

B. ONE_STRIKE_INSIDE:
- on an upward challenge, roll the short CE and its long CE wing up by one 50-point strike;
- on a downward challenge, roll the short PE and its long PE wing down by one 50-point strike;
- the opposite side remains unchanged;
- the moved protective wing remains 200 points from its moved short leg.

## Execution model

Order-level simulation, no artificial bid/ask:
- buy fills = next-minute open + slippage;
- sell fills = next-minute open - slippage;
- Base slippage = ₹0.20 per option premium point per leg/order;
- Stress slippage = ₹0.40.

Costs:
- Paytm Money brokerage = ₹20 per executed order.
- NSE option-sale STT = 0.10% before 2026-04-01 and 0.15% from 2026-04-01.
- NSE option-premium turnover/IPFT rate = 0.03503% before 2026-03-01 and 0.0355299% from 2026-03-01 in the research cost model.
- SEBI turnover fee = 0.0001%.
- Stamp duty = 0.003% on option purchases.
- GST = 18% of brokerage + exchange + SEBI charges.
- Lot size is date-specific: NIFTY 50 before 2021-07-01, 50 until 2024-04-25, 25 from 2024-04-26 to 2024-11-20, 75 through 2026-01-05, 65 from 2026-01-06.
- All execution and cost inputs are logged per order.

## Statistical outputs

For every cell and friction model:
- traded weeks;
- total net P&L;
- mean weekly net;
- median weekly net;
- profitable-week rate;
- percentage of weeks at or above ₹5,000;
- worst week;
- max drawdown;
- profit factor;
- 95% CVaR / expected shortfall;
- total orders and average orders per week.

## Preliminary weekly target gate

A cell is TARGET_QUALIFIED only when all are true:
- at least 100 traded weeks;
- Base mean weekly net >= ₹5,000;
- Stress mean weekly net >= ₹5,000;
- Base median weekly net >= ₹5,000;
- Stress median weekly net >= ₹5,000;
- Base and Stress both have at least 75% of traded weeks >= ₹5,000.

No ranking or parameter tuning is performed inside this phase. The gate is evaluated after all 12 preregistered cells have completed.

## Data integrity gates

Before any P&L is accepted:
- pinned TradeMarkk revision 51ca58c;
- actual expiry file is selected, not inferred from weekly labels;
- entry/adjustment/exit dates are taken from the pinned NIFTY trading calendar;
- all required option legs must exist at every executed fill;
- the next-minute fill must be present unless the registered final-exit fallback is used;
- no future row is used to select a strike or trigger;
- no OHLC value is represented as a bid/ask quote.

## Decision path

- If one or more cells clear the preliminary gate in both Base and Stress: freeze them unchanged and move to Phase 31 regime robustness, then WFA/OOS.
- If no cell clears the gate: this exact Iron Dome family is not promoted. A separate source-derived Equity Income family may be tested; no result-driven tuning of these 12 cells is allowed.
