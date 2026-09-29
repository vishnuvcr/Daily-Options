# Phase 57 — 09:15–09:30 Opening-Range Volatility Regime × Opening-Gap Direction

## Research question

Does the size of the NIFTY opening range formed between 09:15 and 09:30, measured relative to the prior session's range, condition whether the same session's opening gap continues or reverses strongly enough to produce at least ₹5,000 net per completed trading week after realistic costs?

## Literature rationale

Academic ORB research finds that opening-range behavior and volatility state can condition intraday returns, but also shows that ORB profitability can be unstable across periods. A newer 2026 ORB retest study documents associations between opening-range size and subsequent move magnitude while explicitly treating them as descriptive. Recent preregistered ORB work also emphasizes that apparently attractive breakout effects can disappear under realistic costs.

Sources:
- https://www.sciencedirect.com/science/article/pii/S1544612312000438
- https://swopec.hhs.se/umnees/abs/umnees0861.htm
- https://doi.org/10.2139/ssrn.6745958
- https://doi.org/10.2139/ssrn.7428398
- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5198458

These sources motivate a bounded test of opening-range volatility context, not a claim that ORB itself is profitable in NIFTY options.

## Frozen feature construction

For current date t:
- Opening range window = NIFTY bars from 09:15 through 09:29 inclusive.
- Opening-range high = maximum high in that 15-minute window.
- Opening-range low = minimum low in that 15-minute window.
- Opening-range width ratio = (opening-range high − opening-range low) / prior completed session high-low range.
- The regime is classified using the last 60 valid opening-range width ratios strictly before the current date:
  - LOW_OPEN_RANGE: below empirical 33.333rd percentile.
  - MID_OPEN_RANGE: 33.333rd to below 66.667th percentile.
  - HIGH_OPEN_RANGE: at or above 66.667th percentile.
- Current opening-gap direction = sign(current 09:15 open / previous 15:10 close − 1).
- Zero gap = no trade.
- Regime state is complete by 09:30; entry remains 09:31.

This is deliberately different from:
- raw opening-gap magnitude (Phase 44);
- first-15-minute direction confirmation (Phase 45);
- prior close location/range regimes (Phases 46–50);
- prior candle body conviction (Phase 56);
- same-session IV surface screens (Phases 52–55).

## Frozen execution

- FOLLOW_OPEN and FADE_OPEN.
- Entry 09:31 IST option open.
- Exits 10:30 and 15:10 IST option close.
- One-lot 200-point ATM directional debit spread.
- ATM = nearest ₹50 strike to 09:30 NIFTY close.
- Execution expiry = nearest NIFTY expiry on/after current trading date.
- Historical NIFTY lot sizes.
- Existing Paytm Money/NSE/statutory charges.
- Base slippage ₹0.20; Stress ₹0.40 per option-price unit/order.

## Discovery matrix and controls

3 opening-range states × 2 mappings × 2 exits = 12 true cells.

Five fixed state-permutation null seeds: 101, 202, 303, 404, 505. Nulls permute only the prior-only opening-range regime labels across eligible dates, leaving current-day gap direction and all execution prices unchanged.

## Data gates

- ≥95% post-warm-up opening-range feature eligibility.
- ≥95% prior-session range completeness.
- ≥95% opening-range 09:15–09:29 bar completeness.
- ≥95% deterministic expiry mapping.
- Zero prior-information violations.
- ≥95% execution coverage in every true cell.
- Full Base/Stress accounting reconciliation.

## Promotion gate

Both Base and Stress:
- mean weekly net ≥₹5,000;
- median weekly net ≥₹5,000;
- positive-week rate ≥70%;
- execution coverage ≥95%;
- clean accounting.

No WFA/OOS unless at least one frozen true cell clears the complete gate in both friction regimes.

## Stop rule

No post-result change to the opening-range window, ratio definition, 60-session history, tercile boundaries, gap mapping, entry, exits, spread width, expiry rule, or cost model.
