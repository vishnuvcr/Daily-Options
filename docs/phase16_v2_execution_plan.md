# Phase 16 v2 Execution Plan

## Research question
Can the preregistered intraday NIFTY IV-skew tail credit-vertical rule produce reproducible net P&L at or above ₹1,000 per active lot per trading day after realistic costs and doubled slippage?

## Frozen rule
3 entry times × 3 skew-z thresholds × 2 jump brakes × 2 hedge widths × 2 holding periods × 2 stop ratios × 2 directions × 2 expiry types = 288 cells per expiry shard.

Positive skew: short ATM-2 PUT / long ATM-(2+width) PUT.
Negative skew: short ATM+2 CALL / long ATM+(2+width) CALL.
Entry: next-minute option open.
Target: 50% of entry credit.
Stop: 1.50× or 2.00× entry credit.
Hold: 30 or 60 minutes.
Base slippage: ₹0.20 per leg.
Stress slippage: ₹0.40 per leg.

## Data and information barriers
Pinned Artist23 NIFTY 1-minute options revision `45e0a04`.
Trading date derives from timestamp +5:30 IST.
Nearest future actual expiry is carried through feature, entry, execution-window, outcome-cache and variant joins.
Only required ATM±2/3/4 strike files are scanned.

## Computational design
Unit tests → cached dataset → base friction → doubled-slippage stress.
The outcome cache computes each unique setup/side/width/hold/stop result once, then merges those outcomes into the preregistered 288-cell grid.
No test-period retuning, parameter expansion, result-driven filtering, or variant deletion.

## Promotion gate
A candidate must have positive cost-aware performance, positive doubled-slippage performance, sufficient trade and calendar coverage, and at least one untouched walk-forward window at or above ₹1,000 net per active lot per trading day. No single tiny cluster may dominate the promoted conclusion.

## Failure handling
Every engineering/data defect is logged before P&L interpretation. Superseded artifacts are explicitly non-evidentiary. A materially different mechanism becomes a separate research phase.
