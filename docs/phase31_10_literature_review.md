# Phase 31.10 — Literature & Evidence Review

## 1. Institutional flows and Indian equities

NSE identifies FII/FPI and DII trading activity as a research/data product and maintains an FII/DII reporting page. NSE's research/data-sharing documentation also lists FII/FPI and DII trading activity as available data and identifies equity-derivatives daily/monthly archives as a separate historical-data family.

The key methodological implication is that cash-market FII/DII activity is observable, but a historical daily series must be reconstructed from a source with documented temporal coverage. The public `fiidiiTradeReact` endpoint is current-day oriented; therefore Phase 31.10 does not silently pretend that endpoint provides a full historical backfill.

## 2. Participant-wise derivatives positioning

NSE's F&O archive includes participant-wise open-interest reports. Public implementations document the archive naming convention:

`https://nsearchives.nseindia.com/content/nsccl/fao_participant_oi_DDMMYYYY.csv`

and describe four participant categories:
- Client
- DII
- FII
- Pro

The participant report separates index-futures and stock-futures long/short quantities. This makes FII/DII index-futures positioning a cleaner EOD positioning variable than attempting to infer institutional exposure from raw option-chain OI.

The Phase 31.10 feature design therefore uses only index-futures positioning and explicitly avoids mixing stock-futures or option positions into the primary signal.

## 3. Existing public data tooling

Public open-source implementations were inspected to validate the archive path and field interpretation:
- NseKit documents participant-wise OI access through the NSE archive.
- NSE EOD report tooling parses the participant file into FII/DII/Pro/Client index-futures net positioning.
- Other public projects explicitly warn that `fiidiiTradeReact` is not a historical daily backfill endpoint, supporting the decision to treat historical cash FII/DII as an auxiliary dataset rather than a primary true-grid feature.

These projects are used for schema/path reconnaissance only; the trading computation remains based on the pinned repository cache and the official NSE archive.

## 4. Academic evidence

The Indian-market literature contains multiple studies linking FII activity with NIFTY returns or volatility, but results are not uniform across periods, frequencies, and econometric specifications. Relevant themes include:
- FII activity and NIFTY volatility;
- dynamic relationships between foreign institutional flows and NIFTY returns/volatility;
- short-run causality tests between FII/DII activity and NIFTY performance.

The research implication is a need for a no-lookahead, finite, friction-aware experiment rather than adopting an institutional-flow rule from correlation alone.

## 5. Gap between positioning and tradable option P&L

Even when positioning contains directional information, option implementation introduces:
- strike selection;
- expiry selection;
- lot-size changes;
- brokerage;
- STT and exchange/statutory charges;
- entry/exit slippage;
- execution-price coverage.

Phase 31.10 therefore treats institutional positioning as a predictor hypothesis and tests the complete option implementation, not just NIFTY point-return direction.

## 6. Evidence hierarchy

1. **Primary:** official NSE participant-wise OI archive.
2. **Primary/current auxiliary:** official NSE FII/DII activity endpoint.
3. **Secondary validation:** public open-source parsers and historical mirrors, used only for schema/overlap validation or to diagnose availability.
4. **Published research:** used to formulate the hypothesis, not as a source of numerical trading parameters.

## 7. Key sources

- NSE Historical Reports: https://www.nseindia.com/static/resources/historical-reports-capital-market-daily-monthly-archives
- NSE Derivatives Daily/Monthly Reports: https://www.nseindia.com/resources/historical-reports-capital-market-daily-monthly-archives-derivative-market
- NSE Data Sharing Policy / research data list: https://www.nseindia.com/all-reports
- NSE FII/DII report page: https://www.nseindia.com/reports/fii-dii
- Official participant OI archive family: https://nsearchives.nseindia.com/content/nsccl/fao_participant_oi_DDMMYYYY.csv
- NseKit participant-wise OI implementation: https://github.com/Prasad1612/NseKit
- NSE F&O EOD report tooling / participant OI field interpretation: https://github.com/nseepana/eodreport
- FII/DII current-data implementation note: https://github.com/aeron7/nsepython/blob/master/nsepython/rahu.py
- FII/DII historical-data limitations documented by an independent open-source project: https://github.com/Samp_proj (project note referenced during source audit)
- Public FII/DII static API (secondary source): https://github.com/chirag127/fii-dii-activity-api
- Public FII/DII historical dashboard/data: https://github.com/MrChartist/fii-dii-data

## 8. Preregistration interpretation

No paper, public codebase or commentator is allowed to set the Phase 31.10 threshold, lookback, exit, strike, wing or promotion criterion after the fact. Those are frozen in `docs/phase31_10_plan.md`.
