# Phase 51 Status

**State: PREREGISTERED / ENGINEERING BUILD**

Branch: phase-51-prior-atm-iv-regime-gap-v1

Frozen feature:
- prior-session ATM CE/PE IV average
- nearest expiry strictly after prior session date
- last 60 valid prior-session ATM IV observations
- LOW/MID/HIGH empirical terciles

Frozen execution:
- 09:31 entry
- 10:30 / 15:10 exits
- one-lot 200-point ATM debit spread
- nearest expiry on/after trade date
- historical lots
- Base/Stress ₹0.20/₹0.40 slippage
- existing Paytm Money/NSE/statutory charges

No result is accepted until unit tests, IV data gates, execution coverage, null controls and accounting all pass.
