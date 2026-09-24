# Phase 23 Plan — Equity Income YouTube Strategy Discovery

## Purpose
Systematically extract testable options-strategy hypotheses from the Equity Income YouTube channel and route them into the existing research program without treating video claims, examples or payoff diagrams as evidence of profitability.

## Research questions
1. Which distinct option structures and entry/adjustment rules are presented by the channel?
2. Which are genuinely intraday/NIFTY-compatible?
3. Which materially overlap with already-tested families and should be excluded to avoid duplicate research?
4. Which novel hypotheses can be encoded with the existing one-minute NIFTY option data, realistic costs and the information barrier?
5. Do any survive the existing promotion gate: net >= Rs 1,000 per active lot/day, Base and Stress, nested WFA and untouched later OOS?

## Source protocol
- Primary source: Equity Income YouTube channel and individual videos.
- Secondary source: accessible transcript/index pages used only to recover details where the YouTube page does not expose them.
- Independent evidence: academic papers, exchange documentation and historical-data sources.
- Video claims are hypotheses, not validated results.

## Candidate families
A. VIX expected-range / short-strangle or iron-condor air-defense framework.
B. Low-VIX weekly income structure.
C. Low-VIX calendar.
D. Low-VIX diagonal option-selling setup.
E. Bear put spread with explicit adjustment rules.
F. Set-and-strike weekly iron-fly / enhanced iron-fly structure.
G. NIFTY Jade Lizard / downside-protected premium structure.
H. Monthly OTM call debit-spread + further OTM short-call overlay with dynamic roll/hedge steps.
I. Futures/strip or flat-volatility setup as a signal/underlying layer for options.
J. Naked put selling is catalogued for completeness but is not a primary target candidate unless a defined-risk intraday conversion is specified.

## Deduplication
Before numerical testing, compare each candidate to Phase 8-22 frozen families. Existing-equivalent structures are reused only as evidence references; they are not rerun under a new label.

## Scientific execution
For each novel candidate:
1. Formalize exact entry, strike, expiry, stop, target, adjustment and time-out rules.
2. Freeze a minimal preregistered grid.
3. Unit-test contract identity, expiry, option side, timestamp barrier and cost accounting.
4. Run Base and doubled-slippage Stress.
5. Run nested walk-forward.
6. Run independent later-period validation for any candidate that clears preliminary gates.
7. Report mean/median active-day net, win rate, expectancy, PF, drawdown, trade count, concentration, year/regime breakdown and cost sensitivity.

## Promotion
No candidate is promoted from video claims alone. The same >= Rs 1,000 net/active-lot/day and out-of-sample requirements remain in force.

## Phase status
Discovery initiated 2026-09-25.
