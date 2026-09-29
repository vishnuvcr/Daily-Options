# Phase 53 Status

**State: PREREGISTERED / ENGINEERING BUILD**

Branch: phase-53-near-atm-iv-skew-gap-v1

Frozen feature:
- 09:30 one-strike near-ATM put IV minus one-strike near-ATM call IV
- LOW/MID/HIGH by the last 60 valid same-session skew observations

Frozen execution:
- 09:31 entry
- 10:30 / 15:10 exits
- one-lot 200-point ATM debit spread
- nearest expiry on/after trade date
- historical lots
- Base/Stress ₹0.20/₹0.40 slippage
- existing Paytm Money/NSE/statutory charges

No numerical result is accepted until tests, data gate, execution coverage, null controls and accounting all pass.
