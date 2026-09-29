# Phase 55 Status

**State: PREREGISTERED / ENGINEERING BUILD**

Branch: phase-55-iv-curvature-opening-v1

Frozen feature:
- 09:30 ATM IV
- 09:30 OTM put IV at ATM-₹100
- 09:30 OTM call IV at ATM+₹100
- curvature = average wing IV − ATM IV
- prior 60 valid curvature observations
- LOW/MID/HIGH empirical terciles

Frozen execution:
- 09:31 entry
- 10:30 / 15:10 exits
- one-lot 200-point ATM debit spread
- nearest expiry on/after trade date
- historical lots
- Base/Stress ₹0.20/₹0.40 slippage
- existing Paytm Money/NSE/statutory charges

No numerical result is accepted until unit tests, feature gates, null controls, execution coverage and accounting all pass.
