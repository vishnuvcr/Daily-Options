# Phase 17a — Timezone-Aligned Exact-Expiry Execution

## Purpose
Repair and validate Phase 17 without changing its 384-cell hypothesis after the source audit proved that the TradeMarkk option timestamp is timezone-aware and exact-expiry files contain CE/PE, strike, OHLCV and OI.

## Frozen strategy
No threshold, entry-time, width, hold, stop, target, side, or cost parameter changes are made.

## Required engineering invariants
1. Option timestamps remain TIMESTAMP WITH TIME ZONE and are normalized to Asia/Kolkata only at the dataframe boundary.
2. Signal-minute features use option closes/OI/volume from the signal minute.
3. Entry premiums use the next-minute option open.
4. PUT maps to PE and CALL maps to CE everywhere.
5. Actual exact expiry is carried from the selected expiry file through entry and execution.
6. Hold and stop dimensions are retained when assigning simulated trades back to variants.
7. Base and stress use ₹0.20 and ₹0.40 per-leg slippage and the validated cost model.

## Promotion
No numerical result is promoted without base + stress completion and untouched walk-forward/holdout validation.
