# Alternating OTM Buy/Sell Variant — Frozen Research Plan

## Research question
Does reversing the quantity direction—BUY 1 OTM1 and SELL 2 OTM2 on both call and put sides—increase win rate or improve risk-adjusted/net expectancy relative to the completed 1×2/1×2 backspread?

## Frozen structure
- NIFTY, 1 lot.
- 09:30 IST reference; 09:31 IST option entry.
- Nearest listed expiry on or after trade date.
- BUY 1 first OTM call + SELL 2 second OTM calls.
- BUY 1 first OTM put + SELL 2 second OTM puts.
- Exit 15:15 IST (existing 15:14 fallback only if required by engine).
- No stop, target, strike optimization, or discretionary adjustment.

## Phases
A. Implementation/data gate and unit tests.
B. Base/Stress full historical baseline using identical data/cost model.
C. Compare win rate, expectancy, P&L, profit factor, drawdown and annual/expiry behavior against the completed backspread.
D. Analyze losing-trade circumstances using only pre-entry information.
E. Optional frozen holdout test only if Phase D identifies a candidate rule; no threshold tuning on holdout.
F. Manuscript/conclusion.

## Primary hypothesis
Reversing the payoff orientation may increase the frequency of profitable small/contained moves, but it also creates the opposite tail exposure. The backtest will determine whether any win-rate increase survives transaction costs and whether expectancy improves.

## Integrity
The original backspread result remains frozen and is not modified. This branch is a separate strategy experiment.
