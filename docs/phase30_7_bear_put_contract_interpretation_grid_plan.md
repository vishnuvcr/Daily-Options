# Phase 30.7 — Bear Put bounded contract-interpretation grid

## Purpose

Convert the source's remaining unresolved mechanics into an explicit, pre-registered interpretation matrix. This is not a claim that any interpretation is the creator's exact rule. No result-driven selection is permitted.

## Evidence barrier

Primary source: Equity Income video `IpCuGEDxF1k`, transcript SHA-256 `a79b1e15c1f10fe053ffc0ba4999a8675cd26202ce70b27459328210d809c9a6`.

Resolved source facts:
- classic bear put spread: buy higher-strike put, sell lower-strike put;
- worked example: 26,300 long put / 26,200 short put;
- bearish entry follows resistance plus crack/gap-down;
- adverse continuation can be adjusted by selling one additional put at the existing short strike, converting the 1:1 spread to 1:2;
- if the market reverses after the added short, square off the newly sold put;
- source says not to rush the adjustment.

Unresolved source facts remain explicitly experimental: exact resistance mathematics, exact crack/gap threshold, expiry selection, exact entry clock, universal strike rule, debit filter, stop, profit lock, time exit and adjustment timing.

## Phase 30.6 feasibility result used only as an information-independent filter

The preregistered 54-cell spot-only coverage test produced 45 definitions with at least 20 signal weeks. This is a feasibility gate, not an economic ranking. The eligible definitions have 33–53 signal weeks.

All 45 eligible definitions are retained.

## Frozen Phase 30.7 dimensions

### A. Entry definitions — 45 cells

Exactly the 45 definitions from Phase 30.6 with signal_weeks >= 20, preserved verbatim:
- lookback: 30 / 60 / 120 minutes;
- resistance touch tolerance: 0.10% / 0.20% / 0.40%;
- trigger: close-crack or gap-down open;
- threshold: 0.10% / 0.20% / 0.40% for crack, and 0.20% / 0.50% / 1.00% for gap-down.

No definition is added or removed after option P&L is observed.

### B. Expiry selection — 2 cells

1. nearest listed weekly NIFTY expiry after the signal;
2. second-nearest listed weekly NIFTY expiry after the signal.

NIFTY weekly options use Tuesday expiry under the current NSE framework; a Tuesday holiday rolls to the previous trading day. Historical contract mapping must use actual listed expiries, not calendar assumptions. NSE documents this Tuesday framework and the September-2025 transition. 

### C. Strike construction — 2 cells

1. **ATM-consecutive:** long PE = nearest listed strike at/above spot; short PE = immediately lower listed strike.
2. **ATM-minus-one:** long PE = immediately higher listed strike than the nearest-at/below spot strike; short PE = the next lower listed strike.

These are registered mathematical interpretations of the source's 26,300/26,200 consecutive-strike example, not claims about an unstated universal rule.

### D. Adjustment trigger — 3 cells

After entry, if the underlying gaps/opens above the entry resistance:
- +200 points;
- +250 points;
- +300 points.

The source explicitly uses a roughly 200–300 point gap-up illustration. The exact threshold is therefore treated as a bounded interpretation dimension.

Adjustment is delayed until the registered observation interval below; no immediate same-bar adjustment is allowed.

### E. Adjustment wait — 2 cells

- first eligible 15-minute observation after the gap-up;
- first eligible 30-minute observation after the gap-up.

If spot has already reversed back to/below the entry resistance at the observation, no ratio adjustment is made.

If adjustment occurs, sell one additional PE at the original short strike, producing a 1:2 ratio, exactly matching the source example.

### F. Risk/exit convention — 3 cells

1. **Debit-stop / 50%-profit:** stop at 1.0× initial debit loss; lock/exit at 50% of maximum spread value.
2. **Debit-stop / 75%-profit:** same stop; exit at 75% of maximum spread value.
3. **Debit-stop / expiry:** same stop; otherwise hold to expiry settlement/last executable exit.

The fixed 1.0× debit stop is an explicit research convention, not source evidence. It is required to make the strategy executable and is frozen before P&L. No result-driven stop tuning is permitted.

### G. Time exit — 2 cells

For non-target/non-stop positions:
- exit at Monday 15:00 IST before Tuesday expiry;
- exit at Tuesday 15:00 IST / final executable pre-expiry mark.

If Tuesday is a market holiday, use the actual preceding expiry day.

## Grid size

45 × 2 × 2 × 3 × 2 × 3 × 2 = **6,480 registered cells**.

The full matrix is intentionally registered before any P&L. Any implementation may vectorize equivalent dimensions, but no subset may be selected from economic results.

## Execution and cost rules

- Underlying signal uses information available strictly before/at the registered signal bar.
- Option entry uses the next available minute after signal detection.
- Adjustment uses the next available minute after the registered observation.
- Missing decision/fill quotes create a no-trade or unfilled-leg record according to the registered execution policy; later quotes may not silently substitute.
- Historical NIFTY lot size: 75 through the 2025-12-30 expiry; 65 from 2026-01-06 onward, based on NSE's October 2025 revision and transition.
- Brokerage/transaction charges use the date-aware Paytm Money/NSE cost model already validated in prior phases.
- Base slippage: ₹0.20 premium points/order.
- Stress slippage: ₹0.40 premium points/order.

## Information barrier

No option premium, P&L, drawdown, win rate or capital result may influence the definition of the 6,480 cells. Source/spot feasibility filtering is completed before option-level economic testing.

## Statistical analysis

For every registered cell and friction regime:
- completed trades/weeks;
- mean/median weekly net;
- profitable-week rate;
- profit factor;
- max drawdown;
- 5% weekly loss quantile and expected shortfall;
- execution coverage;
- capital/margin peak;
- transaction-cost share of gross P&L.

The ₹5,000/week promotion gate remains unchanged:
- mean weekly net >= ₹5,000;
- median weekly net >= ₹5,000;
- profitable-week rate >=70%;
- >=20 completed weeks;
- >=80% execution coverage.

A cell failing the gate is not tuned after the fact.

## Advancement

Phase 30.7 first performs deterministic contract/coverage validation across the 6,480 cells. If implementation and contract joins pass, the numerical engine may run the complete Base/Stress matrix. If the entire family fails the promotion gate, Bear Put is retired without WFA/OOS tuning. If any cells pass, only then may the next preregistered walk-forward phase open.

## Status

**OPEN — interpretation grid frozen; numerical execution authorization follows implementation/contract audit.**


## Final status — 2026-09-26

The complete Base/Stress execution finished in workflow run **36233110210** with 18/18 shard jobs successful and a successful 6,480-cell aggregate audit. Both friction regimes had **0/6,480 cells pass** the frozen ₹5,000/week promotion gate.

**Phase status: CLOSED — RETIRED.**

See `reports/phase30_7_bear_put_final_result.md` for the audited result. No WFA/OOS branch is authorized for Bear Put.
