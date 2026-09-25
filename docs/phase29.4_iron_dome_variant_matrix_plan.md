# Phase 29.4 — Pre-registered Iron Dome variant matrix

## Purpose

Freeze a limited, transparent set of interpretations for the unresolved Iron Dome rules before any P&L sweep. This avoids silently choosing one reading of ambiguous source language.

## Source-fidelity principle

The matrix separates:
- source-supported facts (NIFTY weekly Iron Fly family, symmetric 200-point example, 60% adjustment mark, two planned adjustments, expiry-day scenario);
- explicit research interpretations (entry timing, exact 60% definition, adjustment movement and exit).

No variant is presented as the creator's exact rule.

## Pre-registered dimensions

Entry time:
- Wednesday 09:30
- Thursday 09:30
- Friday 09:30

These are chosen because the source says a weekly trade may be held for two to four days, while the current NIFTY weekly expiry is Tuesday. The exact entry day remains unverified.

60% trigger interpretation:
- ZONE_60: adverse underlying move reaches 60% of the 200-point wing distance.
- PNL_60: open loss reaches 60% of the variant's static maximum loss.

Adjustment movement:
- ROLL_CENTER_1_STRIKE: move the short straddle centre one NIFTY strike in the adverse direction.
- ROLL_CENTER_2_STRIKES: move the short straddle centre two strikes.
- SHIFT_THREATENED_LONG_1_STRIKE: move the threatened protective long option one strike inward, reflecting the transcript's one-strike-inside/locking description.

Exit:
- EXPIRY_15: close at 15:00 on the current Tuesday expiry.
- RECOVER_FLAT: close when post-adjustment mark-to-market reaches or exceeds zero; otherwise close at expiry.

## Matrix size

3 entry timings × 2 trigger definitions × 3 adjustment rules × 2 exit rules = 36 variants.

## Hard controls

All variants use:
- NIFTY weekly options;
- one-lot base unit for reporting;
- 200-point initial symmetric wings;
- no future information;
- next-available executable bar rather than same-bar hindsight;
- explicit slippage/transaction costs in Phase 30;
- historical NIFTY lot sizes from dated NSE evidence;
- Paytm Money brokerage/cost model registered before numerical results.

Phase 29.4 computes no P&L and selects no winner.

## Gate to Phase 30

Only the frozen 36-variant registry can be tested. Any additional variant requires a new preregistered branch/change and a logged reason before seeing results.
