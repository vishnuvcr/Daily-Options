# Status — Alternating OTM Buy/Sell Phase C

Branch: research/alternating-otm-phase-c-tail-filter-v1

Current status: PREREGISTERED / READY FOR EXECUTION

Parent baseline workflow: 36535251511

Phase objective: identify one simple pre-entry tail-loss exclusion rule from discovery data only, then validate that frozen rule on the untouched 2025+ holdout.

No Phase C selection or holdout result is accepted yet.

## Phase state

- Data source: completed alternating Base/Stress artifacts from workflow 36535251511.
- Discovery: 2021-07-01 to 2024-12-31.
- Holdout: 2025-01-01 onward.
- Candidate grid: 4 features × 5 discovery quantiles = 20 rules.
- Selection criterion: highest mean Base/Stress discovery net-P&L improvement, subject to >=50% retained and positive improvement in both frictions.
