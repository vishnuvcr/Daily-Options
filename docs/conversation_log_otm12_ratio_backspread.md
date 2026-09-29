# Conversation / Decision Log — OTM1 / 2xOTM2 Ratio Backspread

## 2026-09-29
User requested a separate-branch intraday NIFTY options backtest of:
- Sell 1 OTM1 PUT
- Buy 2 OTM2 PUTs
- Sell 1 OTM1 CALL
- Buy 2 OTM2 CALLs

Research goal: identify what is common among losing trades and what market circumstances are associated with profit, so a no-trade filter can later be tested.

Frozen interpretation:
- OTM1/OTM2 = first and second listed OTM strikes at the 09:30 reference;
- 1 lot;
- entry at 09:31 open;
- exit at 15:15 open;
- nearest expiry on/after the trade date;
- repository cost model with Base/Stress slippage;
- only pre-entry features may support prospective loss-avoidance inference.

This log records externally relevant research decisions and status, not hidden chain-of-thought.


## Baseline closure
Clean workflow 36532252218 passed both Base and Stress after the trade_date join and quantile-reporting fixes. Baseline result is now evidentiary and Phase C loser analysis has started. Preliminary discovery evidence points to high prior-day range plus near-expiry entry as a repeatable loser regime; this requires untouched holdout validation.


## Final conclusion
Phase E completed. The clean four-leg baseline is negative after realistic costs in both Base and Stress. Phase C and Phase D identify a reproducible loss-concentration regime (prior-day range > 1.314516% plus <=1.5 days to expiry) that improves holdout P&L when excluded but does not make the retained strategy profitable. The final manuscript and reproducibility supplement are stored on the Phase-E branch.
