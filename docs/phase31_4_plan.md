# Phase 31.4 — Next strategy-family discovery and preregistration

## Status
ACTIVE — bounded discovery only. No parameter tuning of Phase 31.1 is permitted.

## Purpose
Move from the failed fixed-ratio candidate to materially different, source-independent strategy families while preserving the frozen execution/cost methodology.

## Research questions
1. Which economically distinct NIFTY option mechanisms have a defensible hypothesis for producing >= ₹5,000 net per completed week at a declared reference size?
2. Which mechanisms remain testable with the pinned 1-minute option/index data without look-ahead?
3. Which candidate families merit a preregistered numerical grid before any optimization?
4. Do global-open, volatility, VWAP/opening-range, option-microstructure, and defined-risk structures show evidence that justifies deeper testing?

## Candidate families
A. Global overnight gap -> India-open continuation/fade.
B. Opening-range breakout translated into defined-risk debit spreads.
C. VWAP deviation mean reversion with volatility/regime filter.
D. IV-vs-realized-volatility dislocation.
E. OI/volume/price microstructure with deterministic signal timing.
F. India-VIX/realized-volatility regime-conditioned defined-risk structures.

## Data and evidence
- Reuse pinned/cached NIFTY option/index source where sufficient.
- Search and document relevant NSE/BSE methodology, academic literature, open-source implementations and reproducible public datasets.
- Do not substitute inaccessible or unverifiable claims for primary evidence.
- Timestamp all external features and enforce the information barrier.

## Execution and costs
Frozen from research_plan.md:
- Base slippage ₹0.20/order.
- Stress slippage ₹0.40/order.
- Paytm Money-style brokerage and applicable statutory/exchange costs.
- Conservative fills; no hidden scaling.
- Historical lot-size and expiry schedules are mandatory.

## Discovery gate
A family advances only if:
- its mechanism is materially distinct from retired Phase 31.1;
- all economically material rules can be deterministic;
- required data coverage is adequate;
- a finite preregistered grid can be specified;
- no parameter is selected from the eventual test period.

## Statistical plan
For any family promoted to numerical testing:
- daily and weekly net P&L;
- mean, median, positive-week rate;
- profit factor, drawdown, expected shortfall/CVaR;
- execution coverage and trade concentration;
- Base/Stress comparison;
- year/regime/session breakdown;
- bootstrap uncertainty and multiple-testing accounting where feasible;
- nested WFA before any final OOS promotion.

## Stop logic
This phase ends after the finite candidate catalogue and preregistered grids are frozen. It does not search indefinitely and does not tune toward the ₹5,000 target.

## Deliverables
- candidate catalogue;
- literature/source manifest;
- data-availability matrix;
- preregistered hypothesis/grid file;
- phase report;
- updated error/status logs.
