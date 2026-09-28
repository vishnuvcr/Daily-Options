# Phase 37 — Global Shock × NIFTY Opening Dislocation

## Status
CLOSED / RETIRED — discovery gate failed on authoritative run 36379200435.

All four true cells were technically executable but failed the frozen economic promotion gate in both Base and Stress. No WFA/OOS or post-result retuning is authorized.

## Research question
After a large prior-session global equity shock, does the relationship between the global direction and the NIFTY 09:30 opening gap identify a short-horizon directional options edge?

## Hypothesis
A global overnight shock should be reflected partly in the NIFTY opening gap. A large agreement between the two may indicate continuation information, while a large disagreement may indicate an opening dislocation that mean-reverts. The phase tests both states with a fixed direction rule.

## Frozen global shock
Use the six-index Phase 31.8 GLOBAL_LEAD:
- S&P 500, NASDAQ Composite, Nikkei 225, Hang Seng, DAX, KOSPI;
- 60-observation strictly-prior z-scores;
- latest completed global session strictly before the NIFTY trade date;
- trigger abs(GLOBAL_LEAD) >= 1.0.

## Frozen NIFTY opening-gap feature
At 09:30 IST:
- prior NIFTY close = last completed NIFTY session close before the trade date;
- opening gap = ln(NIFTY_09:30 / prior_close);
- GAP_Z = current opening gap standardized by a 60-observation rolling mean and standard deviation calculated strictly from earlier NIFTY opening gaps;
- threshold abs(GAP_Z) >= 0.50.

State:
- CONVERGENT = GLOBAL_LEAD sign == GAP_Z sign.
- DIVERGENT = GLOBAL_LEAD sign != GAP_Z sign.
- Zero-valued signs are no-trade.

## Frozen direction rule
- CONVERGENT: trade in GLOBAL_LEAD direction.
- DIVERGENT: trade opposite GLOBAL_LEAD direction.

## Frozen option structure
- one-lot 200-point debit spread;
- ATM nearest ₹50 to NIFTY 09:30 bar close;
- CE spread for bullish direction, PE spread for bearish direction;
- entry 09:31 option open;
- exit 10:30 or 15:10 IST;
- nearest expiry on/after trade date;
- no stops, targets, adjustments or leverage.

## Four true cells
- CONVERGENT × 10:30
- CONVERGENT × 15:10
- DIVERGENT × 10:30
- DIVERGENT × 15:10

## Null controls
Five fixed seeds: 101, 202, 303, 404, 505.

For each seed, jointly permute the six global z-score columns as a block across NIFTY dates. Recompute GLOBAL_LEAD and the CONVERGENT/DIVERGENT state with the original NIFTY GAP_Z held fixed. All option execution, costs and exits remain unchanged.

## Data gate
- >=95% global-feature eligibility after prior-only warm-up handling;
- >=95% combined GLOBAL_LEAD + GAP_Z feature coverage among globally eligible sessions;
- zero prior-information violations;
- >=95% exact option quote coverage in every true cell;
- deterministic expiry/strike/lot mapping.

If the gate fails, close DATA-LIMITED.

## Costs
- historical NIFTY lot sizes;
- established Phase 31.3/31.6 Paytm Money/NSE/statutory cost model;
- Base slippage ₹0.20/order;
- Stress ₹0.40/order;
- reconciliation: raw gross - slippage - transaction/statutory costs = net.

## Promotion gate
In both Base and Stress, all four cells must be evaluated and any promoted cell must satisfy:
- mean weekly net >= ₹5,000;
- median weekly net >= ₹5,000;
- positive-week rate >=70%.

No WFA/OOS unless the frozen discovery gate is cleared.

## Stop rule
No result-driven changes to:
- global threshold;
- GAP_Z threshold;
- gap lookback;
- index universe;
- direction mapping;
- strike width;
- exits;
- cost model.

## Deliverables
Plan, literature review, source manifest, implementation/tests, manual workflow, data gate, true/null ledgers, Base/Stress summaries, execution coverage, accounting reconciliation, final manuscript, README/status/error-log updates.
