# Conversation and Decision Log

## 2026-09-24 — Phase 4 completion

- User asked to continue the Daily-Options research from the prior chat.
- Repository state was verified before proceeding.
- The corrected Phase 4 GitHub Actions run 35912159508 completed successfully.
- Nested walk-forward result: 22 selected test windows, 8 positive, 0 target-qualified, mean selected test-window net Rs -64.23/lot.
- Decision: retire the prior intraday ATM short-straddle family as a lead candidate rather than run another unconstrained parameter sweep.
- This log records user-visible requirements, decisions, evidence and outcomes; it does not record private hidden chain-of-thought.

## 2026-09-24 — Next bounded hypothesis

- External 2026 NIFTY research indicates OI repositioning is better interpreted as a reaction/state variable around structural price breaks than as a stable advance predictor.
- Decision: test dynamic price-structure breaks first, OI repositioning second, and use a defined-risk debit spread for implementation.
- Next branch: phase-3g-oi-confirmed-breakout.


## 2026-09-24 — Phase 3G completion
- Accepted run 35916600082 completed the corrected forward-OI implementation and generated 79,888 executable paths across 128 pre-registered variants.
- All variants were negative after costs at base and stress slippage; best calendar-day mean was about Rs -61/lot/day at base and Rs -80/lot/day under stress.
- Corrected WFA recomputation produced 13 test windows per friction level, with only 1 positive base window and none positive under stress.
- Decision: retire Phase 3G without further tuning.
- Next research family: derivative price-discovery / option-price lead-lag, motivated by evidence that derivatives can lead the cash index intraday. This family will use a small pre-registered grid and defined-risk spreads.
