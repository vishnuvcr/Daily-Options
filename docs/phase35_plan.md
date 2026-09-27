# Phase 35 — Global Overnight Shock × NIFTY Option Volatility Structure

## Research question
Does the magnitude of completed global overnight equity-market shock, rather than its directional sign, predict a monetizable short-horizon NIFTY volatility response, measured through deterministic long ATM straddles and 200-point long strangles?

## Frozen design
- Study window: 2021-07-01 through 2026-08-31.
- Global inputs: six cached indices from Phase 31.8: S&P 500, NASDAQ, Nikkei, Hang Seng, DAX, KOSPI.
- Information barrier: latest completed global session strictly before the NIFTY date; 60-observation prior standardization; no same-day global information.
- Features: GLOBAL_ABS = abs(mean six-market z-scores); US_ASIA_DISPERSION = abs(mean US z - mean Asia z).
- Thresholds: 1.0 and 1.5.
- Structures: ATM long straddle and 200-point long strangle.
- Entry: 09:31 IST; exits: 10:30 and 15:10 IST.
- Nearest eligible NIFTY expiry on/after trade date; historical lot size; one lot.
- No stops, targets, adjustments, leverage, discretionary filtering, or post-result tuning.
- Base slippage ₹0.20/order; Stress ₹0.40/order; frozen project transaction/statutory charge model.
- Five full-panel permutation null seeds: 101, 202, 303, 404, 505.
- Frozen true grid: 2 features × 2 thresholds × 2 structures × 2 exits = 16 cells.

## Data gate
Require ≥95% complete feature coverage among sessions eligible after the 60-observation warm-up, zero prior-date violations, usable NIFTY option data, and execution-price coverage reported for every true cell. If the gate fails, close DATA-LIMITED and do not substitute sources.

## Promotion gate
A discovery cell is promotable only if both Base and Stress have mean weekly net ≥ ₹5,000, median weekly net ≥ ₹5,000, and ≥70% positive weeks. No WFA/OOS is authorized unless the discovery gate passes.

## Statistical analysis
Report total/mean/median weekly net, positive-week rate, worst trade/week, max drawdown, slippage, transaction costs, raw gross, execution coverage, and five permutation-null comparisons.

## Phase boundaries
1. Freeze plan and branch.
2. Implement/tests.
3. Run data gate.
4. Run frozen Base/Stress grid and nulls only if gate passes.
5. Persist results, status, errors, and manuscript.
6. Close phase and advance to the next preplanned distinct family; do not loop indefinitely.
