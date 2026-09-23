# Phase 3I — Opening-Range False-Break Mean Reversion

## Research question

After a NIFTY opening-range breakout fails and price re-enters the opening range, does the reversal continue far enough over the next 15–60 minutes to produce a positive-cost intraday debit-spread edge?

## Rationale

NSE opening periods have unusually high volatility and price-discovery activity. Indian high-frequency evidence reports strong price discovery in the first 15 minutes and opening serial-correlation/reversal effects after the call auction. Recent NSE breakout research also shows that opening-range designs are materially sensitive to the exact opening window and holding period. These findings justify testing a very specific false-break reversal event rather than a broad technical-indicator sweep.

Sources:
- https://www.sciencedirect.com/science/article/pii/S105752191500023X
- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5198458

## Information barrier

1. Construct the NIFTY spot minute series from option-chain spot fields.
2. For each trading day, build the opening range high/low from the first 5, 15, or 30 minutes after 09:15 IST.
3. A break is observed only after the opening range is complete.
4. A downside false break occurs when price first trades at least 0.05% or 0.10% below the opening-range low and a later minute re-enters at least 0.02% or 0.05% above that low.
5. An upside false break is symmetric.
6. The re-entry minute is the signal timestamp; the trade is entered on the next executable minute only.
7. Only the first qualifying signal per day per parameter variant is used.

## Trade expression

- Downside false break -> buy a call debit spread.
- Upside false break -> buy a put debit spread.
- Expiry: WEEK or MONTH.
- Spread width: 1 or 2 strike steps.
- Maximum hold: 15, 30 or 60 minutes.
- Stop: 50% of initial debit.
- Target: 175% of initial debit.
- Path collisions are resolved conservatively.
- One NIFTY lot with the date-aware lot-size resolver.

## Pre-registered grid

| Parameter | Values |
|---|---|
| Opening-range length | 5, 15, 30 minutes |
| Break excursion | 0.05%, 0.10% |
| Re-entry confirmation | 0.02%, 0.05% |
| Expiry | WEEK, MONTH |
| Spread width | 1, 2 strikes |
| Max hold | 15, 30, 60 minutes |

Total: 144 variants.

## Costs and validation

Use the repository transaction-cost model, Rs 20/order research brokerage default, applicable statutory charges, date-aware NIFTY lots, 0.20 premium-point base slippage per leg and 0.40 stress slippage.

Validation is train -> validation -> 5-day embargo -> untouched test using 180/60/60 trading-day windows and 60-day steps. Parameters are never selected from the test period.

## Promotion / stop rule

The family is promoted only if it has positive net OOS expectancy after costs and at least one untouched test window >= Rs 1,000/lot/day. If the bounded 144-variant family fails or deteriorates under stress, retire it without expanding thresholds or adding ad-hoc filters.

This is the final Phase 3 exploratory family under the present public dataset. A failure moves the project to final synthesis and explicit data-quality/execution limitations rather than endless parameter mining.
