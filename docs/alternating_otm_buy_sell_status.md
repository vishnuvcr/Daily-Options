# Status — Alternating OTM Buy/Sell Variant

Branch: `strategy/alternating-otm-buy-sell-v1`
Status: **BASELINE CLOSED — HIGHER WIN RATE, STILL NEGATIVE AFTER COSTS**

Authoritative clean workflow: **36535251511**

## Exact tested variant

Instead of:
- SELL 1 OTM1 CE + BUY 2 OTM2 CE
- SELL 1 OTM1 PE + BUY 2 OTM2 PE

the variant uses:
- BUY 1 OTM1 CE + SELL 2 OTM2 CE
- BUY 1 OTM1 PE + SELL 2 OTM2 PE

Everything else is unchanged: NIFTY, one lot, 09:30 reference, 09:31 execution, nearest on/after expiry, 15:15 exit, historical lot sizes, Base/Stress slippage and the same transaction-cost engine.

## Baseline comparison

| Metric | Original Base | Alternating Base | Original Stress | Alternating Stress |
|---|---:|---:|---:|---:|
| Trades | 1,209 | 1,209 | 1,209 | 1,209 |
| Win rate | 25.81% | **58.64%** | 23.90% | **54.67%** |
| Gross P&L | -₹272,009.75 | **+₹272,009.75** | -₹272,009.75 | **+₹272,009.75** |
| Costs | ₹445,912.12 | ₹446,177.47 | ₹602,848.12 | ₹603,113.47 |
| Net P&L | -₹717,921.87 | **-₹174,167.72** | -₹874,857.87 | **-₹331,103.72** |
| Mean net/trade | -₹593.81 | **-₹144.06** | -₹723.62 | **-₹273.87** |
| Median net/trade | -₹915.50 | **+₹227.52** | -₹1,032.73 | **+₹107.52** |
| Profit factor | 0.517 | **0.836** | 0.454 | **0.706** |
| Max drawdown | -₹716,320 | **-₹187,691** | -₹873,136 | **-₹336,395** |

## Key finding

The reversal produces a very large win-rate increase:
- Base: +32.83 percentage points.
- Stress: +30.77 percentage points.

But the win rate is not sufficient for profitability because the losing trades are much larger:
- Alternating Base mean winner: +₹1,248.68.
- Alternating Base mean loser: -₹2,118.96.
- Alternating Stress mean winner: +₹1,203.84.
- Alternating Stress mean loser: -₹2,056.28.

The exact gross P&L sign flip (+₹272,009.75 versus -₹272,009.75) shows that reversing every leg's buy/sell direction creates the opposite gross payoff of the original structure. Costs then move both variants further negative.

## Untouched 2025+ holdout

| Metric | Original Base | Alternating Base | Original Stress | Alternating Stress |
|---|---:|---:|---:|---:|
| Trades | 348 | 348 | 348 | 348 |
| Win rate | 27.59% | **60.06%** | 26.72% | **57.47%** |
| Net P&L | -₹282,985 | **-₹24,907** | -₹343,081 | **-₹85,003** |
| Mean/trade | -₹813.18 | **-₹71.57** | -₹985.87 | **-₹244.26** |
| Median/trade | -₹1,316.45 | **+₹446.72** | -₹1,488.91 | **+₹266.72** |

This is important: the win-rate increase is not confined to the discovery period. It persists on the chronological 2025+ holdout, and the alternating structure dramatically reduces the loss versus the original. However, it **still does not reach positive expectancy after costs**.

## Loss mechanism

The alternating structure is effectively the opposite payoff orientation. It collects many smaller/contained wins when the market stays within the profitable region, but a sufficiently large move can make the 2× short far-OTM wings dominate the single nearer long wing.

The holdout therefore shows the characteristic pattern:
- high win rate,
- positive median trade,
- negative mean trade,
- occasional large tail losses.

That is a classic warning that win rate alone is not an adequate objective.

## Phase-C clue

The preliminary loss tree gives modest discrimination (ROC-AUC about 0.55 in both frictions), but this is not yet sufficient to promote a filter. The most visible holdout loss concentration is associated with very low first-15-minute directional movement and very high long/short-range regimes, but no filter has been frozen or tuned.

## Conclusion

**Yes — alternating the buys and sells substantially increases win rate.**

But it does not yet create a profitable strategy. The correct next research question is not "how do we maximize win rate?" but:

> Can we remove the small subset of large-tail losing trades from this higher-win-rate structure without destroying its 55–60% winning-trade base?

Any such filter must be frozen from discovery data and validated on a new untouched holdout.
