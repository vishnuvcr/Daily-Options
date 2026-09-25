# Phase 30 v8 — Cell-state isolation correction

## Invalidated v7 finding
Phase 30 v7 produced apparently strong RISK_60 weekly P&L, but those numbers were invalidated by a shared mutable-state defect. `run_cell` reused `setup[initial_legs]` directly. The first parameter cell closed those leg dictionaries by setting `active=False`; subsequent cells inherited the closed state and therefore recorded the opening premium without a corresponding closing transaction.

Diagnostic evidence: the no-adjustment RISK_60 cells had only about four order-cost charges and Base-to-Stress P&L changed by approximately four order slippage units, consistent with opening-credit-only accounting rather than a full round trip.

## v8 correction
Each parameter cell receives a fresh leg-state list via `clone_initial_legs`. The underlying option DataFrames are shared read-only; mutable order state (`active`, `exit_price`) is isolated per cell.

Two regression tests are added: cloned leg state must not mutate the source setup, and running the same cell twice against the same setup must close four legs both times while leaving the setup reusable.

## Acceptance rule
All v7 Base/Stress P&L is permanently quarantined. No Phase 30 candidate advances to WFA/OOS until v8 Base and Stress both complete, the state-isolation tests pass, full round-trip brokerage/slippage accounting is verified, and the resulting weekly distribution is independently audited.