# Phase 3F OI Repositioning Around Intraday Breaks

## Research question
Does the change in open interest across a fixed daily near-ATM strike band, combined with a same-minute price-structure break, contain incremental intraday directional information after realistic option-trading costs?

## Design
A daily reference ATM strike is fixed from the 09:29–09:31 IST window. OI changes are then measured on the same absolute strikes throughout the day, avoiding the dynamic-ATM contract-mixing problem.

For each expiry type:
- compute 15-minute normalized call-OI change and put-OI change;
- define OI repositioning as normalized call-OI change minus normalized put-OI change;
- detect the first break of the prior 15-minute spot high/low after 09:45;
- test same-sign and inverted OI polarity;
- enter one minute after the event;
- trade a defined-risk debit spread using the current ATM and one/two strikes OTM;
- hold for 30/60/90 minutes.

Grid:
- OI-change threshold: 5%, 10%, 20%;
- breakout buffer: 0%, 0.05%, 0.10%;
- polarity: same-sign/inverted;
- spread width: 1 or 2 strikes;
- hold: 30/60/90 minutes.

The screen stops on its own if the full grid is negative; only a positive, cost-aware configuration would receive a second-stage stop/target or walk-forward treatment.
