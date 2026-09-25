# Equity Income — weekly strategy research program

## New research objective

Pause the current daily/intraday strategy tournament and build a complete strategy inventory from every Equity Income video before testing anything further.

The new trading objective is weekly trading, not daily trading.

Primary economic target:
- minimum target: Rs 5,000 net profit per traded week at the strategy's fixed reference position size;
- position size may not be increased merely to manufacture the Rs 5,000 target;
- report net weekly P&L, median weekly P&L, profitable-week rate, worst week, maximum drawdown, profit factor, expectancy, margin efficiency, and net per lot-equivalent.

A strategy that averages Rs 5,000 only because a few exceptional weeks dominate many losing weeks does not pass the robustness gate.

## Phase 26 — complete channel inventory

Input: the encrypted/private transcript archive produced by the archive branch.

Outputs:
- deterministic video registry;
- transcript registry;
- strategy-candidate registry;
- duplicate/near-duplicate video groups;
- source-fidelity status for every candidate.

No trading backtest is allowed in this phase.

## Phase 27 — strategy reconstruction

For every video that describes a strategy, create a structured rule sheet:

- underlying;
- expiry regime;
- entry day/time;
- strike-selection formula;
- lots per leg;
- long/short leg identity;
- adjustment triggers;
- hard and soft stops;
- profit target;
- time stop;
- roll logic;
- capital or margin assumptions;
- weekly/monthly/expiry-day/event classification.

Every rule field receives:
SOURCE-EXPLICIT, SOURCE-INFERRED, UNSPECIFIED, or CONFLICTING.

A strategy remains UNRESOLVED when any economically material rule is unspecified.

## Phase 28 — deduplication and family clustering

Map every candidate to a canonical payoff family.

Examples:
- short strangle / iron condor;
- ratio spread;
- calendar / diagonal;
- credit spread;
- debit spread;
- butterfly / broken-wing butterfly;
- jade lizard;
- futures/option hybrid;
- directional overlay;
- volatility-regime strategy.

Equivalent strategies are not backtested repeatedly under different video titles.

## Phase 29 — historical data feasibility

Before numerical testing, create a feasibility report covering:

- exact expiry availability;
- 1-minute option OHLC;
- chain completeness;
- execution-quality proxies;
- lot-size history;
- trading-session calendar;
- corporate actions where relevant;
- India VIX and volatility-regime variables where relevant;
- FII/DII flows where relevant;
- global-market context where relevant;
- news/event flags where the source strategy actually uses them.

A strategy is not passed to the simulator if a required field cannot be reconstructed without leakage.

## Phase 30 — deterministic weekly backtest

For each distinct strategy:

1. Freeze the exact source-derived rule.
2. Do not optimize on the full sample.
3. Use only a small preregistered sensitivity set for genuinely unspecified source fields.
4. Use historical lot sizes.
5. Include Paytm Money brokerage, exchange charges, STT, SEBI charges, stamp duty and GST.
6. Apply explicit base and stress slippage.
7. Enforce the information barrier on entries, adjustments and exits.
8. Produce one canonical weekly P&L series.

Primary outputs:
- mean weekly net;
- median weekly net;
- profitable-week rate;
- worst week;
- maximum drawdown;
- profit factor;
- expectancy;
- weekly turnover;
- margin / capital utilization;
- net per lot-equivalent;
- cost sensitivity.

## Phase 31 — regime and robustness

Segment surviving candidates by:
- high / medium / low India VIX;
- trending / range-bound markets;
- gap-up / gap-down regimes;
- expiry-week distance;
- major event weeks;
- domestic and global volatility shocks.

Where applicable, include:
- global index overnight moves;
- US VIX / major global volatility indices;
- USDINR;
- gold;
- FII/DII flows;
- major news and corporate-action flags.

These variables are explanatory unless the source strategy explicitly uses them for entry.

## Phase 32 — nested walk-forward selection

Freeze the strategy rule before each walk-forward test.

Use:
- rolling or expanding training window;
- validation window;
- untouched test weeks;
- no test-period information for parameter selection.

Only a complete weekly P&L stream survives.

## Phase 33 — independent later-period validation

Any candidate that clears the preliminary weekly target is tested on a later period never used for reconstruction or selection.

Promotion requires the Rs 5,000/week threshold to survive:
- base friction;
- stress friction;
- later-period validation;
- drawdown and worst-week constraints.

## Phase 34 — strategy portfolio research

Only after individual strategies survive should combinations be considered.

Evaluate:
- weekly P&L correlation;
- complementary regime behavior;
- overlapping margin;
- capital allocation;
- concentration;
- joint drawdown;
- transaction-cost interactions.

The Rs 5,000 target is evaluated at the declared reference capital, not by arbitrary leverage.

## Phase 35 — final manuscript

The final research report must contain:

- complete video inventory;
- strategy registry;
- source-fidelity matrix;
- data methodology;
- exact rule definitions;
- weekly P&L tables;
- equity curves;
- drawdown analysis;
- regime tables;
- WFA/OOS results;
- cost/slippage sensitivity;
- statistical analysis;
- strengths and limitations;
- rejected strategies and reasons;
- future research directions;
- reproducibility appendix.

## Stop rules

Do not spend multiple phases repeatedly tuning a strategy that fails the preregistered gates.

A strategy that fails both Base and Stress with adequate weekly coverage is retired.

A strategy with insufficient historical data is DATA-LIMITED, not profitable or unprofitable.

A strategy whose source rules remain materially ambiguous is UNRESOLVED and is not tuned through repeated backtests.

## Current status

TESTING PAUSED.

The active work is channel archiving and complete strategy-inventory construction. Trading research resumes only after the archive and strategy registry are complete.
