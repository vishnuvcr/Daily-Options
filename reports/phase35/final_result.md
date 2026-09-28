# Phase 35 — Global Overnight Shock × NIFTY Option Volatility Structure
## Final Result

**Decision:** RETIRED — economic promotion gate failed. No WFA/OOS or parameter tuning authorized.

**Authoritative workflow:** 36342637912  
**Branch:** `phase-35-global-shock-options-structure-v1`  
**Study window:** 2021-07-01 through 2026-08-31

### Research question

Does the magnitude of a completed global overnight equity-market shock, rather than its direction, predict a monetizable short-horizon NIFTY volatility response after realistic execution costs?

### Frozen experiment

Two prior-only global features were tested:

- `GLOBAL_ABS`: absolute mean six-index standardized shock.
- `US_ASIA_DISPERSION`: absolute standardized US-versus-Asia return separation.

Thresholds were 1.0 and 1.5. The option structures were a one-lot ATM long straddle and a one-lot 200-point long strangle, entered at 09:31 IST and exited at 10:30 or 15:10 IST. Nearest eligible NIFTY expiry, historical lot size, Paytm Money/NSE/statutory charges and Base/Stress slippage were frozen before computation.

### Data and integrity gate

The gate **passed**:

| Check | Result |
|---|---:|
| Raw NIFTY sessions | 1,228 |
| Feature-eligible sessions | 1,164 |
| Global feature coverage | 100.00% |
| Required coverage | 95.00% |
| Prior-date/look-ahead violations | 0 |
| Study window | 2021-07-01 → 2026-08-31 |
| Global source | Yahoo Finance via yfinance |
| Global indices | S&P 500, NASDAQ, Nikkei, Hang Seng, DAX, KOSPI |

The cached global data manifest and hashes are persisted in the Phase 35 gate artifact.

### Frozen discovery results

All 16 cells were negative in both Base and Stress. The promotion gate required mean weekly net >= ₹5,000, median weekly net >= ₹5,000 and >=70% positive weeks in **both** friction settings.

| Feature | Thresh. | Structure | Exit | Base mean/wk | Base median/wk | Base +wk | Stress mean/wk | Stress median/wk | Stress +wk |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|
| GLOBAL_ABS | 1.0 | Straddle | 10:30 | -₹261.16 | -₹341.91 | 23.2% | -₹320.10 | -₹394.48 | 23.2% |
| GLOBAL_ABS | 1.0 | Straddle | 15:10 | -₹370.50 | -₹826.15 | 34.8% | -₹427.61 | -₹876.13 | 34.8% |
| GLOBAL_ABS | 1.0 | Strangle | 10:30 | -₹215.00 | -₹267.09 | 18.8% | -₹273.94 | -₹336.06 | 16.1% |
| GLOBAL_ABS | 1.0 | Strangle | 15:10 | -₹178.79 | -₹578.12 | 25.0% | -₹232.24 | -₹622.40 | 25.0% |
| GLOBAL_ABS | 1.5 | Straddle | 10:30 | -₹235.97 | -₹293.16 | 16.2% | -₹286.76 | -₹333.14 | 16.2% |
| GLOBAL_ABS | 1.5 | Straddle | 15:10 | -₹199.77 | -₹1,073.55 | 29.7% | -₹249.26 | -₹1,133.52 | 29.7% |
| GLOBAL_ABS | 1.5 | Strangle | 10:30 | -₹150.28 | -₹225.17 | 18.9% | -₹201.06 | -₹265.15 | 18.9% |
| **GLOBAL_ABS** | **1.5** | **Strangle** | **15:10** | **-₹139.27** | **-₹716.41** | **24.3%** | **-₹186.93** | **-₹756.39** | **24.3%** |
| US_ASIA_DISPERSION | 1.0 | Straddle | 10:30 | -₹439.71 | -₹533.69 | 28.8% | -₹531.12 | -₹599.82 | 26.3% |
| US_ASIA_DISPERSION | 1.0 | Straddle | 15:10 | -₹1,131.38 | -₹1,206.34 | 34.3% | -₹1,219.79 | -₹1,254.95 | 33.8% |
| US_ASIA_DISPERSION | 1.0 | Strangle | 10:30 | -₹429.75 | -₹389.24 | 21.3% | -₹521.10 | -₹496.91 | 19.8% |
| US_ASIA_DISPERSION | 1.0 | Strangle | 15:10 | -₹747.13 | -₹752.64 | 24.9% | -₹829.68 | -₹811.60 | 23.4% |
| US_ASIA_DISPERSION | 1.5 | Straddle | 10:30 | -₹531.38 | -₹420.44 | 25.4% | -₹598.17 | -₹489.04 | 23.1% |
| US_ASIA_DISPERSION | 1.5 | Straddle | 15:10 | -₹925.96 | -₹798.60 | 33.8% | -₹990.50 | -₹844.57 | 33.1% |
| US_ASIA_DISPERSION | 1.5 | Strangle | 10:30 | -₹462.52 | -₹325.48 | 17.8% | -₹529.44 | -₹387.80 | 17.1% |
| US_ASIA_DISPERSION | 1.5 | Strangle | 15:10 | -₹604.56 | -₹652.00 | 26.4% | -₹664.77 | -₹697.17 | 25.6% |

**Best frozen cell by mean weekly net:** GLOBAL_ABS ≥1.5, 200-point strangle, 09:31→15:10.

- Base: total net **-₹5,153.10** across 37 weeks; mean **-₹139.27/week**; median **-₹716.41**; 24.32% positive weeks; max drawdown **-₹23,016.67**.
- Stress: total net **-₹6,916.32**; mean **-₹186.93/week**; median **-₹756.39**; 24.32% positive weeks; max drawdown **-₹23,556.43**.

The strongest cell is therefore approximately **₹5,139/week below** the mean target in Base and **₹5,187/week below** it in Stress. No cell approached the ₹5,000/week gate.

### Cost/accounting check

For the strongest Base cell:

- Raw gross: **+₹1,561.25**
- Slippage: **₹1,817.50**
- Transaction/statutory costs: **₹4,896.85**
- Net: **-₹5,153.10**

Stress raises slippage to **₹3,581.50**, producing **-₹6,916.32** net.

Thus the negative result is not a reporting-sign error: the stored accounting identity is raw gross − slippage − transaction costs = net.

### Permutation-null controls

Five fixed full-panel permutation seeds were run. For the strongest true cell (GLOBAL_ABS 1.5 / STRANGLE / 15:10), the null mean-weekly results were:

| Seed | Base mean/wk | Stress mean/wk |
|---:|---:|---:|
| 101 | -₹38.10 | -₹79.04 |
| 202 | +₹362.02 | +₹327.73 |
| 303 | -₹737.14 | -₹777.46 |
| 404 | -₹798.56 | -₹837.06 |
| 505 | +₹246.17 | +₹202.48 |
| **True** | **-₹139.27** | **-₹186.93** |

The true cell does not outperform all five null realizations and sits inside the permutation range. With only five fixed null seeds, this is a control rather than a formal small-sample p-value.

### Interpretation

The experiment does **not** support the proposition that a large prior global overnight shock, by itself, can be monetized reliably through the tested long-volatility structures at the specified 09:31 entry and fixed exits.

The weaker performance of the US/Asia-dispersion feature relative to the absolute global-shock feature is descriptive evidence from this frozen grid, not a reason to retune the feature.

### Decision

- **0/16** Base cells passed the discovery gate.
- **0/16** Stress cells passed the discovery gate.
- No WFA/OOS was authorized.
- No threshold, structure, expiry, exit, or friction retuning is authorized from these results.
- Phase 35 options-structure is **retired** and preserved as negative evidence.

### Strengths

Strict prior-information barriers, cached source data, a complete finite grid, realistic Base/Stress friction, deterministic contract selection, fixed null controls, and explicit accounting reconciliation reduce several common backtest failure modes.

### Limitations

The global inputs are daily index closes from Yahoo Finance rather than exchange-native global feeds; the test uses a fixed one-lot sizing rule and only two long-volatility structures; and the five-null design is intentionally small and should not be interpreted as a formal hypothesis-test p-value.

### Future research

The next research step should be a separately versioned, independently preregistered mechanism rather than a parameter search over this failed grid. A global-shock × India-local IV/RV-state hypothesis already exists in the repository as a preregistration, but it should be treated as a separate phase/sub-phase with its own executable workflow and frozen acceptance criteria before numerical execution.

### Provenance

Key artifacts:
- `docs/phase35_plan.md`
- `docs/phase35_status.md`
- `docs/phase35_error_log.md`
- `reports/phase35/gate/data_gate.json`
- `reports/phase35/base/true_cell_summary_base.csv`
- `reports/phase35/base/true_cell_summary_stress.csv`
- `reports/phase35/base/null_summary_base.csv`
- `reports/phase35/base/null_summary_stress.csv`

The workflow's only execution failure was a repository-persistence race during the first artifact push; the numerical Base/Stress calculations themselves completed successfully and the artifacts were subsequently persisted and audited.
