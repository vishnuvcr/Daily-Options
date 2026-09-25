# Equity Income / Iron Dome literature review

## Research role
This review is contextual evidence for Phase 29.5–30. It does not override the source-faithful Equity Income rules, add parameters, or select a winner. The numerical experiment remains frozen and must be judged on its own historical data, costs, walk-forward validation and later-period OOS.

## Core findings

### Indian volatility-risk-premium evidence
Garg and Vipul (2015, Journal of Futures Markets) document a volatility risk premium in Indian options and report that option-strategy returns exploiting the premium are substantially reduced once normal transaction costs are included. This supports keeping transaction costs inside the primary performance metric rather than reporting gross option premium capture alone.

Bhat (2021, Global Business Review) studies short-volatility strategies in exchange-traded USDINR options and reports that statistically significant pre-cost returns can become insignificant or negative after bid-ask and brokerage costs. The instrument differs from NIFTY, but the implementation-cost warning is directly relevant to short-volatility strategy research.

Jain (2019, Journal of Futures Markets) finds that implied volatility has predictive content for future volatility in Indian equity options and documents systematic risk-premium features in the market. This provides background for why short-volatility strategies may have an economic source of return without implying that any specific retail strategy is profitable after costs.

### Defined-risk / condor evidence
Niblock's study of condor option spreads in Australia reports that some condor constructions produced reasonable nominal and risk-adjusted results over its sample. This is cross-market evidence and is not directly transferable to NIFTY weekly options.

Chaput (2005, Journal of Futures Markets) examines volatility-trade design and finds that traders' observed structure choices are associated with low deltas and low transaction costs, among other properties. The paper also notes that condors and iron butterflies are less frequently traded than several simpler volatility structures. This supports explicitly tracking execution burden and adjustment count.

### Recent NIFTY-specific evidence
Pillai (2026, SSRN working paper) tests several NIFTY 50 short-volatility strategies with explicit STT, brokerage and slippage assumptions and reports negative net results across its tested families, with tail risk a major driver. Because this is an SSRN working paper rather than a peer-reviewed settled result, it is treated as emerging evidence only.

John (2026, ResearchGate preprint) studies a walk-forward, transaction-cost-aware NIFTY volatility-risk-premium strategy around the post-2024 derivatives-market regime. It is similarly treated as emerging, non-peer-reviewed evidence and is not used to change Phase 30 parameters.

## Methodological implications for this project
1. Gross premium capture is not sufficient evidence of profitability.
2. Brokerage, statutory charges and execution slippage must remain in the headline P&L.
3. Tail-loss metrics, worst week and drawdown must be reported alongside mean and median weekly net.
4. A high positive-week percentage by itself is insufficient because rare tail losses can dominate aggregate economics.
5. Cross-market evidence cannot substitute for NIFTY-specific OOS validation.
6. Recent preprints should be cited as literature context, not treated as established consensus.

## References
Garg, S., & Vipul (2015). Volatility Risk Premium in Indian Options Prices. Journal of Futures Markets, 35, 795–812. DOI: 10.1002/fut.21680.
Bhat, A. (2021). The Profitability of Volatility Trading on Exchange-traded Dollar-rupee Options: Evidence of a Volatility Risk Premium? Global Business Review. DOI: 10.1177/09721509211046169.
Jain, S. (2019). Indian equity options: Smile, risk premiums, and efficiency. Journal of Futures Markets, 39, 150–163. DOI: 10.1002/fut.21971.
Chaput, J.-P. (2005). Volatility trade design. Journal of Futures Markets. DOI: 10.1002/fut.20142.
Niblock, S. J. Flight of the Condors: Evidence on the Performance of Condor Option Spreads in Australia. Applied Finance Letters, 6(1). DOI: 10.24135/afl.v6i01.69.
Pillai, S. (2026). Trading the Volatility Risk Premium on Nifty 50: Strategy Backtest with Realistic Frictions. SSRN, posted June 24, 2026.
John, A. R. (2026). Harvesting the Volatility Risk Premium in Nifty Index Options: Out-of-Sample Evidence and the Post-2024 Regulatory Regime Break. ResearchGate preprint, August 2026.