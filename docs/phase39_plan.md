# Phase 39 — NIFTY Option-Implied vs Realized Opening-Move Dislocation

## Status
PREREGISTERED — engineering build; numerical execution pending.

## Research question
Does the size of the NIFTY 09:15–09:29 realized opening move relative to the contemporaneous 09:30 ATM option-implied 15-minute move contain a reproducible short-horizon directional edge after realistic trading costs?

## Aims and objectives
1. Convert 09:30 ATM option prices into a contemporaneous implied-volatility estimate without using information after 09:30.
2. Compare the realized first-15-minute opening move with the option-implied 15-minute move through a dimensionless ratio.
3. Standardize that ratio only against the previous 60 completed NIFTY sessions.
4. Test continuation and fade mappings through a fixed one-lot 200-point debit spread.
5. Quantify realistic Paytm Money/NSE/statutory charges, Base/Stress slippage, execution coverage and accounting reconciliation.
6. Use five fixed permutation null controls to test whether any apparent state effect is stronger than date-randomized controls.

## Literature basis
Prior NIFTY studies report information content in implied volatility relative to realized/historical volatility. Research on pre-opening index options also motivates testing whether option-implied volatility information can contain short-horizon price information. Phase 39 translates that literature into a tightly time-bounded opening dislocation ratio rather than copying an existing trading rule.

Full references: docs/phase39_literature_review.md

## Study window and source
- Study period: 2021-07-01 through 2026-08-31.
- Underlying and options source: thetrademarkk/india-index-options-1m, revision 51ca58c.
- Persistent cache: data/cache/phase39_trademarkk.
- NIFTY timestamps are normalized to Asia/Kolkata.
- Option files are exact-expiry partitions.

## Frozen information timing
1. Session opening price = NIFTY 09:15 bar open.
2. Realized opening return = (NIFTY 09:29 close − NIFTY 09:15 open) / NIFTY 09:15 open.
3. ATM reference = nearest ₹50 to the NIFTY 09:30 close.
4. Signal option expiry = nearest NIFTY expiry strictly after the trade date. Same-day expiry is excluded from the signal IV calculation.
5. ATM CE and PE option observations = latest available 09:30 bar close for that expiry/strike.
6. Black-Scholes IV uses r=0, q=0 and time to the expiry-day 15:30 IST close.
7. ATM IV = simple average of valid CE and PE IV.
8. Implied 15-minute move percentage = ATM IV × sqrt(15/390).
9. MOVE_RATIO = abs(realized opening return) / implied 15-minute move percentage.
10. MOVE_RATIO_Z = strictly prior 60-session mean/std standardized MOVE_RATIO.
11. No option observation after 09:30, no later NIFTY bar and no current-session exit data enters the signal state.

## Frozen signal states
- HIGH_DISLOCATION: MOVE_RATIO_Z >= +0.75.
- LOW_DISLOCATION: MOVE_RATIO_Z <= −0.75.
- Otherwise: NO_TRADE.
- Direction: sign of the same-session 09:15→09:29 NIFTY return. Zero direction is NO_TRADE.

## Frozen execution
- CONTINUE: bullish early return → long ATM CE / short CE at ATM+₹200; bearish early return → long ATM PE / short PE at ATM−₹200.
- FADE: opposite directional spread.
- Entry: 09:31 option open.
- Exits: 10:30 option close and 15:10 option close.
- One NIFTY lot.
- Historical NIFTY lot sizes.
- No stop, target, adjustment, roll, leverage change or discretionary exclusion.

## Frozen discovery matrix
- HIGH_DISLOCATION × CONTINUE × 10:30.
- HIGH_DISLOCATION × CONTINUE × 15:10.
- HIGH_DISLOCATION × FADE × 10:30.
- HIGH_DISLOCATION × FADE × 15:10.
- LOW_DISLOCATION × CONTINUE × 10:30.
- LOW_DISLOCATION × CONTINUE × 15:10.
- LOW_DISLOCATION × FADE × 10:30.
- LOW_DISLOCATION × FADE × 15:10.
- Total: 8 true cells.

## Null controls
Seeds: 101, 202, 303, 404, 505.
For each seed, permute only the prior-only MOVE_RATIO_Z values across feature-eligible dates while keeping the same-day opening-return direction and all execution prices unchanged. Null states are recomputed from the permuted z-scores.
Nulls are diagnostic falsification controls and cannot be used for parameter selection.

## Data and integrity gates
PASS requires:
- at least 95% of post-warm-up sessions are feature-eligible;
- at least 95% option-IV input completeness after the 60-session warm-up;
- zero prior-information violations;
- deterministic expiry/strike/lot mapping;
- at least 95% execution quote coverage for every true cell;
- Base and Stress accounting reconciliation.
A failure closes the phase DATA-LIMITED and authorizes no economic inference.

## Cost model
- Paytm Money brokerage ₹20 per order.
- Date-aware option-sale STT.
- Exchange transaction charge.
- SEBI turnover fee.
- Stamp duty on buys.
- GST on applicable services.
- Base slippage ₹0.20 per option-price unit/order.
- Stress slippage ₹0.40 per option-price unit/order.
- Historical NIFTY lot sizes by expiry date.

## Primary statistical analysis
- weekly net P&L;
- mean weekly net;
- median weekly net;
- positive-week rate;
- execution coverage;
- total net, worst trade, worst week and maximum drawdown;
- raw gross P&L, slippage and transaction/statutory costs;
- null-control distributions and true-vs-null mean differences;
- yearly and volatility-regime summaries;
- accounting residuals.

## Promotion gate
A true cell is promotable only if, in BOTH Base and Stress:
- mean weekly net ≥ ₹5,000;
- median weekly net ≥ ₹5,000;
- positive-week rate ≥70%;
- execution coverage ≥95%;
- accounting reconciliation passes;
- no unresolved data-quality violation.
No WFA/OOS is authorized until the discovery gate clears.

## Stop rule
No post-result changes to the 09:15–09:29 interval, 09:30 IV observation, strictly-next-expiry rule, sqrt(15/390) scaling, 60-session lookback, ±0.75 thresholds, CONTINUE/FADE mappings, 09:31 entry, 10:30/15:10 exits, 200-point width or cost model.

## Deliverables
Preregisration, literature review, source manifest, Python engine, unit tests, manual GitHub Actions workflow, data gate, Base/Stress ledgers, null controls, execution coverage, final manuscript, reproducibility appendix and status/error updates.