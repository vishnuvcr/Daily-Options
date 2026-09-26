# Phase 31.9 — Literature Review and Evidence Matrix

## Why this hypothesis is testable

NSE defines India VIX as a volatility index derived from NIFTY option bid/ask information that reflects expected volatility over the next 30 calendar days. The official NSE historical-data page provides a downloadable historical India VIX series. These properties make India VIX an appropriate prior-session implied-volatility state variable for a strictly lagged regime test.

Official sources:
- India VIX methodology/description: https://www.nseindia.com/static/products-services/indices-indiavix-index
- Historical India VIX: https://www.nseindia.com/reports-indices-historical-vix
- NSE historical reports index: https://www.nseindia.com/static/resources/historical-reports-capital-market-daily-monthly-archives

## Realized volatility and implied/realized variance evidence

Published Indian-market research documents persistence, asymmetry and time-varying behavior in realized volatility. Other India VIX studies report that India VIX contains forward-looking information about realized volatility. More recent NIFTY VRP work reports that implied variance can exceed realized variance in aggregate, while also finding substantial regime dependence and inversion periods.

Relevant sources:
- NSE India VIX forecast/realized-volatility working-paper literature: https://www.nseindia.com/research/content/resPaper69.pdf
- Indian realized-volatility persistence/asymmetry study: https://www.sciencedirect.com/science/article/pii/S1059056017302949
- NIFTY variance-risk-premium study (working-paper context): https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7109738
- Recent NIFTY VRP preprint using large one-minute option data: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7109552
- NIFTY implied/realized variance forecasting paper: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4527476

## Why the experiment uses a ratio rather than VIX alone

A raw VIX level mixes expected volatility and volatility regime. The VIX/RV ratio asks a narrower question: whether the market's implied volatility state is high or low relative to recent realized NIFTY volatility. That makes the regime interpretable and less dependent on the absolute volatility level across years. The ratio is computed using only completed prior-session information to avoid leakage.

## Why opening-gap direction is paired with the ratio

The experiment does not assume that India VIX itself predicts direction. Instead, it tests whether the volatility-regime state conditions an observable opening-gap directional rule. FOLLOW_GAP and FADE_GAP are both tested symmetrically, so the experiment does not prespecify whether continuation or mean reversion should dominate.

## Data hierarchy

1. Official NSE India VIX history is the authoritative volatility-state source.
2. The project's pinned TradeMarkk NIFTY 1-minute parquet cache supplies reproducible NIFTY/opening and option execution bars.
3. Academic and working-paper studies are used only to justify the hypothesis and interpret results; they are not used to select winning parameters after the fact.

## Literature-to-method mapping

| Evidence | Implication for Phase 31.9 |
|---|---|
| India VIX is an option-order-book-based forward volatility measure | Use VIX as a lagged state variable, not a directional predictor. |
| India realized volatility is persistent/time-varying | Use a prior-only rolling RV20 baseline. |
| Implied/realized variance relationships are regime dependent | Use a fixed VIX/RV ratio regime variable. |
| Cross-regime behavior can differ | Test low/mid/high regimes separately. |
| Literature does not establish a costed NIFTY option trading edge | Require a frozen option P&L test with costs, stress and promotion gates. |

## Evidence limitations

The literature does not prove that the proposed opening-gap rule is profitable. Several newer results are working papers/preprints, and their samples, instruments and objectives differ from this experiment. Their role is hypothesis support only. The Phase 31.9 conclusion must come from the preregistered, costed NIFTY option experiment.
