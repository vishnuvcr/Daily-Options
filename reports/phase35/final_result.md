# Phase 35 — Global Overnight Shock × India-Local Volatility State
## Final Result

**Decision: DATA-LIMITED — RETIRED WITHOUT P&L ACCEPTANCE**

**Authoritative successful workflow:** 36378249952  
**Branch:** `phase-35-global-shock-india-volatility-v1`  
**Study window:** 2021-07-01 through 2026-08-31

### Research question

Does a large prior-session global equity shock become more or less monetizable in NIFTY depending on the prior-day India-local IV–RV state after realistic execution costs?

### Data integrity gate

The global/IV–RV feature gate passed:

| Metric | Result |
|---|---:|
| Raw NIFTY sessions | 1,228 |
| Global-feature-eligible sessions | 1,164 |
| Sessions with both GLOBAL_LEAD and IV_RV_Z | 1,144 |
| Feature coverage | 98.28% |
| Prior-information violations | 0 |
| Warm-up/global-unavailable sessions | 64 |

The global signal used the Phase 31.8 six-index construction and a frozen |GLOBAL_LEAD| >= 1.0 trigger. Local state used prior-session ATM IV minus 20-session realized volatility, standardized with a prior-only 60-session window, with LOW <= -0.75 and HIGH >= +0.75.

### Frozen candidate population

Only **17 candidate days** met both the global-shock trigger and a non-neutral IV–RV state:

- HIGH_VOL_STATE: 16 days
- LOW_VOL_STATE: 1 day

The frozen four cells were the two states crossed with 10:30 and 15:10 exits.

### Execution-coverage gate

| State | Exit | Candidate rows | Complete quote rows | Coverage |
|---|---|---:|---:|---:|
| LOW_VOL_STATE | 10:30 | 1 | 0 | **0.0%** |
| LOW_VOL_STATE | 15:10 | 1 | 0 | **0.0%** |
| HIGH_VOL_STATE | 10:30 | 16 | 16 | **100.0%** |
| HIGH_VOL_STATE | 15:10 | 16 | 16 | **100.0%** |

The preregistered gate requires **>=95% execution quote coverage in every true cell**. Because both LOW_VOL_STATE cells fail this requirement, the phase cannot legitimately produce an accepted Base/Stress P&L result.

### Why no trading conclusion is reported

The absence of executable LOW_VOL_STATE observations is a data-coverage failure, not evidence that the strategy loses money. Likewise, the HIGH_VOL_STATE observations cannot be promoted independently because the preregistered rule requires all four true cells to be evaluated before discovery promotion.

Therefore:

- no Base P&L is accepted;
- no Stress P&L is accepted;
- no null-comparison conclusion is accepted;
- no WFA/OOS is authorized;
- no parameter or state threshold may be changed to manufacture coverage;
- the phase is retired as **DATA-LIMITED**.

### Literature context

Existing Indian-market volatility research supports treating IV/RV measurement as a substantive modelling choice rather than a cosmetic feature. Research on Indian NIFTY options has documented a negative variance-risk-premium/market-neutral-straddle effect and found that continuous realized variance can matter for short-horizon variance-risk-premium dynamics. citeturn0search5turn0search7

Recent NIFTY work also reports that the realized-volatility estimator can materially alter measured IV/RV relationships; a 2026 preprint specifically reports estimator sensitivity when comparing close-to-close and Yang–Zhang volatility. citeturn0search1 Another recent study reports regime dependence in NIFTY weekly volatility relationships. citeturn0search3 These findings motivate the preregistered IV–RV state interaction, but they do not establish that this particular global-shock strategy is profitable.

Historical NSE research has also documented evidence of information transmission from US markets into NIFTY overnight returns, providing background motivation for the global-shock component. citeturn0search24

### Strengths

- strict prior-date information barrier;
- pinned NIFTY/options source revision;
- cached global source with per-index SHA-256 manifest;
- explicit local-IV reconstruction;
- prior-only IV–RV standardization;
- deterministic expiry/strike/lot mapping;
- realistic Base/Stress execution costs;
- explicit per-cell quote-coverage gate;
- reproducible workflow with manual dispatch;
- errors preserved in the repository.

### Limitations

The decisive limitation is sample/execution coverage for the LOW_VOL_STATE branch: only one frozen candidate day exists and its required option quotes are unavailable. The phase therefore cannot distinguish absence of an economic effect from absence of measurable executable observations.

The IV estimate is ATM-straddle-implied volatility rather than a full model-free variance measure, and realized volatility is a 20-session close-to-close estimator. These choices were frozen for this phase and were not changed after seeing the coverage outcome.

### Conclusion

Phase 35 did **not** establish a trading result. It established that the preregistered global-shock × IV–RV-state family is not sufficiently executable on the pinned dataset under the required four-cell coverage rule.

The appropriate research action is to preserve this as **DATA-LIMITED negative evidence** and move to the next materially distinct preregistered family rather than alter the state definition or relax the coverage rule.

### Future direction

A future, separately preregistered study could investigate the same economic mechanism using a source with complete option observations for the LOW_VOL_STATE candidates, or a broader sample period/source. Such a study must be treated as a new phase and must not reuse this phase's missing-data outcome to choose a more favorable threshold.

### Key artifacts

- `docs/phase35_plan.md`
- `docs/phase35_status.md`
- `docs/error_log.md`
- `reports/phase35/gate/data_gate.json`
- `reports/phase35/base/execution_coverage.json`
- `reports/phase35/base/execution_debug.json`
- `reports/phase35/base/feature_panel.csv`
- `reports/phase35/stress/feature_panel.csv`
