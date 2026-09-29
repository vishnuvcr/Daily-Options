# Phase 54 — Same-Session 09:30 ATM Put–Call IV Spread × Opening Direction Result

## Authoritative execution

- Workflow: **36549663605**
- Branch: phase-54-atm-iv-spread-opening-v1
- Artifact: **11024142461**
- Artifact SHA-256: **b081feb3ef23069dea81beda2f041abd63e480c2b2da9c434b05ec670eb0f880**

## Data integrity

- Study sessions: **1,228**
- Post-warm-up sessions: **1,168**
- Feature-eligible sessions: **1,146 / 1,168 = 98.12%**
- 09:30 ATM put/call IV-valid sessions: **1,154 / 1,168 = 98.80%**
- Feature-expiry mapping: **100%**
- Prior-information violations: **0**
- Exact-expiry files: **267**
- Execution coverage across true cells: **99.04%–100%**
- Base and Stress accounting: **reconciled**

## Frozen true-cell results

| Spread state | Mapping | Exit | Base mean/wk | Base median/wk | Base positive weeks | Stress mean/wk | Stress median/wk | Stress positive weeks |
|---|---|---|---:|---:|---:|---:|---:|---:|
| LOW_SPREAD | CONTINUE | 10:30 | -₹442 | -₹780 | 36.2% | -₹533 | -₹894 | 34.0% |
| LOW_SPREAD | CONTINUE | 15:10 | -₹571 | -₹1,106 | 30.9% | -₹663 | -₹1,236 | 29.8% |
| LOW_SPREAD | FADE | 10:30 | -₹195 | -₹300 | 45.9% | -₹296 | -₹400 | 42.6% |
| LOW_SPREAD | FADE | 15:10 | -₹356 | -₹721 | 38.6% | -₹446 | -₹824 | 36.9% |
| MID_SPREAD | CONTINUE | 10:30 | -₹251 | -₹387 | 40.1% | -₹342 | -₹500 | 37.8% |
| MID_SPREAD | CONTINUE | 15:10 | -₹211 | -₹526 | 42.0% | -₹302 | -₹645 | 39.4% |
| MID_SPREAD | FADE | 10:30 | -₹292 | -₹356 | 41.9% | -₹382 | -₹448 | 38.3% |
| MID_SPREAD | FADE | 15:10 | -₹375 | -₹635 | 38.9% | -₹466 | -₹744 | 36.1% |
| HIGH_SPREAD | CONTINUE | 10:30 | -₹282 | -₹433 | 41.2% | -₹373 | -₹545 | 38.7% |
| **HIGH_SPREAD** | **FADE** | **15:10** | **-₹49** | **-₹507** | **44.3%** | **-₹143** | **-₹547** | **43.7%** |
| HIGH_SPREAD | FADE | 10:30 | -₹424 | -₹511 | 36.0% | -₹520 | -₹588 | 32.8% |
| HIGH_SPREAD | CONTINUE | 15:10 | -₹744 | -₹1,020 | 31.0% | -₹834 | -₹1,190 | 30.2% |

**0/12** cells passed the complete promotion gate.

## Best-cell economics

For **HIGH_SPREAD / FADE / 15:10**:

### Base
- Trades: **379**
- Total net: **-₹8,558**
- Mean weekly net: **-₹49.18**
- Median weekly net: **-₹506.69**
- Positive-week rate: **44.25%**
- Worst trade: **-₹4,827**
- Max drawdown: **-₹55,375**
- Raw gross P&L: **+₹49,890**
- Slippage cost: **₹16,368**
- Transaction costs: **₹42,080**

### Stress
- Total net: **-₹24,830**
- Mean weekly net: **-₹142.70**
- Median weekly net: **-₹546.67**
- Positive-week rate: **43.68%**
- Max drawdown: **-₹61,591**
- Raw gross P&L: **+₹49,890**
- Slippage cost: **₹32,648**
- Transaction costs: **₹42,072**

This is an important diagnostic: the best frozen state produced positive gross P&L, but realistic execution friction converted it into a loss.

## Best-cell permutation-null comparison

For HIGH_SPREAD / FADE / 15:10:

Base null mean weekly P&L:
- Seed 101: **-₹484**
- Seed 202: **-₹222**
- Seed 303: **+₹42**
- Seed 404: **-₹364**
- Seed 505: **+₹65**
- Null average: **-₹192**

Stress null mean weekly P&L:
- Seed 101: **-₹561**
- Seed 202: **-₹298**
- Seed 303: **-₹35**
- Seed 404: **-₹439**
- Seed 505: **-₹12**
- Null average: **-₹269**

The true cell was better than the mean permutation-null result under both frictions, but its absolute after-cost expectancy remained negative and far below the promotion threshold.

## Calendar stability

Best-cell Base mean weekly P&L:
- 2021: **+₹145**
- 2022: **+₹57**
- 2023: **-₹78**
- 2024: **-₹32**
- 2025: **-₹677**
- 2026 available: **+₹917**

Stress:
- 2021: **+₹96**
- 2022: **-₹32**
- 2023: **-₹167**
- 2024: **-₹99**
- 2025: **-₹795**
- 2026 available: **+₹769**

The apparent edge is not stable across calendar regimes.

## Decision

**CLOSED — NEGATIVE DISCOVERY.**

The ATM put–call IV spread does not create a robust after-cost opening-direction strategy under the frozen execution model.

No post-result changes to the 60-session history, tercile boundaries, spread definition, expiry rules, direction mapping, entry, exits, spread width, or cost model are authorized.

## Strengths

- 98.12% final feature eligibility.
- 98.80% same-session ATM IV quote/IV coverage.
- 100% feature-expiry mapping.
- Zero prior-information violations.
- 12 frozen cells plus 5 permutation nulls per cell.
- Base and doubled-slippage Stress.
- Historical lot sizes and established transaction-cost model.
- Accounting reconciliation in both frictions.

## Limitations

- The feature collapses the full volatility smile to a single ATM PE-vs-CE difference.
- It is a contemporaneous state, so it cannot distinguish information arrival from market-making inventory effects.
- Gross profitability is still insufficient because execution friction dominates the small directional edge.
- No WFA/OOS is justified because no discovery cell cleared the promotion gate.
