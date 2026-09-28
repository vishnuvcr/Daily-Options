# Phase 38 — Literature Review

## 1. Indian opening-session volatility
Sampath and ArunKumar studied intraday NIFTY volatility and reported a high-volatility opening period that persists through roughly the first 30 minutes, with additional late-session volatility. This supports treating the opening interval as a distinct empirical regime rather than assuming constant intraday variance.

Source: Sampath, A. & ArunKumar, G. (2013), *Do Intraday Volatility Patterns Follow a ‘U’ Curve? Evidence from the Indian Market*, SSRN 2255391.

## 2. Opening-range breakout and continuation
Holmberg, Lönnbark and Lundström evaluated mechanical opening-range breakout rules and argued that early large price movements can identify days with stronger intraday movement. Their empirical application was to crude-oil futures, so it is mechanism evidence rather than NIFTY-specific proof.

Source: *Assessing the profitability of intraday opening range breakout strategies*, Finance Research Letters 10(1), 2013. DOI: 10.1016/j.frl.2012.09.001.

## 3. Range-based realized-volatility measurement
Martens and van Dijk proposed realized range as a more efficient volatility estimator than some realized-variance constructions under plausible market microstructure frictions. Phase 38 uses a simple OHLC range ratio rather than adopting their estimator wholesale; the literature is used to motivate range information as a volatility-state variable.

Source: Martens, M. & van Dijk, D. (2007), *Measuring volatility with the realized range*, Journal of Econometrics 138(1), 181–207.

## 4. Recent opening-range evidence and caution on costs
A 2026 SSRN paper by Fetna reports a preregistered multi-cell ORB study and concludes that its tested ORB variants did not survive realistic futures trading costs. This is recent external evidence that gross intraday pattern discovery can be erased by execution friction, reinforcing the Phase 38 Base/Stress promotion gate.

Source: Fetna, M. (2026), *Opening-Range Breakout Does Not Survive Trading Costs: A Pre-Registered 225-Cell Study on Sixteen Years of Futures Data*, SSRN 7428398.

## 5. Recent one-minute breakout/retest work
A 2026 exploratory SSRN study on QQQ one-minute data documents associations between opening-range size, breakout/retest dynamics and subsequent outcomes, while explicitly cautioning that its findings are descriptive and do not establish causal exploitability. Phase 38 therefore tests a pre-specified NIFTY price-structure/volatility state without treating the literature as a claim of profitability.

Source: Pineda, M. (2026), *ANATOMY OF THE RETEST IN THE QQQ OPENING RANGE BREAKOUT*, SSRN 6745958.

## Research gap
The reviewed evidence motivates an auditable NIFTY-specific test of early-range volatility state plus early directional sign, but does not establish a tradable NIFTY options edge after costs. Phase 38 is therefore framed as a finite falsifiable experiment, not as confirmation of ORB profitability.

## Public sources
- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2255391
- https://www.sciencedirect.com/science/article/pii/S1544612312000438
- https://ideas.repec.org/a/eee/econom/v138y2007i1p181-207.html
- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7428398
- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6745958
