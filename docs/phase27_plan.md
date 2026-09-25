# Phase 27 — Source-faithful strategy reconstruction

## Objective
Recover exact rules for every candidate. Tag every rule field SOURCE-EXPLICIT, SOURCE-INFERRED, UNSPECIFIED or CONFLICTING.

## Inputs
Phase 26 registry + encrypted/private transcripts

## Outputs
docs/equity_income_strategy_rules/*.md

## Weekly research gate
The program target is **₹5,000 net per traded week** at a fixed declared reference position size. Position size may not be increased solely to satisfy the target.

## Completion gate
No candidate enters backtest while economically material rules remain unresolved.

## Mandatory controls
- Keep strategy rules frozen once the phase's test definition is registered.
- Account for Paytm Money brokerage, NSE exchange charges, STT, SEBI fee, stamp duty, GST and explicit Base/Stress slippage.
- Preserve information barriers and historical lot sizes.
- Log every implementation/data error in `docs/error_log.md`.
- Update `docs/research_status.md` after each execution.

## 2026-09-25 — Phase 27 activation after Phase 26 completion

Phase 26 is complete with 169/169 transcript integrity verified. Phase 27 now performs source-preserving rule evidence extraction for all strategy-candidate videos flagged by Phase 26.

Transcript text is fetched through a Python HTTP client, held only in memory, and converted into non-copyright structured evidence: days, times, underlying, premium references, lot/ratio references, strike terminology, stop/target/adjustment phrases and detected payoff-family terms.

Rule cards store only structured evidence and source provenance. They do not store plaintext transcripts. Materially unresolved rule fields remain UNSPECIFIED and are not allowed into numerical testing.