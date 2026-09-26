# Phase 31.8 — Global Overnight Cross-Market Transmission

## Status
PREREGISTERED — global-data gate pending.

## Research question
Does information from major global equity markets, available before the NIFTY open, predict the direction of the NIFTY trading day strongly enough to support a defined-risk directional option spread after realistic costs and slippage?

## Literature basis
An NSE working paper decomposes NIFTY and NASDAQ returns into daytime and overnight components and studies how returns from a non-overlapping market can transmit into the NIFTY opening price. The present phase converts that descriptive transmission idea into a bounded executable hypothesis without assuming that transmission is itself a tradeable edge.

## Global data universe
Six daily equity indices:
- S&P 500 (^GSPC)
- NASDAQ Composite (^IXIC)
- Nikkei 225 (^N225)
- Hang Seng (^HSI)
- DAX (^GDAXI)
- KOSPI Composite (^KS11)

Primary acquisition source: Yahoo Finance via a pinned yfinance version, with the retrieved daily data persisted into the phase branch under `data/cache/phase31_8_global/`. No silent substitute source is allowed after execution begins; the acquisition manifest records source, ticker, date coverage and retrieval timestamp.

The workflow skips re-download when the persisted source files are already present.

## No-lookahead alignment
For each NIFTY trade date t:
- only each global market's **latest completed session strictly before t** is eligible;
- the feature return for that market is that completed session's close-to-close return;
- standardization uses a 60-observation rolling mean and standard deviation calculated strictly from observations before the selected return;
- no global observation from date t or later enters the signal.

This deliberately sacrifices some contemporaneous information to make the information barrier unambiguous.

## Frozen feature grid
Three deterministic composites:
1. **US_LEAD** — mean of standardized S&P 500 and NASDAQ Composite returns.
2. **ASIA_LEAD** — mean of standardized Nikkei 225, Hang Seng and KOSPI returns.
3. **GLOBAL_LEAD** — mean of all six standardized market returns.

Two absolute thresholds:
- 0.50 z
- 1.00 z

Positive composite values map to a long NIFTY call debit spread; negative values map to a long NIFTY put debit spread.

## Frozen execution grid
Two fixed exit horizons:
- 10:30 IST
- 15:10 IST

For all 12 cells:
- signal completed by 09:30 IST;
- entry at 09:31 option open;
- exit at the selected horizon option close;
- nearest NIFTY expiry on/after the trade date only;
- ATM strike nearest ₹50;
- 200-point wing;
- one lot;
- no stop, target, adjustment, leverage or discretionary override.

Grid size: **3 features × 2 thresholds × 2 exit horizons = 12 cells**.

## Null controls
For each feature, its complete eligible signal series is randomly permuted across NIFTY trading dates using fixed seeds 101, 202, 303, 404 and 505 **before thresholding**. The same threshold, execution, cost and exit rules are then applied.

Null controls are diagnostic only and cannot be promoted.

## Data gate
Before P&L:
- all six global sources must exist with continuous enough daily history for the study window;
- at least 95% of eligible NIFTY trade dates must have all three composite feature families available;
- every selected global return date must be strictly earlier than the NIFTY trade date;
- each global z-score must have at least 60 strictly prior observations;
- NIFTY option data must cover the same signal/execution period;
- exact 09:31 entry and horizon exit option rows must be measurable, not silently substituted;
- the global acquisition manifest must record the exact source/version and date coverage.

If the gate fails, the phase closes DATA-LIMITED without inventing substitutes.

## Costs and execution
- Historical NIFTY lot sizes.
- Frozen Phase 31.3 transaction/statutory charge model.
- Base slippage: ₹0.20/order.
- Stress slippage: ₹0.40/order.
- Accounting must satisfy raw gross − slippage − transaction/statutory costs = net P&L.

## Promotion gate
A true cell must satisfy, in both Base and Stress:
- mean weekly net ≥ ₹5,000;
- median weekly net ≥ ₹5,000;
- positive-week rate ≥ 70%.

No WFA/OOS validation is authorized unless the discovery gate is cleared.

## Stop rule
Close after the frozen 12 true cells plus 60 null summaries per friction. Do not add indices, thresholds, lookbacks, horizons or structures because of observed results.

## Required outputs
- global acquisition manifest;
- global data gate;
- daily feature ledger;
- true and null trade ledgers;
- weekly P&L ledgers;
- true-cell Base/Stress summaries;
- null-control comparison tables;
- price coverage diagnostics;
- accounting reconciliation;
- drawdown, worst-week, tail-loss and positive-week statistics;
- final research memo with conclusion, limitations and next direction.

## Primary external evidence
- NSE working paper, *Transmission of Information and Return Spillovers Between U.S. and Indian Markets* (NIFTY/NASDAQ overnight/daytime decomposition): https://nsearchives.nseindia.com/content/research/Paper39.pdf
- Benjamin Po finance dataset pipeline (global market categories; secondary source discovery): https://github.com/benjaminpo/finance-dataset
- Pubmarks public-market datasets: https://github.com/Pubmarks/datasets
