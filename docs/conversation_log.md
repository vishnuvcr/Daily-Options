# Conversation and Decision Log

## 2026-09-23

### User requirement
The user requested a daily, intraday Indian options strategy, with a target of at least Rs 1,000 profit per lot per day, and asked for extensive research to find, create and validate such a strategy.

### Research decision
Treat Rs 1,000 net profit per active lot per trading day as the primary quantitative target. Search broadly across strategy families and regimes. Never use gross P&L as the promotion criterion.

### Engineering decision
The repository was empty, so bootstrap it with a research charter, phase plan, status log, error log and reproducibility scaffolding.

### Communication decision
This log records requirements, research decisions, evidence and outcomes. It intentionally does not record private hidden chain-of-thought.


## 2026-09-23 — Research execution update
- Repository audit confirmed the project started empty.
- Phase 0 charter and Phase 1 data/cost scaffolding were created.
- Phase 2 baseline tournament branch was created with an automated NIFTY one-minute sample download, leakage-aware signal timing, configurable costs/slippage, and unit tests.
- The first CI backtest attempt found an import-path error (E0006); the workflow was corrected to execute the research module form and automatically rerun.
- Current numerical result is intentionally not declared until the corrected backtest completes.
- The research target remains a hypothesis threshold, not a guaranteed daily outcome.


## 2026-09-24 — New-chat continuation
- User asked what comes next after Phase 3E. The decision is to avoid further RSI/VWAP/EMA tuning.
- Phase 3F was created: option-chain microstructure and volatility-regime research using IV, OI, volume, strike concentration and derived gamma proxies.
- A manual data-audit workflow was added. It uses a multi-year public NIFTY options dataset candidate with explicit IV/OI fields and caches the downloaded source between workflow runs.
- The first gate is data validity; strategy optimization begins only after the source passes the audit.


## 2026-09-24 — Execution continuation
- User issued "Ok proceed" to continue the research without stopping mid-phase.
- Action taken: hardened Phase 3F so the complete IV/OI-capable source tree is audited before any trading optimization.
- Decision: do not use the dataset's volume field until the observed schema anomaly is quantified and independently reconciled. This prevents another round of parameter tuning on an unvalidated input.


## 2026-09-24 — Phase 3F result and next hypothesis
- The user’s "Ok proceed" instruction was treated as authorization to continue through the defined research phases without waiting between experiments.
- The multi-year directional IV/OI/volume imbalance screen failed the promotion gate; zero of 972 variants reached Rs 1,000/day and the best configuration was negative after costs.
- Decision: stop tuning the failed directional family and move immediately to a defined-risk short-volatility/iron-fly regime hypothesis using IV/RV, trend magnitude and chain-balance filters.
- The directional result and full data-audit summary are committed under `reports/`.


## 2026-09-24 — OI repositioning result
- The next materially different Phase 3F hypothesis tested normalized OI changes on fixed daily strike bands around prior-15-minute price breaks.
- The full 216-variant grid failed: no positive calendar-day expectancy and no target-qualified configuration.
- Decision: stop tuning this family and move to IV-skew shock/reversion/relative-value features.
