# Phase 54 Status

**State: PREREGISTERED / ENGINEERING BUILD**

Branch: phase-54-same-session-atm-iv-spread-opening-v1

Frozen feature:
- 09:30 matched ATM CE IV minus ATM PE IV
- nearest expiry strictly after current date for feature construction
- last 60 valid same-session spread observations
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
