# Reversed OTM1 / 2x OTM2 Ratio Spread — Frozen Plan

## Research question
Does reversing every leg direction—buy 1 OTM1 call + sell 2 OTM2 calls, and buy 1 OTM1 put + sell 2 OTM2 puts—increase win rate and improve risk-adjusted/net profitability relative to the completed 1×2 backspread?

## Frozen controls
- Same NIFTY data revision and dates as the completed backspread.
- Same 09:30 strike reference, 09:31 entry and 15:15 exit.
- Same nearest-on-or-after expiry.
- Same one-lot sizing and historical lot sizes.
- Same Base/Stress costs and slippage.
- No strike, timing, exit, stop, target or filter optimization.

## Comparisons
Report win rate, mean/median P&L, gross P&L, costs, net P&L, profit factor, drawdown, payoff asymmetry and holdout performance. Win-rate improvement alone will not be treated as evidence of a superior strategy if losses become materially larger.

## Branch endpoint
Baseline comparison first. If a higher-win-rate structure is observed, a separate chronological discovery/holdout analysis may examine loss concentration, without changing the frozen structure.
