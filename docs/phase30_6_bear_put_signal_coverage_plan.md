# Phase 30.6 — Bear Put source-interpretation signal coverage

## Research question
Which deterministic mathematical interpretations of the source's "resistance -> crack/gap-down" entry concept produce sufficient, reproducible weekly signal coverage without using option P&L to choose the definition?

## Source evidence
The Equity Income video was published January 4, 2026 and its description explicitly promises key entry/exit rules and risk-management guidance. The archived full caption stream is 243 segments. The transcript provides:
- sustained resistance;
- a crack or gap-down as the bearish trigger;
- a preference for trading resistance;
- a 26,300/26,200 bear put worked example;
- a later 200–300 point gap-up failure example leading to a ratio adjustment;
- "do not rush" and reversal-based square-off logic for the added short put.

The transcript does **not** provide a fixed mathematical resistance definition, crack threshold, exact entry clock, fixed hard stop, or numeric profit target. Therefore these remain explicit experimental dimensions.

## Frozen 54-cell coverage matrix

Resistance lookback:
- 30 minutes
- 60 minutes
- 120 minutes

Resistance touch tolerance:
- 0.10%
- 0.20%
- 0.40%

Bearish trigger:
- close/crack below resistance by 0.10%, 0.20%, or 0.40%; OR
- gap-down open below resistance by 0.20%, 0.50%, or 1.00%

That is 3 × 3 × 6 = **54 deterministic definitions**.

### Mathematical definition
For each trading day, using only bars strictly before the signal minute:
1. Compute the prior-window rolling high over the selected lookback.
2. Define a resistance candidate when at least two separate bars in the window have highs within the selected tolerance of the candidate resistance.
3. A crack signal occurs when the current 1-minute close is below resistance by the selected crack threshold.
4. A gap-down signal occurs when the current 1-minute open is below resistance by the selected gap threshold.
5. The first qualifying signal of the day is retained.
6. No signal may use bars after the signal minute.

This is a **source interpretation grid**, not a claim that any one mathematical definition is the original creator's exact rule.

## Coverage outputs
For each of 54 definitions record:
- number of trading days with a signal;
- signals per 32-week option-calendar window;
- days with zero/multiple signals;
- first/median/latest signal clock;
- clustering by weekday;
- percentage of option-calendar weeks with a qualifying entry;
- missing-data rate.

No P&L, strike selection or adjustment optimization is allowed in Phase 30.6.

## Advancement gate
At least 20 completed weeks must contain signals for a definition to be eligible for Phase 30.7. All 54 definitions remain registered; eligibility is a feasibility filter, not a performance selection.

## Status
Coverage grid registered; backtest remains blocked pending coverage results and source-rule interpretation audit.
