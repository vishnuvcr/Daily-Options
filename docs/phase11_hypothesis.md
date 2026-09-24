# Phase 11 — Breakout/Pullback with Option-OI Confirmation

## Research question

Can an intraday BANKNIFTY breakout that fails a first impulse, pulls back toward the structural break level, and then reclaims it with supportive option OI produce a cost-adjusted, walk-forward-validated edge?

## External evidence motivating the family

A September 2026 SSRN working paper tests intraday break-of-structure / change-of-character events in NIFTY 50 options and reports that PE-minus-CE OI differentials around breaks are strongly associated with break direction after multiple-testing correction. This is treated as a hypothesis lead, not as proof of profitability. Source: https://papers.ssrn.com/sol3/Delivery.cfm/7394780.pdf?abstractid=7394780&mirid=1

The public 1-minute index/options dataset used here documents BANKNIFTY 1-minute spot and option bars with strike, option type, expiry and open interest. It is CC-BY-NC-4.0 and research-only. Source: https://huggingface.co/datasets/thetrademarkk/india-index-options-1m

## Fixed pre-registration

64 variants:
- opening range: 5 / 15 minutes;
- breakout distance: 0.05% / 0.10%;
- pullback tolerance: 0.02% / 0.05%;
- entry gate: 09:45 / 10:00 IST;
- maximum holding: 15 / 30 minutes;
- risk profile: 20% stop + 50% target / 30% stop + 80% target.

The strategy always trades the next available expiry, uses one-strike defined-risk debit spreads, and uses the BANKNIFTY option chain for OI confirmation. The pullback/reclaim observation window is fixed at 10 one-minute bars after the initial breakout.

## Information barrier

Signals use completed spot bars and option OI observations at or before the signal timestamp. Execution is the next minute. Absolute strikes and expiry are fixed at entry.

## Execution and costs

- Base slippage: 0.20 premium points per leg.
- Stress slippage: 0.40 premium points per leg.
- Paytm Money brokerage/statutory/exchange charges come from the repository cost model.
- Within-bar stop/target collisions resolve in favor of the stop.
- Historical BANKNIFTY lot size is taken from the repository contract map.

## Promotion gate

Preliminary: mean active-day net >= Rs 1,000/lot for at least one variant.
Formal: positive untouched-test expectancy, at least one untouched test window >= Rs 1,000/lot/day, and no material collapse under doubled slippage.

No variant will be promoted from an in-sample or preliminary leaderboard alone.
