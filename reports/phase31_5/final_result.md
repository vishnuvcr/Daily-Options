# Phase 31.5 discovery result

Finite ORB grid completed successfully in GitHub Actions run **36245174834**.

## Frozen grid

18 cells were tested:
- OR windows: 5, 15, 30 minutes
- Break multipliers: 0.25×, 0.50×, 1.00×
- Base slippage: ₹0.20/order
- Stress slippage: ₹0.40/order
- Full frozen transaction/statutory cost model
- One trade/day; defined-risk 200-point debit spread; same-day 15:10 exit

## Numerical result

| Regime | Best discovery cell | Trades | Total net | Mean weekly net | Median weekly net | Positive weeks |
|---|---|---:|---:|---:|---:|---:|
| Base | 30-min OR, 1.00× | 512 | ₹47,477.23 | ₹92.73 | -₹128.01 | 47.13% |
| Stress | 30-min OR, 1.00× | 512 | ₹25,955.61 | ₹50.69 | -₹168.12 | 45.90% |

The 30-min/1.00× cell is the only discovery cell with positive total net in both Base and Stress among the highest-performing Base cells, but it does **not** satisfy the project's weekly consistency gate: mean weekly net is far below ₹5,000 and positive-week frequency is below 70%.

Other Base-positive cells also deteriorate materially under Stress. For example, 5-min/0.50× falls from ₹48,731.34 Base total net to ₹995.39 Stress total net; 15-min/1.00× falls from ₹36,257.74 to ₹6,224.74.

## Cost and risk observations

For the 30-min/1.00× Base cell:
- Worst trade: -₹5,788.71
- Worst week: -₹10,155.68
- Total slippage: ₹21,778.50
- Total transaction/statutory costs: ₹55,538.27

The complete cell summary and daily trade/diagnostic ledgers are retained in the workflow artifact.

## Decision

**Phase 31.5 is CLOSED as discovery evidence; no ORB candidate is promoted to WFA/OOS.**

The result does not meet the preregistered ₹5,000/week consistency requirements. No result-driven parameter tuning is authorized from this grid.

The next phase should be a scientifically distinct, preregistered candidate only if its information barrier, data coverage, execution model and economic hypothesis justify testing.

Run: **36245174834**  
Artifact: **phase31-5-orb-discovery**  
Branch: `phase-31.5-finite-candidate-testing-v1`
