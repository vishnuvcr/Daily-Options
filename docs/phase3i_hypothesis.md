# Phase 3I — NIFTY Futures-versus-Spot Lead-Lag

## Why this phase is next

Phase 3H retired the option-price pressure family after all 108 variants failed cost-aware walk-forward validation. Phase 3I therefore changes the information source rather than adding more option-pressure parameters.

Academic evidence makes NIFTY futures a testable candidate: a 2022 one-minute NIFTY study reports greater futures contribution to price discovery, while a later Indian high-frequency study using 5-minute data reports NIFTY futures leading spot. Earlier intraday work also reports futures-to-spot causality. These findings are evidence for a hypothesis, not an assumption that the effect is still tradeable.

Sources:
- https://doi.org/10.1155/2022/2164974
- https://doi.org/10.1108/IJOEM-07-2022-1097
- https://doi.org/10.1080/13504851003742442
- https://zenodo.org/records/10899828

## Research question

Does NIFTY futures information contain incremental short-horizon predictive information about NIFTY spot returns after timestamp alignment, contract-roll handling and realistic data-quality controls?

## Stage 1 — Data gate

Primary public source: Zenodo "Nifty spot and futures data.zip", DOI 10.5281/zenodo.10899828.

The source describes one-minute NIFTY spot and NIFTY_F1 futures data for 2017–2020. The workflow must audit:

- file identity and schema;
- date range and number of trading days;
- duplicate timestamps;
- non-positive prices;
- minute-grid completeness during the NSE session;
- spot/futures timestamp overlap;
- futures contract/roll continuity;
- timezone/session correctness;
- volume availability and anomalies.

The Zenodo record exposes the spot/futures archive as a 9.0 MB download with a published MD5 of 240aecc77a7275ec2f05a092b976bf91.

No strategy optimization is allowed if the data gate fails.

## Stage 2 — Predictive diagnostic gate

At each minute t, all features use information timestamped at or before t.

Pre-registered feature set:

- futures log return over 1, 3 and 5 minutes;
- spot log return over 1, 3 and 5 minutes;
- futures-minus-spot return differential over the same horizons;
- futures/spot basis and basis change, where both prices are valid.

Pre-registered directional diagnostic:

- thresholds: 0, 2, 5 and 10 basis points;
- mode: continuation or contrarian;
- lookbacks: 1, 3 and 5 minutes;
- one first signal per trading day for each diagnostic variant;
- forward spot horizons: 1, 3 and 5 minutes.

The diagnostic gate is considered informative only when a configuration shows a directionally correct mean forward move and hit rate materially above chance in more than one forward horizon, with the sign reproduced in both halves of the sample. A purely in-sample or single-window effect is not sufficient.

## Stage 3 — Only if Stage 2 passes

Only after the diagnostic gate passes will the branch add option execution.

The option expression will be pre-registered as:

- bullish signal -> defined-risk NIFTY call debit spread;
- bearish signal -> defined-risk NIFTY put debit spread;
- deterministic ATM strike plus a 1- or 2-step wing;
- maximum hold 5/10/15 minutes;
- one trade per day per parameter variant;
- next executable minute;
- date-aware NIFTY lot size;
- repository Paytm Money/NSE cost model;
- 0.20 option-premium points per-leg base slippage and 0.40 stress slippage;
- nested train/validation/5-day embargo/test walk-forward.

Historical NIFTY lot size for the 2017–2020 Zenodo sample is 75; the 2020 NSE circular retained the 75-lot NIFTY index contract. Later lot-size transitions remain date-aware in the research code.

## Promotion gate

A strategy is promoted only if the option implementation has positive net OOS expectancy after costs and at least one untouched test window reaches Rs 1,000/lot/day. Stress results must remain informative.

## Stop rules

- Fail the data gate -> stop Phase 3I without strategy tuning.
- Fail the predictive gate -> stop Phase 3I before downloading/processing the large options archive.
- Fail the bounded option implementation -> retire the family without post-hoc threshold expansion.
