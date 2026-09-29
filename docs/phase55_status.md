# Phase 55 Status

**State: PREREGISTERED / ENGINEERING BUILD**

Branch: phase-55-same-session-smile-curvature-opening-v1

Frozen feature:
- 09:30 average of ATM−₹50 PE IV and ATM+₹50 CE IV
- minus 09:30 average of ATM CE/PE IV
- nearest strict-next expiry
- last 60 valid prior-day same-session curvature observations
- LOW/MID/HIGH empirical terciles

Frozen execution:
- 09:31 entry
- 10:30 / 15:10 exits
- one-lot 200-point ATM debit spread
- nearest expiry on/after current date
- historical lots
- Base/Stress ₹0.20/₹0.40 slippage
- existing Paytm Money/NSE/statutory charges

No numerical result is accepted until tests, feature coverage, null controls, execution coverage and accounting pass.
