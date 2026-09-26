# Phase 30.2 — Falcon Spread weekly independent replication — final audited result

## Scope and provenance

- Authoritative workflow run: **36220915944**
- Branch: `phase-30.2-falcon-expiry-type-fix-v1`
- Corrected implementation commit: `17793cc3eb6ddcf40484dc75339c208459cc3aef`
- Dataset: `rissin/nse-options-intraday`
- Runtime-resolved immutable dataset revision recorded by the run: `8f7739cab3f38abdcbc6332a6d0a83e1341326e3`
- Research window: 2025-09-01 through 2026-08-31, capped by available 2025/2026 partitions
- Frozen strategy family: **270 cells**
- Base: slippage 0.20 premium points/order, ₹10/order brokerage
- Stress: slippage 0.40 premium points/order, ₹10/order brokerage
- Other transaction costs: repository date-aware NSE/STT/SEBI/stamp-duty/GST framework
- Promotion gate: mean weekly net >= ₹5,000; median weekly net >= ₹5,000; profitable-week rate >=70%; >=20 completed weeks; >=80% execution coverage

## Source-faithful trading structure

Current Tuesday-expiry analogue registered for the source-era Friday/Monday/Wednesday sequence:
**Wednesday entry -> Thursday adjustment -> Monday pre-expiry exit**.

Initial structure:
- sell 5 near-week CE and 5 near-week PE around the target premium;
- buy 3 next-week CE and 3 next-week PE.

Adjustment:
- buy 5 near-week CE one listed strike above the original short CE;
- buy 5 near-week PE one listed strike below the original short PE.

The 270-cell grid varies entry clock, target premium, far-week strike mode, adjustment time and hard-stop multiple exactly as preregistered. No result-driven tuning was performed.

## Engineering validity corrections

### E0317-E0319: timestamp boundary
Raw source timestamps were normalized explicitly into Asia/Kolkata, including both timezone-aware (+05:30) and timezone-naive IST materializations.

### E0321: provenance check
An attempted retrospective pin to the older Phase 25 source revision `78b1c546...` was rejected because that revision does not contain the required NIFTY 2026 Upstox partition. It is not used for this result.

### E0322: exact-expiry type bug
The corrected loader stored expiry values as pandas datetime-like values, while `select_target()` compared them to Python `date` values. That comparison silently returned false for every row and created the earlier 0-setup artifact.

The fix normalizes both sides to pandas timestamps before comparison, with a regression test for both datetime and date representations. After the fix, the same cached dataset produced 468 setups and 4,212 executable trade records.

### Persistence
Base computation completed and its artifact was uploaded successfully, but the runner's persistence push was rejected by a fast-forward race after the branch was advanced by a documentation commit. The Base artifact is therefore the authoritative copy of the missing leaderboard/trade files. Stress persisted successfully in the repository.

## Base friction result

- Candidate setups: **468**
- Trade records: **4,212**
- Positive-mean variants: **17 / 270**
- Promotion-qualified variants: **0 / 270**
- Completed weeks for the measured leading variant: **31**
- Execution coverage: **96.875%**
- Best measured variant: `10:00:00|p30|DIAGONAL_PREMIUM|adj11:00:00|stop1.5`
- Total net: **₹44,393.06**
- Mean weekly net: **₹1,432.03**
- Median weekly net: **₹834.58**
- Profitable-week rate: **54.84%**
- Profit factor: **1.87**
- Max drawdown: **-₹16,717.15**
- 5% weekly-loss quantile: **-₹8,455.40**
- Expected shortfall (5% tail mean): **-₹12,967.70**
- Worst single measured week/trade outcome: **-₹14,961.66**
- Maximum consecutive losing weeks/trades for the leading variant: **6**

No Base variant met any combination sufficient to satisfy the full promotion gate; only 17 variants had positive mean net, and none reached the ₹5,000 weekly threshold or 70% positive-week rate.

Authoritative Base artifact:
https://github.com/vishnuvcr/Daily-Options/actions/runs/36220915944/artifacts/10899530531

## Stress friction result

- Candidate setups: **468**
- Trade records: **4,212**
- Positive-mean variants: **3 / 270**
- Promotion-qualified variants: **0 / 270**
- Completed weeks for the measured leading variant: **31**
- Execution coverage: **96.875%**
- Leading measured variant: `10:00:00|p30|DIAGONAL_PREMIUM|adj11:00:00|stop1.5`
- Total net: **₹22,749.06**
- Mean weekly net: **₹733.84**
- Median weekly net: **₹54.58**
- Profitable-week rate: **51.61%**
- Profit factor: **1.37**
- Max drawdown: **-₹24,333.45**
- 5% weekly-loss quantile: **-₹9,053.40**
- Expected shortfall (5% tail mean): **-₹13,415.70**
- Worst single measured week/trade outcome: **-₹15,441.66**
- Maximum consecutive losing weeks/trades for the leading variant: **6**

Authoritative Stress artifact:
https://github.com/vishnuvcr/Daily-Options/actions/runs/36220915944/artifacts/10899630104

## Interpretation

The zero-setup result from runs 36216668042 / 36218652778 / 36220039329 was an implementation/data-boundary artifact and is **not** a Falcon performance result.

After the E0322 correction, the frozen Falcon family generated substantial executable coverage. The complete Base and Stress calculations both failed the preregistered ₹5,000/week promotion gate by a wide margin:

| Metric | Base | Stress |
|---|---:|---:|
| Setups | 468 | 468 |
| Trades | 4,212 | 4,212 |
| Positive-mean variants | 17/270 | 3/270 |
| Promotion-qualified | 0/270 | 0/270 |
| Leading mean weekly net | ₹1,432.03 | ₹733.84 |
| Leading median weekly net | ₹834.58 | ₹54.58 |
| Leading positive-week rate | 54.84% | 51.61% |
| Leading profit factor | 1.87 | 1.37 |
| Leading max drawdown | -₹16,717 | -₹24,333 |

The registered continuation rule therefore closes Phase 30.2 **without WFA/OOS selection and without result-driven retuning**.

## Conclusion

**Falcon Spread is not promoted to the walk-forward stage in this research program.**

The decision is based on the corrected, source-faithful, cost-adjusted Base and Stress runs after resolving the timestamp and exact-expiry type implementation defects. The family generated trades reliably after correction, but **0 of 270 frozen variants** satisfied the weekly promotion gate in either friction regime.

## Next bounded research phase

The next distinct source-faithful Equity Income candidate is **Bear Put Spread** (Phase 30.3/30.4). Its source evidence is already archived and hashed, but the numerical backtest remains blocked until the missing resistance definition, quantitative crack/gap trigger, stop-loss, exit rule and expiry-selection fields are explicitly resolved.
