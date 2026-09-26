# Phase 30.9 — STRANGLE AIR DEFENSE SYSTEM: VIX source-resolution and bounded execution matrix

## Candidate

Video ID: `aRjY_O6U3nQ`  
Title: **Retail Option Sellers Need This First - STRANGLE AIR DEFENSE SYSTEM**

The public YouTube description says the video presents a VIX-based framework for estimating the expected NIFTY range for an expiry, discusses 1-sigma and 2-sigma ranges, uses the framework for short strangles and iron condors, and discusses when to adjust positions as price moves toward the strikes.

## Why this phase follows Phase 30.8

Phase 30.8 was source-blocked because essential fields could not be reconstructed from the publicly available encrypted transcript archive without the private decryption key.

This candidate has materially richer source-explicit execution evidence in the audited Python-extracted rule cards:
- underlying: NIFTY;
- short/sell entry action;
- 0.20 delta reference;
- out-of-the-money strike reference;
- premium-zone reference;
- 3:25 time reference;
- target exit approximately 5 minutes before expiry;
- adjustment language including add/hedge;
- width/expected-range references.

The remaining unresolved fields are entry day/time, exact expiry convention, exact adjustment trigger/quantity, stop convention, and capital convention. These are handled as a preregistered interpretation matrix rather than selected after P&L.

## Research questions

1. Does a VIX/expected-range short-strangle implementation produce non-negative and consistent weekly net P&L after realistic costs?
2. How sensitive is the result to nearest versus next weekly expiry?
3. Does source-explicit 0.20-delta construction behave differently from 1-sigma or 2-sigma expected-range construction?
4. Which explicitly bounded adjustment interpretations are executable without future-data leakage?
5. Does the source's 3:25 pre-expiry exit remain operationally reproducible under holiday-shifted expiry dates?
6. Does the candidate clear the fixed ₹5,000 net/completed-week promotion gate under both Base and Stress friction?

## Evidence classification

### SOURCE-EXPLICIT
- NIFTY underlying.
- Short/sell option-selling action.
- 0.20 delta.
- OTM strike language.
- 3:25 time reference.
- Approximate 5-minute-before-expiry exit.
- Adjustment concepts containing add/hedge.
- Premium-zone and width references.

### SOURCE-CORROBORATED
The public YouTube description corroborates VIX expected-range construction, 1-sigma/2-sigma framing, short strangles/iron condors, and adjustment when price approaches the strikes.

### UNSPECIFIED / INFERRED
- Entry day/time.
- Nearest vs next weekly expiry.
- Exact expected-range-to-strike mapping.
- Exact adjustment trigger and quantity.
- Stop-loss.
- Fixed capital convention.

## Bounded preregistered interpretation matrix

No parameter may be added after inspecting P&L.

Dimensions:

1. Entry time: 09:20, 10:00, 11:00 IST.
2. Expiry: nearest listed weekly expiry; next listed weekly expiry.
3. Strike construction:
   - A: source-explicit 0.20 absolute delta call + put.
   - B: 1-sigma VIX expected range.
   - C: 2-sigma VIX expected range.
4. Adjustment trigger:
   - A: spot reaches the short-strike level (touch).
   - B: spot reaches 90% of the distance from entry spot to the threatened short strike.
5. Adjustment action:
   - A: add a same-side short option according to the threatened side.
   - B: add a protective hedge option on the threatened side.
6. Risk exit:
   - A: no separate stop; hard exit only.
   - B: 2.0× initial credit as a portfolio stop.

Total registered cells: **3 × 2 × 3 × 2 × 2 × 2 = 144**.

The matrix is a source-inference sensitivity analysis. It is not a claim that all 144 rules are what the video literally says.

## Fixed execution conventions

- Underlying: NIFTY.
- Reference sizing: 1 lot per leg using the date-aware historical NIFTY lot-size schedule already used by the project.
- Exit: actual listed expiry day at 15:25 IST, with holiday-shifted expiry handled using the contract calendar.
- Execution: next available one-minute option quote after the decision timestamp.
- No future data.
- Base slippage: ₹0.20 per order.
- Stress slippage: ₹0.40 per order.
- Date-aware NSE/Paytm Money transaction costs, STT, exchange charges, GST and applicable brokerage model.
- Missing option quote on a required leg means that cell/week is not silently substituted.

## India VIX data

Primary reference: NSE's historical India VIX endpoint.

Pinned secondary reproducibility source: GitHub repository `RajeshMohan82/VIX-Mean-Reversion-Strategy`, commit `aa7daa84230ad62e2329e08e332f79dddf35a28a`, file `NIFTY_VIX_merged_2022_2026.csv`. This source will be copied into the branch as a cached research input and used only for the registered study window; it is not treated as superior to NSE. 

## Statistics

For every cell:
- completed trading weeks only for weekly mean/median/profit-rate statistics;
- execution coverage = completed signal weeks / eligible signal weeks;
- gross P&L and all transaction-cost components separately;
- net P&L;
- profit factor;
- max drawdown;
- weekly 5% VaR and expected shortfall;
- average and peak capital proxy;
- profitable-week rate.

Promotion gate:
- mean weekly net >= ₹5,000;
- median weekly net >= ₹5,000;
- profitable-week rate >=70%;
- at least 20 completed weeks;
- execution coverage >=80%.

Any cell failing one criterion fails promotion.

## Phase closure

The phase closes as:
- **PASS — numerical candidate ready for WFA/OOS**, or
- **FAIL — no 144-cell interpretation clears the gate**, or
- **DATA-BLOCKED — required VIX/option data cannot be verified**.

No result-driven reinterpretation is allowed.
