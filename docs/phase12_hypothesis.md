# Phase 12 — Derivative Lead/Lag → Option Execution

## Research question

Does a short-horizon price-discovery imbalance between the nearest NIFTY futures contract and NIFTY spot contain incremental information for the next-minute/next-few-minute spot direction, and can that information be expressed through a cost-adjusted defined-risk option spread?

## Why this is materially different

Retired families used spot-only momentum, option-premium lead/lag, OI-breaks, cross-index strength, and regime-filtered credit spreads. Phase 12 instead tests the **relationship between a tradable derivative price and spot before selecting the option trade**.

The literature does not justify assuming a permanent direction. A 2007 NIFTY study reported index futures and options leading cash, with calls leading cash by up to one hour, while later work found periods in which spot led futures. Therefore this phase estimates the relationship empirically rather than imposing a fixed lead direction. Sources:
- https://indianjournals.com/article/mc-11-2-002
- https://indianjournals.com/article/abjfm-1-2-002
- https://ideas.repec.org/a/spr/decisn/v43y2016i3d10.1007_s40622-016-0137-1.html

## Pre-registration

NIFTY only in Stage 1.

Variant grid: 144 configurations
- lead window: 1 / 3 minutes;
- lead-gap z-threshold: 0.75 / 1.00 / 1.50;
- entry: 09:45 / 10:00 IST;
- expiry: next WEEK / next MONTH;
- debit-spread width: 1 / 2 available strike steps;
- maximum hold: 10 / 20 / 30 minutes;
- risk profile: stop 30% / target 60%, or stop 50% / target 100%.

No result-based parameter additions are permitted.

## Signal

At minute t, construct a rolling standardized return for the active NIFTY futures contract and NIFTY spot over the selected lead window k:

lead_gap(t) = z_futures_return_k(t) - z_spot_return_k(t)

A signal exists only when:
- |lead_gap(t)| >= threshold;
- futures and spot returns have the same sign;
- the signal timestamp is within the allowed entry window;
- the futures contract is demonstrably nearest-to-expiry from information available at t.

The next executable minute is the option entry. There is no look-ahead to future spot movement.

## Execution

- Express CALL signals as ATM/OTM defined-risk debit spreads.
- Express PUT signals symmetrically.
- Strike and expiry are frozen at entry.
- Use next-minute option opens, conservative stop/target collision handling and maximum hold.
- Historical lot size is expiry-aware.
- Base slippage 0.20 premium points/leg; stress 0.40.

## Data sources

Primary public futures source: OpenChart, which documents authenticated-free historical NSE IDX/EQ/FO OHLCV access including 1-minute intervals and NIFTY futures symbols. This is a source adapter, not a guarantee of historical completeness: the first gate must verify coverage and timestamp integrity. https://github.com/Arpitjain1234/openchart

Option/spot source: pinned project NIFTY option dataset already cached by the repository (artist-23/nifty-options-data, revision 45e0a04). Deployment would require licensed/executable-data validation.

Secondary data-source leads for reconciliation:
- Kaggle public NSE F&O 1-minute dataset: https://www.kaggle.com/general/545727
- OptionVault commercial/research dataset: https://github.com/QuantDev-stack/OptionVault
- Zerodha-based collectors for 1-minute NIFTY options/futures are documented publicly but require account authentication.

## Data gate

Before any strategy computation:
1. futures history must contain at least 300 trading days;
2. futures and spot timestamps must overlap for at least 90% of eligible market minutes;
3. active-contract selection must be deterministic and expiry-aware;
4. no duplicate timestamp/contract rows after normalization;
5. futures prices must be positive and basis continuity must be auditable;
6. option entry coverage must be >= 80% of generated signals before P&L analysis.

Failure of the data gate parks the phase without producing a strategy result.

## Promotion gate

Preliminary: at least one variant with mean active-day net >= ₹1,000/lot.

Formal:
- positive untouched walk-forward expectancy;
- at least one untouched test window >= ₹1,000/lot/day;
- doubled-slippage stress does not materially collapse the edge;
- adequate trade count and no single-period concentration dominating the result;
- no parameter selected using the untouched test data.
