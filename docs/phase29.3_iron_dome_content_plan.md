# Phase 29.3 — NIFTY Iron Dome content-to-contract validation

## Objective

Take the two Phase 29.2 contract-ready duplicate candidates and determine whether the source describes a deterministic, executable Iron Dome rule set that can be represented leg-by-leg against the pinned NIFTY 1-minute option data.

## Candidates

- 5xz7X5QsFv8 — Nifty Iron Dome: 2 Adjustments Only for Working People (2026-04-30).
- 9cetNfglyO4 — Nifty Iron Dome Options Strategy: 2 Adjustments Only for Working People (2026-05-02).

## Research questions

1. Can a reliable Python transcript fetch reproduce the source transcript for both videos without using a model-generated transcript?
2. Which explicit facts are stated about entry time, expiry, centre/wing strikes, lot ratios, adjustment triggers, adjustment legs, stop/loss limits, and exit?
3. Do the pinned TradeMarkk NIFTY expiry partitions around the source dates contain all contracts needed by the extracted rule?
4. Does the independent Rissin source contain the same dates/contract universe sufficiently for replication?
5. Can the rule be frozen without discretionary interpretation?

## Method

1. Fetch transcripts with youtube-transcript-api, preferring the exact video ID and English tracks.
2. Store only transcript SHA-256, segment count, and short rule-evidence snippets/timestamps in the research artifact; do not commit full plaintext transcripts.
3. Extract candidate rule statements using deterministic keyword/number matching (entry, expiry, CE/PE, strike, lot, adjustment, stop, exit).
4. Inventory the exact TradeMarkk NIFTY Parquet expiry files surrounding the 2026-04-30/2026-05-02 source dates at revision 51ca58c.
5. For candidate expiry files, download only the bounded files required for schema/content inspection, using a revision-pinned Hugging Face cache.
6. Verify the independent Rissin yearly NIFTY partition availability for 2026 and, where feasible, inspect its schema/content.
7. Do not infer missing rules from payoff diagrams or title language. Missing rule facts become explicit blockers.
8. Keep numerical backtesting disabled. Phase 29.3 only decides whether a fully specified contract rule exists.

## Hard gate to Phase 30

A candidate can move to a numerical test only when:
- transcript/rule evidence establishes every leg and trigger;
- expiry and lot-size regime are dated and exact;
- required contract records exist at every signal/adjustment point;
- the rule is deterministic enough to code without future information;
- execution price/slippage/cost model is separately registered.

## Outputs

- reports/phase29_3_iron_dome_rule_evidence.json
- reports/phase29_3_expiry_file_inventory.json
- reports/phase29_3_summary.json
- data/equity_income/phase29_3_transcript_fetch_manifest.json
- tests/test_phase29_3_iron_dome_content.py
- .github/workflows/phase-29.3-equity-income-iron-dome-content-v1.yml

## Stop condition

Stop when both candidate videos are either fully specified for later numerical coding or have explicit, reproducible blockers. Do not invent missing strategy mechanics and do not start P&L in Phase 29.3.
