# Phase 30.3 — Equity Income Bear Put source resolution

## Purpose
Resolve the source-faithful trading rules for the Equity Income video **“Bear Put Spread Attack Plan: When to Enter and How to Adjust”** (video ID `IpCuGEDxF1k`) before any numerical testing.

## Research question
Can the source-defined bear-put-spread method be reconstructed into a deterministic current NIFTY weekly rule set, including entry timing, strike selection, adjustment logic, stop-loss, exit, and position sizing, without inventing missing rules?

## Scope
1. Recover timestamped caption segments with a deterministic Python-only acquisition path.
2. Hash the complete recovered caption stream for provenance.
3. Extract bounded contextual windows around economically material rule terms.
4. Freeze a source-resolution matrix with explicit states: OBSERVED, AMBIGUOUS, UNRESOLVED, or CONTRADICTED.
5. Reconcile current NIFTY Tuesday-expiry / dated lot-size rules only after the source mechanics are resolved.
6. Keep `backtest_allowed=false` until all economically material fields are resolved and an executable contract join is verified.

## Required source fields
- underlying/instrument
- structure and long/short leg direction
- expiry selection
- entry day/date relation to expiry
- entry clock
- strike-selection rule
- premium/debit/credit rule
- lot ratio
- adjustment trigger
- adjustment strike movement
- adjustment timing
- stop-loss definition/value
- profit target, if any
- time-based exit
- event-based exit
- no-trade / skip conditions
- maximum holding period
- capital/margin language when explicitly source-defined

## Evidence standard
Transcript/caption evidence is primary. Public YouTube description or other external pages may corroborate but cannot fill a missing numerical rule. No result-driven choice is allowed.

## Numerical-testing gate
Backtesting is blocked until:
- the source rule card is frozen;
- current Tuesday-expiry geometry is mapped;
- historical lot-size schedule is verified by dated exchange evidence;
- exact contract coverage is established;
- Paytm Money/NSE transaction charges and Base/Stress slippage are registered;
- the information barrier and next-minute execution convention are fixed.

## Planned downstream phases
- 30.3: source resolution
- 30.4: exact contract/lot readiness
- 30.5: bounded numerical grid
- 30.6: nested WFA and later-period OOS only if the numerical gate is passed

## Current status
Source resolution started on a dedicated branch. No P&L is authorized from this phase.
