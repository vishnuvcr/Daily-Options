# Reversed OTM1 / 2x OTM2 Four-Leg Ratio — Status

## Completed baseline comparison

Construction tested:
- BUY 1 OTM1 PUT
- SELL 2 OTM2 PUT
- BUY 1 OTM1 CALL
- SELL 2 OTM2 CALL
- Same 09:30 reference, 09:31 execution, nearest on/after expiry, 15:15 exit, one lot and historical lot sizes as the original study.

Authoritative workflow: 36534525761

| Metric | Reversed Base | Reversed Stress |
|---|---:|---:|
| Trades | 1,209 | 1,209 |
| Wins | 709 | 661 |
| Losses | 500 | 548 |
| Win rate | **58.64%** | **54.67%** |
| Gross P&L | ₹272,009.75 | ₹272,009.75 |
| Costs | ₹446,177.47 | ₹603,113.47 |
| Net P&L | **-₹174,167.72** | **-₹331,103.72** |
| Mean net/trade | -₹144.06 | -₹273.87 |
| Median net/trade | ₹227.52 | ₹107.52 |
| Profit factor | 0.836 | 0.706 |
| Max drawdown | -₹187,691.21 | -₹336,394.72 |

## Comparison with original orientation

Original Base/Stress win rates were 25.81% / 23.90%. Reversing the legs increases them to 58.64% / 54.67%.

The gross P&L flips from -₹272,009.75 to +₹272,009.75 because the reversed structure is the opposite payoff orientation of the original four-leg structure. Costs therefore become decisive: the reversed structure remains negative after realistic friction.

## Additional observation

Expiry-day trades are particularly strong for the reversed construction:
- 253 expiry-day trades
- 67.19% Base win rate
- +₹59,074.74 Base net P&L
- +₹233.50 mean Base net/trade

Non-expiry days remain negative:
- 956 trades
- 56.38% Base win rate
- -₹233,242.46 Base net P&L

This is a descriptive finding only. It has not been optimized or holdout-validated and must not yet be treated as a trading filter.

## Interpretation

Reversing the orientation clearly raises the probability of a positive trade, but the payoff asymmetry becomes unfavorable after costs: winners are smaller on average than losers. The next bounded research question should therefore be whether the reversed construction can be made positive by a pre-entry regime filter, particularly around expiry-day/volatility conditions, using a fresh chronological discovery/holdout split.
