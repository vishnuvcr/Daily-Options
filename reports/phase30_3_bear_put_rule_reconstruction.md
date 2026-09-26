# Phase 30.3 — Bear Put source rule reconstruction

## Source
- Video: **Bear Put Spread Attack Plan: When to Enter and How to Adjust**
- YouTube video ID: `IpCuGEDxF1k`
- Source caption segment count: **243**
- Transcript SHA-256: `a79b1e15c1f10fe053ffc0ba4999a8675cd26202ce70b27459328210d809c9a6`
- Evidence artifact: `reports/phase30_3_bear_put_source_contexts.json`
- Numerical backtest authorization: **NO**

## Resolved source facts

### Structure
The source explicitly describes a **classic bear put spread**: buy one put and sell another put after it. The worked example buys the **26,300 put** and sells the next lower **26,200 put**. This is a defined-risk debit put spread in the example.

### Entry concept
The source explicitly says not to enter merely from an opinion. It describes waiting for the market to decide: when price is sustaining near a resistance level and then a **crack or gap down** occurs, the bear put spread can come into the picture. The source also says it personally prefers to trade resistance.

This is a **market-condition trigger**, not a fixed clock.

### Example payoff / capital discussion
The simulator example states an adverse outcome of about **22,155** and then refers to the favorable outcome as **4.3**; the unit/scale of the latter value is not recoverable with sufficient certainty from the extracted evidence and is therefore not used as a numerical rule. The source separately says capital deployment remains on the lower side for the debit spread because margin is based on the combined legs.

### Adjustment
The source discusses the failure case where the market breaks resistance and continues upward. It gives an example of a large gap up of roughly **200–300 points** and says that, if the market does not come back and the trader still wants to adjust, the original 26,300/26,200 bear put can be **converted into a ratio** by selling **one additional 26,200 put**. The source explicitly calls this an adjustment rather than a new initial entry.

The source also warns: **do not rush the adjustment immediately** because the market can reverse. If the market reverses, the newly sold put should be squared off.

### Risk / margin
The source notes that adding the extra short put requires additional margin. It does not provide a fixed stop-loss number in the recovered evidence.

## Unresolved fields

| Field | Status | Reason |
|---|---|---|
| Exact entry clock | UNRESOLVED | Source gives market-condition logic, not a fixed time |
| Exact resistance definition | UNRESOLVED | “Resistance” is discussed but not frozen as a mathematical rule |
| Exact crack/gap-down threshold | UNRESOLVED | No numerical trigger recovered |
| Expiry selection | UNRESOLVED | Extracted evidence does not freeze weekly/monthly or exact days-to-expiry |
| Strike algorithm | PARTIALLY RESOLVED | Worked example uses consecutive 26,300/26,200 puts, but universal strike rule is not explicitly stated |
| Debit threshold | UNRESOLVED | No fixed entry debit/credit rule recovered |
| Adjustment trigger | PARTIALLY RESOLVED | Breakout/gap-up and failure of view are clear; exact quantitative trigger is not |
| Adjustment timing | PARTIALLY RESOLVED | “Do not rush” is explicit, but no fixed waiting time or clock is given |
| Adjustment quantity | RESOLVED FOR EXAMPLE | One additional 26,200 short put |
| Reversal handling | RESOLVED FOR EXAMPLE | Square off the newly sold put if market reverses |
| Stop-loss | UNRESOLVED | No fixed hard-stop value recovered |
| Profit target | UNRESOLVED | No numerical target recovered |
| Time-based exit | UNRESOLVED | No exact exit clock/date rule recovered |
| Lot ratio | PARTIALLY RESOLVED | Initial example is 1:1; adjustment example becomes 1:2 at the short strike |
| No-trade rule | PARTIALLY RESOLVED | Source requires a resistance-based bearish confirmation; it does not define a complete algorithm |
| Capital requirement | QUALITATIVE ONLY | Source says deployment remains lower but extra short put requires additional margin |

## Methodological decision
No missing field is filled by model inference. No P&L is accepted from this phase. A later numerical phase must either:
1. obtain additional source evidence that resolves the missing fields, or
2. register a bounded interpretation grid that treats each unresolved interpretation as an explicit experimental dimension rather than silently choosing one.

Even in option (2), the initial test may only proceed after an information-barrier-safe mathematical definition of resistance/crack/gap-down and a pre-registered stop/exit convention are documented.

## Next phase
Phase 30.4 may perform **data/contract feasibility only** for NIFTY index options and dated lot-size/exact-expiry coverage. It must not convert unresolved Bear Put rules into performance results.
