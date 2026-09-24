# Phase 15 — VRP Regime + Jump-Brake Short Volatility

## Research question
Can an intraday NIFTY short-volatility strategy avoid the weak-tail regimes that hurt unfiltered short straddles by entering only when an option-implied volatility premium over recent realized volatility is sufficiently positive and the recent 15-minute spot move is not already in a jump state?

## Preregistered grid
288 fixed cells:
- Entry 09:30 / 10:00 / 10:30 IST
- VRP threshold 0 / 2 / 4 volatility points
- 15-minute absolute-return brake <= 0.25% / 0.40%
- ATM short straddle / ATM±2 iron fly
- next WEEK / next MONTH expiry
- 30 / 60 minute hold
- stop at 1.30x / 1.50x entry package
- fixed target at 0.50x entry package

No grid expansion or result-driven threshold tuning is allowed.

## Data
Primary preliminary source: artist-23/nifty-options-data revision 45e0a04, reusing the Phase 3F cache. The audit covers 33.96M rows in 84 parquet files; Phase 15 does not use the quarantined volume field.
Independent later validation: rissin/nse-options-intraday 1-minute NIFTY option files plus an independently sourced NIFTY index series. The Rissin dataset documents NIFTY 1-minute coverage from Oct 2024 onward and option expiry/strike/option_type fields. citeturn967763search2turn967763search9

## Why this family is distinct
Earlier short-straddle work was largely unfiltered or used a single VRP threshold. Phase 15 combines a continuous IV-minus-realized-volatility regime with an explicit short-horizon jump brake and a capped-risk iron-fly alternative.

Recent NIFTY literature reports persistent positive VRP in many periods but also finds that unfiltered short-volatility can be overwhelmed by tail losses and implementation costs, motivating explicit regime and tail-risk conditioning. citeturn601520search0turn601520search3turn601520search10

## Promotion gate
Positive base OOS expectancy, at least one untouched test window >= ₹1,000/lot/day, positive under doubled slippage, sufficient trade count, no one-day concentration, and reproduction on the independent later source.