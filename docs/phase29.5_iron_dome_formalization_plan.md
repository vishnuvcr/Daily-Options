# Phase 29.5 — NIFTY Iron Dome source-fidelity formalization and contract/lot readiness

## Purpose
Freeze a small, source-anchored set of deterministic interpretations for the two Equity Income Iron Dome videos, correct for the current NIFTY Tuesday-expiry regime, and verify historical contract/lot assumptions before opening numerical testing.
This phase produces no P&L.

## Current-rule translation
NIFTY weekly index options expire Tuesday. The expiry-day change from Thursday to Tuesday took effect in September 2025. The two target videos are dated April 30, 2026 and May 2, 2026, so their calendar examples are already post-change and must not be shifted back to Thursday.
For a normal Tuesday expiry, the source's stated 2–4 trading-session holding concept maps to deterministic entry candidates: T-4 Wednesday, T-3 Thursday, T-2 Friday. Exchange holidays override weekday labels through the exchange calendar.

## Frozen source facts
- NIFTY weekly Iron Fly / Iron Dome core.
- Maximum two adjustments.
- Explicit 60% adjustment mark.
- Illustrative 200-point balanced wings.
- 2–4 trading-session holding concept.
- Directional/deeper-ITM adjustment concept.
- One-strike-inside adjustment example.
- Monday 09:30 adjustment example and near-close/theta-decay example.
- 15:00 expiry-day illustration.

## Bounded formalization family
Entry: T-4, T-3, or T-2 trading sessions before Tuesday expiry; first formalization uses 09:30.
Initial structure: weekly iron fly / short-straddle core; 200-point protective wing width; 1:1:1:1 ratio; bearish/source-anchored center operationalized as one 50-point strike above ATM. This is a formalization, not a claim of hidden source precision.
Trigger A: WING_60 = underlying moves 60% of the 200-point wing distance, i.e. 120 points, toward the challenged side.
Trigger B: RISK_60 = running position loss reaches 60% of the initial defined maximum loss.
Adjustment A: RECENTER_BOTH = close the current short CE/PE pair and recenter the short straddle at current ATM/rounded strike, rebuilding 200-point wings with 1:1:1:1 ratio.
Adjustment B: ONE_STRIKE_INSIDE = move the challenged short leg one 50-point strike deeper ITM while preserving the rest of the defined-risk structure.
Maximum adjustments: 2; the second is allowed only if the registered trigger reoccurs.
Exit: fixed 15:00 on expiry day for the initial numerical study. Earlier discretionary loss exits are excluded from the first pass.

## Frozen matrix
3 entries × 2 triggers × 2 adjustment styles = 12 preregistered cells.
Results may not be used to choose a trigger or adjustment definition inside Phase 29.5.

## Contract/lot gate
- Exact NIFTY weekly expiry contract.
- Date-valid lot size.
- Tuesday expiry unless exchange holiday moves it to prior trading day.
- Weekly strike interval 50 points.
- Every required leg present on entry, adjustment and exit dates.
- No bid/ask inference from OHLC.
The repository historical lot schedule and NSE revision show NIFTY at 65 lots for the 2026 candidate expiries; the machine gate uses date-indexed logic rather than a current-size constant.

## Execution-cost gate
- Paytm Money brokerage baseline versioned.
- NSE statutory/exchange charges date-aware.
- Base and Stress slippage explicit per leg.
- No future information in signals or adjustments.
- If bid/ask is unavailable, the execution model must be explicitly labelled as an OHLC-derived proxy, not observed spread data.

## Weekly economic objective for Phase 30

The current Equity Income promotion target is **₹5,000 NET per completed trading week** at the frozen reference strategy position size. The retired ₹1,000-per-day rule is not used for Phase 30.

Phase 30 must report:
- mean weekly net ≥ ₹5,000 on untouched OOS weeks;
- median weekly net ≥ ₹5,000 on untouched OOS weeks;
- profitable-week rate ≥70%;
- executed-week coverage ≥80% unless a source-frozen no-trade condition applies;
- Base and doubled-slippage Stress;
- worst week, weekly drawdown, expected shortfall/CVaR, profit factor and concentration;
- nested walk-forward selection followed by independent later-period OOS.

Hidden position scaling is prohibited: lot ratios, reference size, all four legs, costs and capital usage must be disclosed.

## Phase 30 opening criteria
All 12 cells must have deterministic rules, valid date-specific lot size, exact contract joins, no missing mandatory legs, and registered cost/slippage definitions.
Then Phase 30 can run weekly net P&L, profitable-week rate, median, worst week, drawdown, profit factor, expected shortfall/CVaR, capital efficiency, Base/Stress, nested WFA/OOS and later-period validation.

## Stop condition
Stop Phase 29.5 once the 12-cell matrix, contract/lot mapping and execution-readiness gate are machine-validated. No result-driven expansion is allowed.