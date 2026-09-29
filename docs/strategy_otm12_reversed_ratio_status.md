# Reversed OTM1 / 2x OTM2 Ratio Spread — Initial Result

## Frozen variant tested
- Buy 1 OTM1 CE, sell 2 OTM2 CE
- Buy 1 OTM1 PE, sell 2 OTM2 PE
- Same strike selection, 09:30 reference, 09:31 entry, 15:15 exit, expiry, one-lot sizing and costs as the original backspread.

## Clean workflow
- Workflow: 36534517785
- Eligible sessions: 1,227
- Completed trades: 1,209
- Execution coverage: 98.53%

| Metric | Original Base Backspread | Reversed Base | Original Stress | Reversed Stress |
|---|---:|---:|---:|---:|
| Win rate | 25.81% | **58.64%** | 23.90% | **54.67%** |
| Mean net/trade | -₹593.81 | **-₹144.06** | -₹723.62 | **-₹273.87** |
| Median net/trade | -₹915.50 | **₹227.52** | -₹1,032.73 | **₹107.52** |
| Mean winner | ₹2,459.89 | ₹1,248.68 | ₹2,521.14 | ₹1,203.84 |
| Mean loser | -₹1,655.97 | **-₹2,118.96** | -₹1,742.90 | **-₹2,056.28** |
| Profit factor | 0.517 | **0.836** | 0.454 | **0.706** |
| Net P&L | -₹717,921.87 | **-₹174,167.72** | -₹874,857.87 | **-₹331,103.72** |
| Max drawdown | -₹716,320.49 | **-₹187,691.21** | -₹873,136.49 | **-₹336,394.72** |

## Holdout
On the untouched 2025+ holdout:
- Base win rate: 60.06%; net P&L -₹24,907.42; profit factor 0.943.
- Stress win rate: 57.47%; net P&L -₹85,003.42; profit factor 0.816.

## Interpretation
Reversing the legs materially increases win rate and substantially reduces drawdown and aggregate loss, but the strategy remains negative after realistic costs. The higher win rate is purchased by larger average losing trades.

This is therefore a promising structural direction for a bounded next phase, but it is not yet a profitable strategy.
