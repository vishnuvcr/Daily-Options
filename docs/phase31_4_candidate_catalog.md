# Phase 31.4 candidate evidence matrix

| Family | Evidence | Main caveat | Data requirement | Decision |
|---|---|---|---|---|
| Global overnight gap -> India open | Cross-market studies find opening-gap predictability can be selective and depends on market sequence; recent 2026 work stresses time-aligned information barriers. | Predictability is not universal; must use only markets already closed before NSE open. | Global index/futures close + NIFTY open; calendar/time-zone map. | **TEST** |
| Opening-range breakout + defined-risk option translation | ORB has published evidence in intraday markets; 2025 NSE study evaluates 5/15/30-min variants. | Evidence is not NIFTY-options-specific and parameter mining is a major risk. | 1-min NIFTY + option chain, deterministic OR windows. | **TEST** |
| IV vs realized-volatility / VRP | Indian NIFTY literature documents IV/RV information; a 2026 NIFTY study reports positive VRP on 74.9% of days in its sample. | VRP can invert and is not automatically monetizable after costs; must model execution and tail risk. | Intraday option IV reconstruction + realized volatility. | **TEST** |
| OI/volume microstructure | Older Indian studies find OI/volume contain information; a 2026 NIFTY study reports no robust OOS advance-prediction from intraday OI repositioning. | Strong publication/data-mining risk; latest evidence argues against using OI repositioning as a direct forecast. | Intraday OI/volume by strike, strict lagging. | **TEST WITH NULLS** |
| Order imbalance / LOB | Indian microstructure evidence finds short-term return predictability from order imbalance in liquid stocks. | Current pinned dataset may not contain sufficient depth/order-book fields. | L1/L2 or high-quality trade/quote data. | **DATA GATE** |
| VIX/RV regime-conditioned defined-risk structures | NIFTY options literature supports volatility smile/tail-risk structure and IV/RV dynamics. | Regime conditioning can overfit quickly; must preregister finite cells and WFA. | India VIX + NIFTY options + realized vol. | **TEST** |

## Evidence notes

- Global gap research: the 2026 cross-index study explicitly aligns observations to what is available before each market opens and finds selective, market-dependent predictability rather than universal predictability. citeturn0search0turn0search13
- ORB: published research finds intraday ORB profitability in some markets; a 2025 NSE study specifically evaluates multiple ORB windows and volume thresholds on Indian data. This supports testing the mechanism, not assuming profitability. citeturn0search5turn0search11
- IV/RV: Indian NIFTY research finds information in implied volatility, while the 2026 VRP study reports a positive average VRP with meaningful inversion and tail asymmetry. This is a concrete hypothesis for a cost-aware test. citeturn0search16turn0search6
- OI/volume: multiple Indian studies report predictive information in OI/volume, but the 2026 intraday NIFTY study reports that its OI-repositioning signal failed genuinely held-out tests. Therefore this family must include explicit null tests and OOS validation. citeturn0search1turn0search3turn0search4
- Order imbalance: Indian evidence supports short-horizon information in order imbalance, but the required depth data may not exist in the pinned cache. citeturn0search15

## Preregistered finite grids

### A. Global gap
- Inputs: prior eligible global close-to-close returns, India pre-open gap, VIX/VIX-equivalent where available.
- Signal windows: fixed 0, 5, 15 minutes after open.
- Direction: continuation and fade are separate hypotheses.
- Option implementation: ATM debit spread first; no naked short option.
- No threshold chosen from test weeks.

### B. ORB
- OR windows: 5, 15, 30 minutes.
- Break condition: fixed multiples of opening-range width.
- Implementation: ATM/near-ATM debit spread with fixed expiry selection.
- Exit: fixed intraday time or fixed risk stop, preregistered.
- Volume filter: absent / 1.2x / 1.5x only if volume is available without leakage.

### C. IV/RV
- IV measure: ATM forward IV.
- RV measures: fixed realized-volatility estimators.
- Signal: IV-RV spread percentile using trailing history only.
- Implementation: defined-risk debit/credit structure matched to the sign of the spread.
- Tail-risk cap is mandatory.

### D. OI/volume
- Lagged OI change, lagged volume, put/call imbalance, price/OI joint states.
- Signals must use data completed before entry.
- Include permutation/null and shuffled-timestamp controls.
- No direct forecasting claim unless held-out improvement survives.

### E. VIX/RV regimes
- Regime variables fixed before testing: India VIX percentile, realized-vol percentile, trend state.
- Structure family fixed by regime.
- Finite grid only; WFA required before any OOS promotion.

## Advancement rule

A candidate proceeds to Phase 31.5 numerical testing only if:
1. deterministic mechanics are fully specified;
2. data coverage passes;
3. a finite grid is frozen;
4. costs/slippage are included;
5. the hypothesis is materially distinct from Phase 31.1;
6. the planned WFA/OOS protocol is written before running the grid.
