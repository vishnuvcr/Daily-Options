# Phase 30.7 — Bear Put final audited result

## Status

**CLOSED — RETIRED at the weekly promotion gate.**

Authoritative GitHub Actions run: **36233110210**  
Branch: `phase-30.7-bear-put-contract-interpretation-grid-v1`  
Workflow: `Phase 30.7 - Bear Put sharded Base Stress matrix`

The screenshot checkpoint showing 9/18 shards complete is superseded by the completed run. All **18/18 shard jobs succeeded** (9 Base + 9 Stress), followed by a successful aggregate job. The aggregate audit reports **6,480/6,480 registered cells**, with **zero duplicate cells** in both friction regimes.

## Frozen experiment

The preregistered matrix was unchanged from the information barrier:

45 source/spot-feasible entry definitions × 2 expiry choices × 2 strike constructions × 3 gap thresholds × 2 adjustment waits × 3 risk/exit conventions × 2 time exits = **6,480 cells**.

No cell was selected from economic results after the run.

## Base friction result

- Registered / aggregated cells: **6,480 / 6,480**
- Cells passing weekly promotion gate: **0**
- Best full-sample mean weekly net: **-₹5,724.97**
- Best median weekly net: **-₹4,885.24**
- Profitable-week rate: **0.0%**
- Profit factor: **0.00**
- Max drawdown: **-₹168,065.998**
- Weekly 5% quantile: **-₹15,871.53**
- Weekly 5% expected shortfall: **-₹18,115.76**
- Execution coverage: **52.63%**
- Average capital proxy: **₹33,750.63**
- Peak capital proxy: **₹40,492.50**
- Gross P&L: **-₹163,965.35**
- Net P&L: **-₹171,749.04**
- Transaction-cost share of absolute gross P&L: **4.75%**

The cell attached to these summary statistics used: 30-minute resistance lookback, 0.10% touch tolerance, gap-down trigger at 0.50%, nearest weekly expiry, consecutive ATM strikes, +200-point adjustment gap, 15-minute adjustment wait, debit-stop/expiry exit, and expiry-day 15:00 exit. This is reported as the aggregate's best cell, not as an economically recommended strategy.

## Stress friction result

- Registered / aggregated cells: **6,480 / 6,480**
- Cells passing weekly promotion gate: **0**
- Best full-sample mean weekly net: **-₹5,826.11**
- Best median weekly net: **-₹4,937.20**
- Profitable-week rate: **0.0%**
- Profit factor: **0.00**
- Max drawdown: **-₹170,980.291**
- Weekly 5% quantile: **-₹16,102.78**
- Weekly 5% expected shortfall: **-₹18,323.65**
- Execution coverage: **52.63%**
- Average capital proxy: **₹33,750.63**
- Peak capital proxy: **₹40,492.50**
- Gross P&L: **-₹167,001.35**
- Net P&L: **-₹174,783.27**
- Transaction-cost share of absolute gross P&L: **4.66%**

The doubled-slippage case therefore worsened the best mean weekly net by about **₹101.14/week** relative to Base.

## Interpretation

The Bear Put family did not clear the frozen **₹5,000 net/completed-week** promotion gate in either friction regime. The failure is not solely a cost-slippage effect: even the Base result has zero profitable weeks for the aggregate's best cell and insufficient execution coverage against the 80% gate.

Because the full preregistered interpretation space was completed without any passing cell, **no walk-forward selection, later-period OOS selection, or result-driven parameter tuning is authorized for Bear Put**. The family is retired as a tested Equity Income candidate.

This is a research conclusion for the frozen implementation and data window, not a claim about the underlying video creator's strategy in all possible implementations.

## Audit trail

- Aggregate artifact: `phase30-7-bear-put-aggregate-results`
- Base diagnostics: 9 shard files, 0 duplicate cells, 6,480 aggregated cells
- Stress diagnostics: 9 shard files, 0 duplicate cells, 6,480 aggregated cells
- Contract audit passed all registered structural checks before P&L.
- Historical pre-P&L audit file retains `pnl_authorized=false` as a provenance record; the authoritative post-run aggregate summaries are the evidence that numerical computation was completed.

## Next phase

The next bounded research step is **Phase 30.8 — source-fidelity reconstruction of the next preregistered Equity Income candidate**, not Phase 31. Phase 31 is reserved for strategies that first survive the Phase 30 weekly gate.

The next reconstruction-queue candidate is the video **“No More Straddles. This Strategy Is Smarter” (OvaJumYancs)**. Its existing repository evidence contains source-explicit references to NIFTY, short/long actions, ATM and one-strike terminology, a 3:30 time reference, a 100-point width reference, and an ambiguous 3:30 ratio/lot reference, while exact structure, timing and risk/exit mechanics remain unresolved. These must be resolved from primary transcript evidence before any numerical test is allowed.

