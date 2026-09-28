# Phase 41 — NIFTY Option-Gamma Concentration × Opening-Gap Direction

## Status
PREREGISTERED — engineering build; numerical execution pending.

## Research question
Does prior-session OI-weighted option-gamma concentration around NIFTY ATM condition whether the next session's opening gap continues or reverses strongly enough to generate at least ₹5,000 net per completed trading week after realistic costs?

## Aims
1. Build a reproducible prior-session gamma-concentration measure from public exact-expiry NIFTY option data.
2. Keep all signal inputs at or before the previous session's 15:10 information cutoff.
3. Test whether high versus low gamma concentration changes opening-gap follow-through/reversal.
4. Quantify the effect through fixed one-lot 200-point debit spreads under Base and Stress friction.
5. Compare true cells with five fixed permutation-null controls.

## Literature rationale
Research links option gamma exposure and hedging demand to short-horizon return momentum/reversal. Soebhag reports net gamma exposure predicts future equity returns and attributes the relation to hedge rebalancing; Barbon & Buraschi document intraday momentum/reversal conditional on gamma imbalance and liquidity; recent preregistered GEX work also stresses that strike-local “gamma wall” claims require control-matched falsification. Phase 41 therefore tests **gamma concentration**, not a proprietary dealer-sign assumption, and treats the result as a hypothesis test rather than proof of dealer positioning.

## Study window and source
- 2021-07-01 through 2026-08-31.
- NIFTY index + exact-expiry option partitions from TradeMarkk revision 51ca58c.
- India/Kolkata timestamps.
- Persistent cache: data/cache/phase41_trademarkk.

## Frozen prior-session gamma feature
For each current session t, use the previous completed NIFTY session d:
- prior spot = NIFTY 15:10 close on d;
- ATM = deterministic nearest ₹50 using half-up rounding;
- expiry = nearest NIFTY expiry strictly after d;
- strike universe = ATM ±₹500 in ₹50 increments;
- core universe = ATM ±₹100;
- for each CE/PE strike, use the latest valid positive option observation at or before 15:10 on d;
- require positive OI and positive close;
- solve Black-Scholes implied volatility with r=0, q=0 and time to expiry-day 15:30 IST;
- gamma = φ(d1)/(S × IV × sqrt(T));
- gamma mass = OI × gamma × historical lot size;
- GAMMA_CONCENTRATION = core-window gamma mass / full-window gamma mass.

Observation completeness is measured explicitly over the required CE/PE strike legs; missing rows are not imputed.

## Frozen standardization
- GAP direction is current 09:15 NIFTY open / previous 15:10 close − 1.
- GAMMA_CONCENTRATION_Z uses the strictly prior 60 valid GAMMA_CONCENTRATION observations.
- Missing observations never enter the 60-observation history and are never forward-filled.
- HIGH_GAMMA_CONCENTRATION: z ≥ +0.75.
- LOW_GAMMA_CONCENTRATION: z ≤ −0.75.
- Otherwise no trade.

## Frozen execution
- FOLLOW_GAP: positive gap → CALL debit spread; negative gap → PUT debit spread.
- FADE_GAP: positive gap → PUT; negative gap → CALL.
- Entry: 09:31 option open.
- Exit: 10:30 or 15:10 option close.
- One NIFTY lot.
- 200-point defined-risk debit spread.
- Current-session expiry: nearest NIFTY expiry on/after the trading date.
- Historical lot sizes.

## Discovery matrix
2 gamma states × 2 gap mappings × 2 exits = 8 true cells.
Null seeds: 101, 202, 303, 404, 505.
Nulls permute only prior-only gamma-concentration z values across feature-eligible dates; same-day gap direction and execution prices remain fixed.

## Data gates
- ≥95% post-warm-up feature eligibility.
- ≥95% prior-session chain coverage.
- ≥95% CE/PE observation completeness in both core and total windows.
- zero prior-information violations.
- deterministic expiry/strike/lot mapping.
- ≥95% execution quote coverage for each true cell.
- accounting reconciliation.

## Cost model
- Paytm Money brokerage ₹20/order.
- Date-aware option-sale STT.
- Exchange transaction charge.
- SEBI turnover fee.
- Stamp duty on buys.
- GST.
- Base slippage ₹0.20 per option-price unit/order.
- Stress slippage ₹0.40.
- Historical NIFTY lot sizes.

## Statistical analysis
Primary:
- total net;
- mean weekly net;
- median weekly net;
- positive-week rate;
- profit factor;
- worst week/trade;
- maximum drawdown;
- raw gross, slippage, transaction/statutory costs;
- execution coverage;
- bootstrap mean-weekly interval;
- true-versus-null mean comparison;
- year/regime summaries.

## Promotion gate
In BOTH Base and Stress:
- mean weekly net ≥₹5,000;
- median weekly net ≥₹5,000;
- positive-week rate ≥70%;
- execution coverage ≥95%;
- accounting reconciliation passes.

No WFA/OOS unless at least one true cell clears in both frictions. No result-specific tuning is permitted.

## Stop rule
No post-result changes to chain/core widths, 60-valid-observation lookback, ±0.75 thresholds, gamma formula, IV construction, expiry rule, gap mapping, entry, exits, spread width, costs or lot sizing.