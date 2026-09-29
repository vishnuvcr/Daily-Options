# Phase 55 Status

**State: PREREGISTERED / ENGINEERING BUILD**

Branch: phase-55-front-next-expiry-atm-iv-term-structure-v1

Frozen feature:
- 09:30 front-expiry ATM IV versus next-expiry ATM IV
- TERM_SLOPE = back IV minus front IV
- STEEP_TERM >= 0; INVERTED_TERM < 0
- no post-result threshold selection

Frozen execution:
- 09:31 entry
- 10:30 / 15:10 exits
- one-lot 200-point ATM debit spread
- nearest expiry on/after current date
- historical lots
- Base/Stress ₹0.20/₹0.40 slippage
- existing Paytm Money/NSE/statutory charges

No numerical result is accepted until unit tests, feature gates, execution coverage, null controls and accounting all pass.
