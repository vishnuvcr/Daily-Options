# Phase 36 — Global Shock Breadth / Cross-Market Disagreement

## Status
CLOSED / RETIRED — discovery gate failed on authoritative run 36378802491.

All four true cells were executable, but none met the frozen economic promotion gate in both Base and Stress. No WFA/OOS or post-result retuning is authorized.

## Research question
When a large prior-session global equity shock reaches the NIFTY pre-open information set, does the shock behave differently when the six source markets broadly agree with the shock direction versus when the global move is internally split?

## Literature basis
International equity-market research documents return and volatility spillovers across markets, the importance of temporal proximity for transmission, and changing international comovement. This phase operationalizes a narrower trading hypothesis: the same aggregate global shock may carry different information when it is broad-based across markets versus internally split. This is a descriptive conditional-predictability test, not an assumption that spillover implies tradeability.

Primary literature:
- Diebold & Yilmaz, Economic Journal (2009), "Measuring Financial Asset Return and Volatility Spillovers, with Application to Global Equity Markets": https://onlinelibrary.wiley.com/doi/10.1111/j.1468-0297.2008.02208.x
- Connolly & Wang, Pacific-Basin Finance Journal (2003), "International equity market comovements: Economic fundamentals or contagion?": https://www.sciencedirect.com/science/article/pii/S0927538X02000604
- Ferreira, Martins & others, Economic Modelling (2019), "Return spillovers around the globe: A network approach": https://www.sciencedirect.com/science/article/pii/S0264999317310519
- Frijns, Verschoor & Zwinkels (2017), "Excess stock return comovements and the role of investor sentiment": https://www.sciencedirect.com/science/article/pii/S1042443117300963
- Phase 31.8 NSE evidence on U.S./Indian overnight transmission is retained in this repository.

## Data universe
Six daily equity indices from the pinned Phase 31.8 Yahoo Finance cache:
- S&P 500 (^GSPC)
- NASDAQ Composite (^IXIC)
- Nikkei 225 (^N225)
- Hang Seng (^HSI)
- DAX (^GDAXI)
- KOSPI Composite (^KS11)

No replacement source, ticker or date window is allowed after execution begins.

## Global feature construction
For each market:
- close-to-close return;
- 60-observation rolling z-score;
- standardization uses observations strictly before the selected global return;
- strict latest-completed-session-before-NIFTY-date alignment.

Aggregate:
- GLOBAL_LEAD = arithmetic mean of the six standardized returns.

Trigger:
- abs(GLOBAL_LEAD) >= 1.0.

Breadth / disagreement state:
- Count how many of the six standardized market returns have the same sign as GLOBAL_LEAD.
- BROAD_SHOCK = agreement count >= 4 of 6.
- SPLIT_SHOCK = agreement count <= 3 of 6.
- No third state; every triggered day is assigned to exactly one state unless all six standardized returns are zero, which cannot meet the trigger.

## Frozen execution grid
Four true cells:
- BROAD_SHOCK × 10:30 IST
- BROAD_SHOCK × 15:10 IST
- SPLIT_SHOCK × 10:30 IST
- SPLIT_SHOCK × 15:10 IST

Structure:
- positive GLOBAL_LEAD -> long 200-point CE debit spread;
- negative GLOBAL_LEAD -> long 200-point PE debit spread;
- ATM strike = nearest ₹50 to the 09:30 NIFTY bar close;
- entry = 09:31 option open;
- exit = selected horizon option close;
- nearest NIFTY expiry on/after trade date;
- one lot;
- no adjustment, stop, target, leverage or discretionary override.

## Null controls
Five fixed seeds: 101, 202, 303, 404, 505.

For each seed:
- jointly permute the six market z-score columns as a six-column block across NIFTY dates;
- recompute GLOBAL_LEAD and the breadth state from the permuted block;
- retain all NIFTY prices, option data, costs and execution rules unchanged.

Nulls are diagnostic only and cannot be promoted.

## Data gate
Before P&L:
- >=95% of global-feature-eligible NIFTY sessions must have all six strict-prior z-scores;
- zero prior-information violations;
- >=95% executable quote coverage in every true cell;
- deterministic expiry/ATM/lot mapping;
- exact 09:31 and exit option rows must be measurable.

If the gate fails, close DATA-LIMITED.

## Costs
- historical NIFTY lot sizes;
- established Phase 31.3/31.6 date-aware Paytm Money/NSE/statutory cost model;
- Base slippage ₹0.20 per option-price unit/order;
- Stress ₹0.40.

Accounting must satisfy:
raw gross - slippage - transaction/statutory costs = net P&L.

## Promotion gate
Both Base and Stress, and all four true cells evaluated:
- mean weekly net >= ₹5,000;
- median weekly net >= ₹5,000;
- positive-week rate >=70%.

No WFA/OOS unless the frozen discovery gate is cleared.

## Stop rule
No post-result:
- threshold change;
- added indices;
- alternate breadth thresholds;
- alternate lookback;
- strike optimization;
- structure switching;
- result-driven retuning.

## Required outputs
- acquisition manifest;
- data gate;
- daily feature panel;
- true signal ledger;
- Base/Stress trade ledgers;
- execution coverage;
- true-cell summaries;
- weekly summaries;
- five-seed null summaries for each friction;
- accounting reconciliation;
- drawdown, worst-week and tail statistics;
- final manuscript;
- updated error log/status/README.
