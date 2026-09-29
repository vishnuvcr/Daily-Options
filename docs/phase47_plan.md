# Phase 47 — Opening-Gap Magnitude Normalized by Prior-Day Range × Gap Direction

## Research question

Does the magnitude of the NIFTY opening gap relative to the immediately preceding session's high-low range contain information about continuation versus reversal that is economically useful after realistic NSE/Paytm Money costs?

## Literature/data rationale

Opening gaps have documented post-gap directional behavior and the effect is known to vary with gap size. Plastun et al. (2020) document abnormal post-gap price movement and temporary momentum in US indices. A recent 2026 global-index study also finds opening-gap series are heavy-tailed and volatility-clustered, motivating normalization rather than using raw gap points alone.

A useful practitioner normalization is gap size divided by the previous session's high-low range. Steenbarger's historical S&P 500 analysis used exactly this normalization and reported that it separates relatively small from relatively large gaps across changing volatility regimes; its 40%-of-prior-range threshold is used only as literature context, not as evidence for NIFTY profitability.

Recent NIFTY gap analyses likewise report materially different behavior across gap-size regimes. These are descriptive external evidence only; no external result is used to select Phase 47 parameters.

Sources:
- https://www.sciencedirect.com/science/article/pii/S1062940820300747
- https://pmc.ncbi.nlm.nih.gov/articles/PMC10017064/
- https://www.sciencedirect.com/science/article/pii/S2214845026000918
- https://traderfeed.blogspot.com/2006/11/do-opening-gaps-tend-to-fill.html
- https://www.youtube.com/watch?v=V2iuxDzV2l8

## Frozen feature construction

Signal date t:
- Prior completed session range = prior-session NIFTY 15:10-session high minus prior-session 15:10-session low.
- Opening gap = current 09:15 NIFTY open / prior-session 15:10 close - 1.
- Gap-range ratio = absolute price gap / prior-session high-low range.
- A zero gap is NO_TRADE.
- The ratio uses only information available before 09:15 on date t.

Frozen states:
- SMALL_REL_GAP: ratio < 0.20
- MEDIUM_REL_GAP: 0.20 <= ratio < 0.40
- LARGE_REL_GAP: ratio >= 0.40

The 0.40 boundary is motivated by the published range-normalized gap literature; 0.20 creates a finite three-state partition around small/common versus materially large gaps. These thresholds are frozen and cannot be changed after results.

## Frozen execution

For every state:
- FOLLOW_GAP and FADE_GAP.
- Entry 09:31 IST using the option open.
- Exit 10:30 or 15:10 IST using the option close.
- One-lot 200-point ATM directional debit spread.
- ATM = nearest ₹50 strike to 09:30 NIFTY close using deterministic half-up rounding.
- Nearest NIFTY expiry on/after the current trading date.
- Historical NIFTY lot sizes.
- Existing Paytm Money/NSE/statutory cost model.
- Base slippage ₹0.20 and Stress slippage ₹0.40 per option-price unit/order.

## Discovery matrix and controls

3 relative-gap states × 2 direction mappings × 2 exits = 12 true cells.

Five fixed state-label permutation nulls per cell, seeds 101/202/303/404/505. Nulls permute the prior-only state labels across eligible dates while preserving same-day gap direction and all execution prices.

## Data gates

- At least 95% session/feature eligibility over the study window.
- At least 95% valid prior-day range and prior close coverage among candidate sessions.
- Zero prior-information violations.
- Deterministic expiry, strike and lot mapping.
- At least 95% execution quote coverage in every true cell.
- Accounting reconciliation.

## Promotion gate

In both Base and Stress:
- mean weekly net >= ₹5,000;
- median weekly net >= ₹5,000;
- positive-week rate >= 70%;
- execution coverage >= 95%;
- clean accounting.

No WFA/OOS is authorized unless at least one frozen true cell clears the full gate in both friction regimes.

## Statistical analysis

Primary:
- weekly net P&L distribution;
- mean/median weekly net;
- positive-week rate;
- total net P&L;
- worst week and maximum drawdown;
- execution coverage;
- accounting reconciliation.

Secondary:
- state and direction sample sizes;
- Base versus Stress degradation;
- comparison of true-cell performance with the matched permutation-null distributions;
- descriptive effect of the ratio state on continuation/fade outcomes.

No post-result state selection or threshold optimization is permitted.

## Stop rule

If no frozen cell passes the dual-friction promotion gate, Phase 47 closes as negative discovery. No threshold tuning, exit substitution, or state redefinition is allowed.
