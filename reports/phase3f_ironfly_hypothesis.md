# Phase 3F Iron-Fly Volatility Regime Hypothesis

## Research question
Can a defined-risk short-volatility iron fly, conditioned on elevated implied-to-realized volatility and a range/neutral option-chain regime, improve net intraday expectancy and consistency without the unbounded loss profile of a naked short straddle?

## Economic rationale
The directional IV/OI/volume imbalance screen produced negative net expectancy across 972 variants. The next test therefore changes the payoff mechanism and the regime condition rather than retuning directional thresholds.

The iron fly used here is:
- short ATM call + short ATM put;
- long ATM+2 call + long ATM-2 put;
- one trade per day/expiry/parameter tuple;
- signal at t and entry at t+1 minute;
- time exit in Stage 1;
- close-based stop/target in Stage 2 only for the best Stage-1 regime configurations.

## Stage 1
Regime grid:
- entry: 09:45, 10:00, 10:15 IST;
- IV/RV minimum: 1.00, 1.25, 1.50;
- absolute 15-minute spot return maximum: 0.05%, 0.10%, 0.20%;
- absolute OI imbalance maximum: 5%, 10%, 20%;
- absolute volume imbalance maximum: 5%, 10%, 20%;
- 120-minute exit.

The first gate is economic: after realistic costs and slippage, a candidate must have positive all-calendar-day expectancy and a profit factor above 1 before additional exit tuning is permitted.

## Stage 2
Only the top 10 Stage-1 configurations are expanded:
- stop multiplier: 1.3, 1.5, 2.0 times entry credit;
- target credit decay: 25%, 50%, 75%;
- hold: 60, 120, 180 minutes.

Stage 2 uses exact four-leg exit quotes at the close of the trigger bar and the eight-order cost model. A promoted candidate must be rerun with the independent execution/robustness protocol in the parent research plan.

## Risk controls
The payoff is defined-risk by construction. No naked short leg is used. No signal may use information from bars after the entry decision. The research remains a backtest; no live-trading conclusion is drawn from Stage 1/2 alone.
