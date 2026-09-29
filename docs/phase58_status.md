# Phase 58 Status

**State: PREREGISTERED / ENGINEERING BUILD**

Branch: phase-58-atm-volume-imbalance-gap-v1

Frozen feature:
- 09:15–09:29 ATM CE and PE volume sums
- feature expiry = nearest strict-next expiry
- volume imbalance = (CE volume − PE volume)/(CE volume + PE volume)
- prior 60 valid imbalance observations
- LOW/MID/HIGH empirical terciles

Frozen execution:
- 09:31 entry
- 10:30 / 15:10 exits
- one-lot 200-point ATM debit spread
- nearest expiry on/after trade date
- historical lots
- Base/Stress ₹0.20/₹0.40 slippage
- existing Paytm Money/NSE/statutory charges

No numerical result is accepted until unit tests, volume completeness gate, null controls, execution coverage and accounting all pass.
