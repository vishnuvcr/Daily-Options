# Phase 29.2 — Equity-Income contract coverage and expiry mapping

## Purpose

Convert the 51 Phase 29.1 preliminary-feasible family members from aggregate source availability into a conservative, strategy-specific contract-readiness matrix. No trading P&L is computed in this phase.

## Research questions

1. Can each candidate's underlying be determined from the frozen Phase 28 title/family metadata without inventing missing information?
2. Does the pinned TradeMarkk source contain the exact underlying/expiry partitions required by the candidate's payoff family?
3. Is an independent Rissin partition available for the same index underlying, and where is independent validation structurally unavailable?
4. Which families require multiple simultaneous expiries (calendar/diagonal/ratio structures), and are at least two dated option partitions present?
5. Which candidates still require exact rule reconstruction, contract-level joins, dated NSE lot-size evidence, or quote-quality validation before numerical testing?

## Frozen inputs

- Phase 28 family registry: phase-28-equity-income-dedup-v1:data/equity_income/strategy_families.csv.
- Equity Income discovery manifest: equity-income-channel-archive-v1:data/equity_income/video_manifest.jsonl.
- Equity Income transcript manifest: equity-income-channel-archive-v1:data/equity_income/transcript_manifest.jsonl.
- Phase 29.1 source inventory with pinned revisions:
  - TradeMarkk 51ca58c.
  - Rissin 78b1c5468255d18cf492984bfe6fe4e3ac874d7c.

## Method

1. Copy the frozen Phase 28 candidate registry and the two archive manifests into the workflow workspace.
2. Verify that every Phase 28 candidate video ID is present in the archived 169-video discovery manifest.
3. Use title/family hints to infer an underlying only when the text is explicit. Otherwise mark UNDERLYING_UNRESOLVED.
4. Infer whether the structure requires one expiry, multiple expiries, weekly/intraday timing, or long-dated/LEAPS continuity. This is metadata-level inference only.
5. Intersect those requirements with actual Parquet partition counts from Phase 29.1. Do not treat a repository directory as data presence.
6. Mark independent-validation availability separately from primary-source availability.
7. Require a dated contract join for historical lot size/expiry and do not back-project current rules.
8. Keep backtest_allowed=NO for all rows. This phase may authorize the next contract-content validation step only; it never authorizes P&L.

## Readiness states

- CONTRACT_READY_FOR_CONTENT_JOIN: underlying known, primary partition present, and for index candidates an independent index partition is also present; exact contract fields still need content-level validation.
- DATA_PARTIAL_INDEPENDENT_GAP: primary data exist but independent source does not cover the same underlying (notably stock-option candidates).
- UNDERLYING_UNRESOLVED: title/family metadata do not identify a defensible underlying.
- LONG_DATED_DATA_LIMITED: LEAPS/long-dated continuity cannot be established from the pinned intraday dataset.
- RULE_RECONSTRUCTION_REQUIRED: family metadata are too broad or unresolved for a deterministic contract composition.

## Hard gates

No candidate becomes numerically backtestable until all of the following are true:
- exact underlying and leg composition are frozen;
- exact expiry identity and historical expiry regime are joined without look-ahead;
- all required legs have sufficient historical contract/quote coverage;
- historical lot size is resolved from dated official evidence;
- executable price model is explicit and does not infer bid/ask from OHLC;
- Paytm Money brokerage and NSE statutory/exchange costs remain included in later P&L phases.

## Outputs

- reports/phase29_2_contract_coverage_matrix.csv
- reports/phase29_2_summary.json
- data/equity_income/phase29_2_contract_manifest.json
- docs/phase29.2_contract_coverage_plan.md
- tests/test_phase29_2_contract_coverage.py
- .github/workflows/phase-29.2-equity-income-contract-coverage-v1.yml

## Stop condition

Stop Phase 29.2 after the deterministic contract-readiness matrix and provenance checks are complete. Do not start numerical testing from this phase unless the explicit Phase 30 contract-content gate is satisfied.
