# Phase 29.3 — Iron Dome source-derived rule reconstruction

## Source evidence

Two Equity Income videos were fetched by Python tooling:

- 5xz7X5QsFv8 — published 2026-04-30.
- 9cetNfglyO4 — published 2026-05-02.

The transcript fetch was successful for both after the workflow added a yt-dlp auto-caption fallback. No transcript plaintext is stored in this repository; the research artifact stores hashes and short timestamped evidence snippets.

## High-confidence facts

1. The strategy is presented as a NIFTY weekly Iron Dome built from an Iron Fly / short-straddle core.
2. The first video explicitly demonstrates a balanced-wing example around a 23,900 centre: sell 23,900 and buy the call 200 points above and put 200 points below. This describes the illustrated example; it is not evidence that 23,900 is a universal live entry strike.
3. The source explicitly discusses holding the weekly trade for roughly two to four days.
4. The source explicitly refers to a 60% mark as an adjustment point.
5. The source shows Monday morning 9:30 and Tuesday morning adjustment/exit scenarios.
6. The second video is labelled as part two and describes the same NIFTY Iron Dome family, including moving a leg one strike inside and a later locking-style adjustment.
7. The second video explicitly shows a 3:00 p.m. expiry-day scenario and says the adjustment is intended to allow theta decay toward the end of the weekly series.
8. The source describes only two planned adjustments, with the timing treated as important/non-negotiable.

## What is NOT yet deterministic

The transcript evidence does not provide a clean machine-readable rule for:

- the exact entry weekday/time;
- how the initial centre strike K0 is selected algorithmically;
- whether the 60% trigger is defined from max-profit, max-loss, payoff-range position, or another graphical threshold;
- the exact first adjustment leg sequence in every market direction;
- the exact second adjustment strike formula;
- the exact exit rule when neither stop nor expiry is reached;
- whether the illustrated 200-point wings are universal or an example;
- the exact quantity/lot ratio for each leg.

The captions also contain repeated fragments, so ambiguous wording must not be promoted to a fact.

## Provisional coding envelope

For research only, a candidate implementation may represent the family as:

- NIFTY weekly Iron Fly;
- short ATM/selected-centre call + put;
- symmetric long wings at K0 ± 200 as one explicit variant;
- maximum two adjustments;
- adjustment trigger parameterized as a 60%-mark candidate;
- expiry-day exit and early exit represented separately;
- all costs/slippage applied later.

This is a **research hypothesis**, not a claim that it is the creator's exact executable rule.

## Data readiness

The pinned TradeMarkk NIFTY source contains 267 expiry Parquet files at revision 51ca58c. The files relevant to the source dates include 2026-04-28, 2026-05-05, 2026-05-12 and 2026-05-19. Their verified schema contains timestamp, strike, option_type, expiry, OHLCV and open_interest fields.

The independent Rissin source remains useful for replication, but this phase has not proven exact contract-level leg coverage for the reconstructed rule.

## Research decision

Do not start a single-rule P&L backtest as though the source rule were fully known. The appropriate next step is a **pre-registered variant sweep** over the explicitly identified ambiguities (entry timing, 60% trigger definition, adjustment formula and exit), with the source evidence frozen and all variants penalized for slippage, brokerage, statutory charges and lot-size changes. Any variant that survives must then undergo walk-forward/out-of-sample testing.
