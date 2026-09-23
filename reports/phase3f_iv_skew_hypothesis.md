# Phase 3F IV-Skew Shock/Reversion

## Research question
Does a large intraday shock in near-ATM put-vs-call implied volatility, followed by mean reversion in relative option value, provide a tradable intraday edge after costs when expressed as a defined-risk four-leg structure?

## Structure
Use fixed strike bands relative to a daily ATM reference:
- CALL ATM+1 and ATM+2;
- PUT ATM-1 and ATM-2.

When put IV minus call IV jumps upward, the research takes the relative-value stance:
- long CALL ATM+1 / short CALL ATM+2 vertical;
- short PUT ATM-1 / long PUT ATM-2 vertical.

When the skew shock is downward, the signs are reversed.

This is a four-leg defined-risk structure. The payoff is not a naked short option.

## Signal
At 09:45, 10:00 or 10:15 IST, calculate:
- skew = IV(PUT ATM-1) - IV(CALL ATM+1);
- 15-minute skew shock = current skew minus skew 15 minutes earlier.

A trade is triggered when:
- absolute skew shock is at least 2, 4 or 6 IV points;
- absolute skew is at least 0, 2 or 4 IV points.

Entry is the next minute. The selected strikes remain fixed through the holding period.

## Initial grid
3 entry times × 3 shock thresholds × 3 absolute-skew thresholds × 3 holding periods = 81 parameter variants per expiry class.

Every variant is scored on:
- mean active-day net;
- mean all-calendar-day net;
- trade win rate;
- positive-day rate;
- profit factor;
- max drawdown;
- total net.

The ₹1,000/day promotion gate is applied only to net P&L after the project cost model and 0.20-point per-leg slippage.

## Stop rule
If no configuration has positive mean all-calendar-day net, the family is retired without additional exit-parameter tuning. A positive configuration may advance to a second-stage stress screen and then to walk-forward validation.
