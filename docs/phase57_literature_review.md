# Phase 57 Literature Review

## Opening-range and volatility state

Holmberg, Lönnbark and Lundström (2013) study mechanical Opening Range Breakout strategies and explicitly connect opening-range rules to intraday momentum. Their application to crude-oil futures also shows that results are not invariant over subperiods.

Source:
https://www.sciencedirect.com/science/article/pii/S1544612312000438

Lundström's “Day trading returns across volatility states” finds that ORB results differ materially across volatility states, which directly motivates using opening-range width as a regime variable rather than a universal breakout rule.

Source:
https://swopec.hhs.se/umnees/abs/umnees0861.htm

A 2026 SSRN study on QQQ opening-range breakout sequences reports that opening-range size is associated with subsequent move magnitude, while stressing that the paper is descriptive and does not claim exploitability.

Source:
https://doi.org/10.2139/ssrn.6745958

A 2026 preregistered ORB study reports that several apparent ORB effects disappear under realistic trading costs and multiple-testing controls, reinforcing this project's dual-friction gate.

Source:
https://doi.org/10.2139/ssrn.7428398

A 2025 SSRN paper specifically studies ORB variants on NSE equities using 5/15/30-minute windows and volume filters. Its results are not imported as strategy evidence because the universe, signal, instrument and cost model differ materially from this phase.

Source:
https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5198458

## Research implication

Phase 57 tests opening-range volatility as a conditioning variable for the current opening gap, not a conventional breakout entry. The state is fully defined before the 09:31 trade and is frozen before observing P&L.
