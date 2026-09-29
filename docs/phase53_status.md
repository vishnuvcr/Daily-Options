# Phase 53 Status

**State: PREREGISTERED / ENGINEERING BUILD**

Branch: phase-53-near-atm-iv-skew-opening-v1

Frozen feature:
- 09:30 IV of one OTM put at ATM-₹100 minus one OTM call at ATM+₹100
- nearest expiry strictly after the current date
- prior 60 valid same-session skew observations
- LOW/MID/HIGH empirical terciles

Frozen execution:
- 09:31 entry
- 10:30 / 15:10 exits
- one-lot 200-point ATM debit spread
- nearest expiry on/after trade date for execution
- historical lots
- Base/Stress ₹0.20/₹0.40 slippage
- existing Paytm Money/NSE/statutory charges

No numerical result is accepted until unit tests, feature gates, null controls, execution coverage and accounting all pass.
