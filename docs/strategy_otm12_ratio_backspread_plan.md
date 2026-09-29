# Strategy Research Plan — OTM1 / 2xOTM2 Four-Leg Intraday Ratio Backspread

Branch: strategy/otm1-2x-otm2-ratio-backspread-v1
Created: 2026-09-29
Status: preregistered / implementation

## Research question
For the fixed one-lot structure (Sell 1 OTM1 PUT, Buy 2 OTM2 PUTs, Sell 1 OTM1 CALL, Buy 2 OTM2 CALLs), which market circumstances are associated with net profitability, and which pre-entry circumstances are disproportionately present in losing trades?

## Frozen strategy definition
- Underlying: NIFTY index options.
- Position size: 1 lot.
- Entry reference: 09:30 IST close.
- Executable entry: 09:31 IST bar open.
- Exit: 15:15 IST bar open.
- Expiry: nearest listed NIFTY expiry on or after the trading date.
- OTM1 call: first listed strike strictly above the 09:30 NIFTY reference; OTM2 call: second listed strike.
- OTM1 put: first listed strike strictly below the reference; OTM2 put: second listed strike.
- Quantities/signs: OTM1 PE -1, OTM2 PE +2, OTM1 CE -1, OTM2 CE +2.
- No baseline discretionary adjustment, stop, target, leg replacement, or post-result tuning.

## Execution and cost model
Reuse the repository's established Paytm Money/NSE/statutory convention: ₹20 per order (₹40 per leg round trip), date-aware option STT, NSE transaction charge, SEBI turnover fee, stamp duty and GST, plus Base slippage ₹0.20 and Stress slippage ₹0.40 per option price point per side. Historical NIFTY lot size is applied by expiry.

## Data
Pinned source: thetrademarkk/india-index-options-1m, revision 51ca58c. Expected files: data/cache/phase24_trademarkk/index/NIFTY.parquet and data/cache/phase24_trademarkk/options/NIFTY/*.parquet. Backtest window: 2021-07-01 through 2026-08-04. Raw data are not committed because of size; GitHub Actions cache persists/reuses the pinned dataset.

## Pre-entry feature family
Only information available by 09:30 may support a prospective loss-avoidance rule: overnight gap; first-15-minute return and range; prior-day range/return; prior-20-session median range; weekday; expiry proximity and expiry-day flag; NIFTY level; four-leg entry premiums; short-premium sum; far-premium sum; net entry credit/debit; long-to-short premium ratio; tail-premium/convexity proxy. Post-entry variables are diagnostic only.

## Statistical analysis
Report trade count, execution coverage, gross/net P&L, costs, win rate, mean/median, average win/loss, expectancy, profit factor, drawdown and calendar/expiry breakdown. Compare winners versus losers for every frozen pre-entry feature, use discovery quantile bins, and replicate those bins unchanged on a chronological holdout. Use a shallow interpretable decision tree as a diagnostic, not as an authorization to retune the baseline.

Chronological split: discovery 2021-07-01 through 2024-12-31; untouched holdout 2025-01-01 through the latest complete session in the pinned dataset.

## Research phases
A. Implementation and data gate.
B. Frozen Base/Stress baseline.
C. Losing-trade/common-circumstance analysis.
D. Frozen holdout filter probe.
E. Conclusion and bounded manuscript. No open-ended optimization.

## Main hypotheses
H1: the structure benefits from sufficiently large realized movement because it is convex outside the short OTM1 strikes.
H2: very small opening movement is associated with losses because premium decay dominates.
H3: entry premium geometry conditions profitability.
H4: expiry proximity and expiry-day microstructure change the loss rate.
H5: a simple pre-entry no-trade filter may reduce losses without eliminating most profitable trades.
