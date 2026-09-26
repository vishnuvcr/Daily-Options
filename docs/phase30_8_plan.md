# Phase 30.8 — “No More Straddles. This Strategy Is Smarter” source-fidelity resolution

## Purpose

Resolve the mechanics of the next preregistered Equity Income candidate before any option P&L is computed.

Primary source:
- video ID: OvaJumYancs
- title: No More Straddles. This Strategy Is Smarter

This phase is a source-resolution phase only. It must not use option P&L to choose among interpretations.

## Why this candidate is next

The preregistered Phase 27.2 reconstruction queue lists this video as a T1 candidate. That queue is an evidence/reconstruction order, not an economic ranking.

Existing Python-extracted transcript evidence is substantial but incomplete:
- NIFTY is source-explicit.
- Short actions are source-explicit.
- ATM strike language is present.
- One-strike language is also present, creating a strike-rule conflict that requires resolution.
- A 100-point width reference is present.
- A 3:30 time reference is present.
- Adjustment/move language is present in the broader extracted evidence.
- Exact entry day/time, expiry, stop, target, capital rule and exact adjustment mechanics remain unresolved.

## Research questions

1. What exact payoff structure replaces the straddle?
2. Is the structure a short strangle, a ratio structure, a spread, or a sequence that changes from one to another?
3. What are the exact long/short legs, strike offsets and 100-point-width semantics?
4. Does “ATM” describe the initial short strike, a reference strike, or only an example?
5. What does “one strike” modify, and is it part of entry or adjustment?
6. What is the exact entry day and clock time?
7. What does the 3:30 reference mean: entry, adjustment, exit, observation, or merely an example?
8. What is the adjustment trigger and exact leg action?
9. What are the stop, target/profit-taking and hard exit rules?
10. What expiry selection is intended under the current and historical NIFTY expiry regime?
11. What is the smallest fully executable source-faithful rule that can be taken into the contract/data gate without inventing missing mechanics?

## Scientific method

### Step 1 — Primary evidence consolidation

Use only the repository's Python-acquired transcript evidence as the primary source. For each field, preserve:
- exact source video ID;
- evidence timestamp(s) in seconds;
- extracted phrase/value;
- evidence classification.

No model-generated transcript text is treated as primary evidence.

### Step 2 — Field-level classification

Every material field is classified as:
- SOURCE-EXPLICIT
- CONFLICTING
- SOURCE-INFERRED
- UNSPECIFIED

The first three categories are not interchangeable.

### Step 3 — Conflict resolution

For the ATM vs one-strike conflict and the 3:30/3:30 ratio ambiguity:
- compare all available transcript occurrences;
- identify whether the field is describing the same position or different phases;
- prefer repeated, context-consistent statements over isolated fragments;
- retain unresolved conflicts rather than forcing a single interpretation.

### Step 4 — External corroboration

External descriptions/pages may be used as secondary corroboration. They cannot override contradictory primary transcript evidence and cannot silently fill omitted rules.

A failed or unavailable web corroboration search does not become positive evidence.

### Step 5 — Executability gate

Before numerical testing, require an explicit resolution for:
- underlying;
- payoff/leg structure;
- entry trigger and clock;
- strike construction;
- expiry selection;
- adjustment trigger/action;
- stop;
- target/profit lock;
- time exit;
- fixed reference position/capital convention.

Any unresolved essential field keeps Phase 30.8 BLOCKED_FOR_PNL.

### Step 6 — Contract/data gate

Only after source resolution:
- verify exact listed-expiry joins;
- verify historical lot-size schedule;
- verify sufficient 1-minute quote coverage for every leg;
- verify no-future-data execution;
- verify Paytm Money/NSE date-aware costs and Base/Stress slippage.

### Step 7 — Numerical phase, only if authorized

If the source is executable, register the entire bounded interpretation matrix before P&L, then run Base and Stress on the frozen matrix. The weekly promotion gate remains:
- mean weekly net >= ₹5,000;
- median weekly net >= ₹5,000;
- profitable-week rate >=70%;
- >=20 completed weeks;
- >=80% execution coverage.

No test-period tuning or position-size scaling to manufacture the target.

## Planned outputs

- research/phase30_8_no_more_straddles_resolution.py
- tests/test_phase30_8_no_more_straddles_resolution.py
- reports/phase30_8_no_more_straddles_source_resolution.json
- manual GitHub Actions workflow .github/workflows/phase-30.8-equity-income-no-more-straddles-source-resolution-v1.yml
- updated docs/research_status.md
- updated docs/error_log.md

## Completion criterion

The phase closes only when the rule is either:
1. SOURCE-RESOLVED / CONTRACT-READY, allowing a separate numerical phase, or
2. SOURCE-BLOCKED / RETIRED, with a documented reason.

No economic result may be used to force source resolution.

## Status

OPEN — source-resolution only; P&L blocked.
