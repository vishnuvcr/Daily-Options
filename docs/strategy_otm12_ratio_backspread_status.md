# Status — OTM1 / 2xOTM2 Four-Leg Intraday Ratio Backspread

As of: 2026-09-29

| Phase | Status | Result |
|---|---|---|
| A implementation/data gate | CLOSED | Timestamp probe passed; option/session trade-date join fixed; regression coverage added. |
| B baseline Base/Stress | CLOSED | Clean workflow 36532252218 PASS. 1,209 trades, 98.53% execution coverage. Base net P&L -₹717,921.87; Stress net P&L -₹874,857.87. |
| C losing-trade/common-circumstance analysis | ACTIVE | Dedicated branch will quantify winner/loser feature differences and stable loser regimes. |
| D frozen holdout filter probe | PENDING | Only after C. |
| E conclusion/manuscript | PENDING | Bounded endpoint. |

## Clean baseline
- Workflow: 36532252218
- Commit: `2a2f4613484c8f600c76af889f0b3aa27cb8b889`
- Eligible sessions: 1,227
- Executed trades: 1,209
- Execution coverage: 98.53%
- Base: 312 wins / 897 losses; win rate 25.81%; gross P&L -₹272,009.75; costs ₹445,912.12; net P&L -₹717,921.87; profit factor 0.517; max drawdown -₹716,320.49.
- Stress: 289 wins / 920 losses; win rate 23.90%; gross P&L -₹272,009.75; costs ₹602,848.12; net P&L -₹874,857.87; profit factor 0.454; max drawdown -₹873,136.49.
- Median net trade: -₹915.50 Base / -₹1,032.73 Stress.
- Mean winning trade: ₹2,459.89 Base / ₹2,521.14 Stress; mean losing trade: -₹1,655.97 Base / -₹1,742.90 Stress.

## Phase-C early evidence
- A shallow loss classifier has no useful predictive power: discovery cross-validated ROC-AUC is approximately 0.51 Base and 0.38 Stress.
- A separate discovery-only regression tree identifies a repeatable high-loss regime: prior-day range above ~1.3145% together with <=1.5 calendar days to expiry.
- That regime is deliberately being treated as a candidate loser-avoidance rule only; holdout validation is required before any operational use.

## Integrity rules
- No post-entry variable may be used as an entry filter.
- No parameter is tuned on the holdout.
- No earlier failed run is used as trading evidence.
- Base and Stress both must agree before a result is treated as robust.
