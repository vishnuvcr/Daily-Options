# Phase 58 — 09:15–09:29 ATM Option Volume Imbalance × Opening-Gap Direction

## Research question

Does the imbalance between ATM call and put trading volume accumulated during the first 15 minutes of the NIFTY session condition whether the opening move continues or reverses strongly enough to generate at least ₹5,000 net per completed trading week after realistic costs?

## Literature rationale

Academic research finds that option-market order imbalance can contain information about subsequent index or stock returns, including immediately after the market opens. Recent work also finds predictive power in short intraday option order-imbalance windows. This phase uses the closest reproducible public-data proxy available in the pinned dataset: **ATM call volume versus ATM put volume**, because the dataset does not provide aggressor-side trade flags needed for true signed order flow.

Sources:
- https://www.sciencedirect.com/science/article/pii/S1059056021002367
- https://onlinelibrary.wiley.com/doi/abs/10.1002/fut.22301
- https://pubsonline.informs.org/doi/10.1287/mnsc.2019.3529
- https://arxiv.org/abs/2201.09319
- https://onlinelibrary.wiley.com/doi/full/10.1111/jofi.12380

These studies motivate the hypothesis only. Their order-imbalance definitions are not identical to this public-data volume proxy.

## Frozen feature construction

For current trading date t:
- Reference spot = NIFTY 09:30 close.
- ATM strike = nearest ₹50 using deterministic half-up rounding.
- Feature expiry = nearest NIFTY expiry strictly after the current trading date.
- During 09:15–09:29 inclusive, sum option volume for:
  - ATM CE at the feature expiry;
  - ATM PE at the feature expiry.
- Define VOLUME_IMBALANCE = (CE_volume − PE_volume) / (CE_volume + PE_volume).
- Zero denominator or missing side = feature invalid.
- Use the last 60 valid VOLUME_IMBALANCE observations strictly before the current date.
- LOW_VOLUME_IMBALANCE: below empirical 33.333rd percentile.
- MID_VOLUME_IMBALANCE: 33.333rd to below 66.667th percentile.
- HIGH_VOLUME_IMBALANCE: at or above 66.667th percentile.
- Current opening-gap direction = sign(current 09:15 open / prior completed 15:10 close − 1).
- Zero opening gap = no trade.

The volume feature is complete by 09:30; entry remains 09:31.

## Important interpretation constraint

This is **not** true signed order imbalance. It is a put-vs-call volume imbalance proxy. No buyer/seller aggressor classification is inferred from volume alone.

## Frozen execution

- FOLLOW_OPEN and FADE_OPEN.
- Entry 09:31 IST option open.
- Exits 10:30 and 15:10 IST option close.
- One-lot 200-point ATM directional debit spread.
- ATM = nearest ₹50 to 09:30 NIFTY close.
- Execution expiry = nearest NIFTY expiry on/after current trading date.
- Historical NIFTY lot sizes.
- Existing Paytm Money/NSE/statutory charges.
- Base slippage ₹0.20; Stress ₹0.40 per option-price unit/order.

## Discovery matrix and controls

3 volume-imbalance states × 2 mappings × 2 exits = 12 true cells.

Five fixed state-permutation null seeds: 101, 202, 303, 404, 505. Only prior-only volume-imbalance regime labels are permuted across eligible dates, preserving same-day opening direction and execution prices.

## Data gates

- ≥95% post-warm-up volume-feature eligibility.
- ≥95% ATM CE and PE volume completeness in the 09:15–09:29 window.
- ≥95% feature-expiry mapping.
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

No WFA/OOS unless at least one frozen true cell clears the complete gate in both frictions.

## Stop rule

No post-result change to the ATM strike, 09:15–09:29 window, volume definition, 60-session history, tercile boundaries, feature expiry, execution expiry, gap mapping, entry, exits, spread width, or cost model.
