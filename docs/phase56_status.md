# Phase 56 Status

**State: PREREGISTERED / ENGINEERING BUILD**

Branch: phase-56-candle-conviction-gap-v1

Frozen feature:
- prior-session candle body / prior high-low range
- 60 valid strictly prior observations
- LOW/MID/HIGH conviction terciles
- prior candle direction stored descriptively only

Frozen execution:
- 09:31 entry
- 10:30 / 15:10 exits
- one-lot 200-point ATM debit spread
- nearest expiry on/after trade date
- historical lots
- Base/Stress ₹0.20/₹0.40 slippage
- existing Paytm Money/NSE/statutory charges

No numerical result is accepted until unit tests, data gates, null controls, execution coverage and accounting all pass.
