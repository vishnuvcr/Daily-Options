# Phase 36 Literature Review — Global Shock Breadth / Cross-Market Disagreement

## Rationale

Global equity returns do not transmit uniformly. The literature distinguishes return spillovers, volatility spillovers, temporal proximity, contagion/comovement and sentiment-related commonality. That motivates testing whether an aggregate global shock is informative differently when it is broad-based across source markets versus internally split.

### Diebold & Yilmaz (2009)
The authors propose separate return and volatility spillover measures and document economically important variation in both across global equity markets, including bursts in volatility spillovers. This supports treating international transmission as a conditional, time-varying phenomenon rather than a single fixed coefficient. https://onlinelibrary.wiley.com/doi/10.1111/j.1468-0297.2008.02208.x

### Connolly & Wang (2003)
This study reports that foreign market returns can materially influence subsequent domestic returns and explicitly examines intraday and overnight international comovement. This supports a strict non-overlapping information barrier for an India-open test. https://www.sciencedirect.com/science/article/pii/S0927538X02000604

### Return spillover network evidence
A 2019 network study of 40 stock markets finds that market variables explain time-varying spillover connectivity and that temporal distance between markets matters for information propagation. The present phase therefore uses only completed source-market sessions strictly before the NIFTY trade date. https://www.sciencedirect.com/science/article/pii/S0264999317310519

### International comovement and sentiment
Frijns, Verschoor and Zwinkels (2017) find that international equity comovements have increased and that non-fundamental components linked to investor sentiment explain a substantial part of comovement. This motivates distinguishing broad consensus from split cross-market moves. https://www.sciencedirect.com/science/article/pii/S1042443117300963

### Disagreement and expected returns
Yu (2011) documents predictive relations between portfolio disagreement and subsequent market returns. That evidence is not directly equivalent to cross-index return-sign breadth, but it motivates testing whether internally heterogeneous market information carries different pricing implications. https://www.sciencedirect.com/science/article/pii/S0304405X10001807

## Research gap
The present test is deliberately narrower than these papers: it asks whether a fixed NIFTY defined-risk debit spread performs differently when a frozen aggregate global shock is broad-based across six markets versus split. It does not claim that breadth itself is a structural state variable or that spillover implies a tradeable edge.

## Methodological implication
The null design jointly permutes the six-market z-score vector as a block. This preserves cross-market dependence and breadth structure within each permuted vector while destroying date alignment with NIFTY outcomes.
