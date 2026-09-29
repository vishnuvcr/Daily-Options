# Phase 47 Literature Review

## Gap anomaly and continuation/reversal

Plastun, Sibande, Gupta and Wohar (2020), *Price gap anomaly in the US stock market: The whole story*, study DJI, S&P 500 and NASDAQ gaps over 1928–2018 and report abnormal post-gap price movement, with a temporary momentum component. This supports testing both continuation and reversal rather than assuming that every gap fills.

Link: https://www.sciencedirect.com/science/article/pii/S1062940820300747

A 2023 open-access study on opening gaps across S&P 500, Nasdaq100 and Russell 2000 stocks finds that gap openings contain information about subsequent price adjustment and that the response differs by gap direction and size. It also emphasizes that gap events can arise from overnight information shocks.

Link: https://pmc.ncbi.nlm.nih.gov/articles/PMC10017064/

A 2026 paper on 24 global stock indices documents that opening-gap series are heavy-tailed and exhibit volatility clustering and calendar structure. That is relevant to why raw gap points should not be treated as a constant measure of shock magnitude.

Link: https://www.sciencedirect.com/science/article/pii/S2214845026000918

## Range-normalized gap magnitude

Brett Steenbarger's historical gap study explicitly normalizes the opening gap by the prior day's high-low range, arguing that this removes part of the changing-volatility effect. The study uses 20% and 40% reference levels in S&P 500 data and reports materially different fill behavior for small versus large normalized gaps. This is practitioner evidence, not NIFTY-specific academic validation, and is used only to motivate the frozen Phase 47 state boundaries.

Link: https://traderfeed.blogspot.com/2006/11/do-opening-gaps-tend-to-fill.html

## Recent NIFTY evidence

A September 2026 Trading with Groww video reports a 6.5-year NIFTY gap backtest and explicitly separates small, medium and large opening gaps before examining continuation and gap-fill behavior. Because the study excludes brokerage, tax, bid-ask and slippage, its results are not used as strategy evidence; it is included as a current Indian-market research lead only.

Link: https://www.youtube.com/watch?v=V2iuxDzV2l8

A 2026 NIFTY gap-history analysis reports that large gaps are relatively rare and behave differently from routine openings. This is descriptive third-party evidence and is not used to set Phase 47 thresholds.

Link: https://intradaylab.com/blog/nifty-gap-up-history-analysis

## Research implication

The literature supports a bounded test of gap magnitude and normalization, but does not establish that a NIFTY options strategy will be profitable after friction. Phase 47 therefore uses a fixed finite grid, permutation nulls, realistic costs and a dual-friction promotion gate rather than importing published win rates or fill rates.
