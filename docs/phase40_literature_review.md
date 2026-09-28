# Phase 40 — Literature Review

## Research rationale
Phase 40 tests a specific overnight-dislocation mechanism: whether the next-session opening gap is unusual relative to the prior session's option-implied one-session move, with prior implied-versus-realized volatility recorded as context. The literature motivates the mechanism but does not establish profitability of this exact NIFTY strategy.

## 1. NIFTY variance-risk premium and overnight variance
Agarwal (2026) studies 43 million-plus one-minute NIFTY option bars from 2022–2026 and constructs ATM implied volatility and realized volatility, explicitly incorporating overnight gap variance through the Yang-Zhang estimator. The study reports persistent and asymmetric NIFTY variance-risk-premium behavior. This supports measuring implied and realized volatility on the same underlying while treating overnight variation as economically distinct. This is a recent SSRN preprint rather than peer-reviewed confirmation of the present strategy.
Source: https://papers.ssrn.com/sol3/Delivery.cfm/6530119.pdf?abstractid=6530119&mirid=1&type=2

## 2. Overnight versus intraday variance risk premium
Papagelis et al. (2025) decompose the variance risk premium into overnight and intraday components across major markets and report that the overnight component differs materially from the intraday component, with different forecasting behavior by horizon. This motivates a signal centered on the overnight gap rather than treating a full trading day as a homogeneous variance interval.
Source: https://onlinelibrary.wiley.com/doi/10.1002/fut.22589

## 3. Overnight periods in option pricing
Boes, Drost and Werker examine closed-market overnight periods in option pricing and model overnight jumps separately from intraday continuous dynamics. Their results show that overnight jumps materially contribute to option-price risk. This supports the methodological separation of prior-day option information from the following session's opening gap.
Source: https://www.cambridge.org/core/journals/journal-of-financial-and-quantitative-finance/article/abs/impact-of-overnight-periods-on-option-pricing/12C2222725

## 4. Day-night asymmetry in option returns
Muravyev and Ni (2020) document that option returns differ markedly between overnight and intraday periods and relate the pattern to volatility seasonality and option pricing. Although their evidence is from U.S. options, it strengthens the case for testing an explicit overnight-to-open component rather than assuming the same intraday dynamics continue through the close-to-open interval.
Source: https://www.sciencedirect.com/science/article/abs/pii/S0304405X19302193

## 5. Option implied-volatility information and returns
Han and Li (2020) find that aggregate implied-volatility spreads contain predictive information for future stock-market returns and that the effect is connected to option demand and macro information. Phase 40 does not copy that predictor; it uses ATM IV as a volatility-scale input and isolates the gap-to-implied-move dimension.
Source: https://pubsonline.informs.org/doi/full/10.1287/mnsc.2019.3520

## 6. Why the method is deliberately conservative
Phase 40 uses a finite 8-cell grid, fixed null seeds, strict timestamp cutoffs, explicit costs, doubled slippage and a hard data gate. This is important because literature showing predictive information in options does not by itself establish a tradable edge after brokerage, statutory charges and execution friction.

## 7. Key limitations from literature
- Overnight jump behavior differs across markets; U.S. or global evidence is not assumed to transfer to NIFTY.
- Annualized IV scaled by sqrt(1/252) is a one-session benchmark, not a literal model of the non-trading overnight clock.
- Black-Scholes IV inherits price/model error and requires robust quote availability.
- Predictive association between IV/RV or option information and future returns is not equivalent to profitable debit-spread trading after costs.

## References
1. Agarwal, Y. (2026). The Variance Risk Premium in Nifty 50: A Structural Anatomy Across Nine Empirical Filters. SSRN 6530119.
2. Papagelis, G., Dotsis, G., et al. (2025). The Variance Risk Premium Over Trading and Nontrading Periods. Journal of Futures Markets. DOI: 10.1002/fut.22589.
3. Boes, M.-J., Drost, F. C., & Werker, B. J. M. (2007/2009). The Impact of Overnight Periods on Option Pricing.
4. Muravyev, D., & Ni, X. (2020). Why do option returns change sign from day to night? Journal of Financial Economics, 136(1), 219–238.
5. Han, B., & Li, G. (2020). Information Content of Aggregate Implied Volatility Spread. Management Science, 67(2), 1249–1269.