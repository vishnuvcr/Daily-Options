# Phase 33 — Dealer Gamma Exposure Proxies

## Status
**PREREGISTERED — numerical testing not yet started.**

## Research question
Does prior-session NIFTY option gamma positioning, measured from expiry/strike-level open interest and option-implied volatility, identify a repeatable intraday regime in which an opening directional debit-spread strategy can produce at least ₹5,000 net per completed trading week after Base and Stress transaction costs?

## Rationale
Dealer gamma is a materially different information family from Phase 32's local skew/smile shape. The literature links gamma exposure and hedging demand to intraday price dynamics, but the sign of an aggregate "dealer GEX" is an inventory assumption rather than a mathematical property of option gamma. The experiment therefore makes the sign convention explicit, freezes it before numerical testing, and separately records sign-agnostic gamma concentration diagnostics.

## Aims
1. Reconstruct prior-session NIFTY gamma exposure from the pinned option/OI cache.
2. Test whether gamma-regime state predicts opening-gap continuation versus reversal.
3. Test whether the distance to the gamma-flip and concentration of gamma around ATM add information beyond aggregate GEX.
4. Quantify economic performance after the existing Paytm Money/NSE/statutory cost model and Base/Stress slippage.
5. Compare true cells against five full-panel null permutations.

## Frozen population and information timing
- Underlying: NIFTY 50.
- Study window: 2021-07-01 through 2026-08-31, matching the preceding phases.
- Signal timestamp: **prior completed NIFTY session close**.
- OI snapshot: the **last available option observation on the prior NIFTY session**, never current-session OI.
- Option chain: all available NIFTY expiries with positive OI and valid strike/option type, subject to a fixed ±1,500-point moneyness window around prior close.
- No current-session option OI or volume enters the signal.
- Strict no-lookahead barrier: signal timestamp must be <= prior session close; entry is next-session 09:31.

## Gamma construction
For each option:
- Compute Black-Scholes gamma using prior-session close, strike, time-to-expiry, implied volatility from the stored option close, r=0 and q=0.
- Contract gamma contribution is scaled by OI and the current historical NIFTY lot size.
- The preregistered dealer-inventory proxy uses the conventional sign contract: **calls contribute +GEX and puts contribute -GEX**. This is explicitly an assumption, not an intrinsic property of gamma.
- Report the sign-reversed aggregate as an audit diagnostic only; it is not a post-result alternative.
- Net GEX is the sum across the fixed chain window.

Derived features:
1. **GEX_Z:** prior-only 60-session z-score of net GEX.
2. **FLIP_DISTANCE_Z:** prior-only 60-session z-score of the absolute distance between prior spot and the zero-GEX/root level, signed by whether spot is above or below the root.
3. **ATM_GEX_SHARE_Z:** prior-only 60-session z-score of absolute ATM ±2-strike gamma contribution divided by absolute total GEX.

The zero-GEX level is calculated only when a sign change exists across the fixed strike grid. If no root exists, that session is feature-ineligible for FLIP_DISTANCE_Z; no interpolation across missing roots is permitted.

## Frozen strategy rule
The signal is evaluated at the prior close and acted on at next-session 09:31.

- If the aggregate GEX sign is **negative**, the registered dealer-hedging hypothesis is **gap FOLLOW**.
- If aggregate GEX sign is **positive**, the registered hypothesis is **gap FADE**.
- For FLIP_DISTANCE_Z and ATM_GEX_SHARE_Z, the direction is still determined only by the sign of aggregate GEX; the feature controls whether the state is sufficiently extreme.
- Opening gap = next-session 09:15 open relative to prior close.
- FOLLOW means trade in the gap direction.
- FADE means trade against the gap.
- If the opening gap is zero or unavailable, no trade.

Instrument: one-lot ATM directional debit spread on the next valid NIFTY expiry, with fixed ±200-point wing. The long leg is the ATM option in the chosen direction and the short leg is the same-side 200-point OTM option.

## Frozen discovery grid
- Features: GEX_Z, FLIP_DISTANCE_Z, ATM_GEX_SHARE_Z
- Absolute thresholds: **0.75 and 1.25**
- Exits: **10:30 and 15:10 IST**
- True cells: **3 × 2 × 2 = 12**
- Null seeds: **101, 202, 303, 404, 505**
- Five complete-panel permutations per true cell and friction regime. Each seed applies one common row permutation jointly to `net_gex` and all three registered gamma-state features, preserving their cross-sectional relationships while destroying their time alignment to the trade date.
- Base slippage: ₹0.20 per option-price unit per order.
- Stress slippage: ₹0.40 per option-price unit per order.
- Existing date-aware Paytm Money/NSE/statutory cost model.
- Historical NIFTY lot sizes.
- No stop, target, adjustment, roll, threshold change or post-result strike optimization.

## Data gates
Before any P&L:
1. >=95% prior-session OI/price coverage for feature-eligible sessions.
2. >=95% expiry/strike coverage for the fixed chain window.
3. >=95% executable entry/exit coverage for every true cell.
4. Zero prior-positioning/lookahead violations.
5. Valid gamma and IV inputs for >=95% of required feature rows.
6. Five null seeds complete for every cell/friction.

## Economic promotion gate
A cell must satisfy **all** conditions in both Base and Stress:
- mean weekly net P&L >= ₹5,000;
- median weekly net P&L >= ₹5,000;
- positive-week rate >=70%;
- execution coverage >=95%;
- no unresolved data-quality violation;
- null-control comparison does not indicate that the true result is inferior to the matched null family.

No WFA/OOS is authorized unless a frozen cell clears this gate.

## Statistical analysis
Report:
- total/weekly net P&L;
- mean, median and percentile weekly P&L;
- positive-week rate;
- trade count and active weeks;
- max drawdown and ulcer index;
- expectancy and profit factor;
- raw gross P&L;
- slippage and statutory/brokerage costs;
- 1,000-draw weekly bootstrap intervals;
- true-versus-null differences;
- year/regime/session breakdowns;
- cost and slippage sensitivity;
- feature coverage and signal concentration.

No model selection based on bootstrap outcomes is allowed.

## Stop rule
If all 12 cells fail, Phase 33 closes. No gamma threshold, wing, exit or sign convention may be tuned after seeing results. The next family must be materially distinct.

## Deliverables
Plan, literature review, source manifest, engine, unit tests, manual GitHub Actions workflow, data-gate report, Base/Stress ledgers, null controls, figures, final manuscript, status log and error log.
