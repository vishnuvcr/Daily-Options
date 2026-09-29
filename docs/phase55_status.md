# Phase 55 Status

**State: PREREGISTERED / ENGINEERING BUILD**

Branch: phase-55-current-atm-iv-term-structure-gap-v1

Frozen feature:
- 09:30 front/back expiry ATM IV slope
- STEEP_TERM / INVERTED_TERM by sign only
- front expiry nearest on/after trade date
- back expiry next listed expiry
- current-session information barrier at 09:30

Frozen execution:
- 09:31 entry
- 10:30 / 15:10 exits
- one-lot 200-point ATM debit spread
- historical lots
- Base/Stress ₹0.20/₹0.40 slippage
- existing Paytm Money/NSE/statutory charges

No numerical result is accepted until unit tests, feature gates, null controls, execution coverage and accounting all pass.
