# Phase 56 Status

**State: PREREGISTERED / ENGINEERING BUILD**

Branch: phase-56-same-session-atm-term-slope-opening-v1

Frozen feature:
- 09:30 ATM IV of nearest strict-next expiry minus 09:30 ATM IV of second strict-next expiry
- same ₹50 ATM strike
- last 60 valid same-session term-slope observations
- LOW/MID/HIGH empirical terciles

Frozen execution:
- 09:31 entry
- 10:30 / 15:10 exits
- one-lot 200-point ATM debit spread
- nearest expiry on/after current date for execution
- historical lots
- Base/Stress ₹0.20/₹0.40 slippage
- existing Paytm Money/NSE/statutory charges

No numerical result is accepted until tests, two-expiry feature coverage, null controls, execution coverage and accounting pass.
