# Final Data-Gap Assessment

## Purpose

The exploratory strategy search is closed. This document identifies the smallest set of new data capabilities needed before a future strategy phase can credibly restart.

## Priority table

| Priority | Data requirement | Minimum acceptance criterion | Scientific reason |
|---|---|---|---|
| 1 | Historical option bid/ask | >=95% synchronized quote coverage for candidate contracts | Converts theoretical close-bar returns into executable returns |
| 2 | Primary NIFTY spot/index tape | >=99% timestamp alignment | Removes proxy mismatch |
| 3 | Futures contract identity and roll history | deterministic roll selection with no future information | Prevents spurious futures/spot signals |
| 4 | Option OI/volume/IV history | full-partition audit with field-level anomaly report | Enables microstructure research without hidden schema contamination |
| 5 | India VIX history | minute-level session alignment where available | Supports volatility-regime conditioning |
| 6 | FII/FPI and DII timestamps | documented publication timestamp and revision status | Prevents look-ahead through daily aggregates |
| 7 | NSE/BSE top-of-book/depth | synchronized venue identifiers and timestamps | Enables genuine cross-venue price-discovery tests |
| 8 | Global overnight variables | synchronized global futures, crude, USD/INR and major indices | Tests cross-market information transmission |
| 9 | News/event timestamps | publication time plus source identity | Separates event-driven from endogenous moves |
| 10 | Contract/corporate-action master | exact strike/lot/adjustment mapping | Preserves historical contract economics |

## Restart rule

No new strategy grid should start until the relevant data gate passes.

## Execution-first rule

The next candidate should be tested with historical bid/ask if possible, a frozen execution specification, the trader's actual Paytm Money tariff, and a separate paper-shadow stage before live consideration.

## Stop rule

A new phase must remain bounded and pre-registered. A negative result should terminate the family rather than trigger ad-hoc threshold expansion.
