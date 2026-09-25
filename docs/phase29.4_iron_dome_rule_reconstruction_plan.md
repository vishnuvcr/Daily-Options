# Phase 29.4 — NIFTY Iron Dome rule reconstruction and formalization freeze

## Objective

Convert the successful Phase 29.3 source-text acquisition into a reproducible rule ledger. The phase must separate facts explicitly supported by the two Equity Income videos from illustrative examples and unresolved mechanics.

No P&L is produced in Phase 29.4.

## Research questions

1. What is explicitly stated about the initial NIFTY structure, strike geometry and wing width?
2. What exactly is the 60% adjustment reference: premium, P&L, price/range or another chart metric?
3. What are the first and second adjustment actions, including which legs move and in which direction?
4. Is the “one strike inside” instruction a fixed part of the second adjustment or an example?
5. What lot ratios are supported by the source?
6. What are the actual entry and exit timing conventions relative to the current Tuesday NIFTY weekly expiry?
7. Which mechanics remain underdetermined after cross-reading both videos?

## Source evidence policy

- Transcript retrieval must remain Python-only and source-caption based; no LLM-generated transcript.
- The Phase 29.3 multi-source fallback remains the acquisition layer.
- Store hashes, timestamps and derived structured facts. Do not commit plaintext transcript.
- Do not infer a rule solely from a payoff chart when the transcript does not define it.
- Label each rule field as EXPLICIT, ILLUSTRATIVE, FORMALIZATION_REQUIRED or UNRESOLVED.

## Deterministic analysis

The Phase 29.4 script will:
1. Fetch both source transcripts with the Phase 29.3 Python acquisition layer.
2. Extract calendar mentions, time mentions, percentages, strike-like numbers, wing-width numbers and adjustment/action keywords.
3. Build a machine-readable fact ledger.
4. Cross-check the two videos for consistent mechanics.
5. Produce a bounded formalization matrix without using any P&L result to choose parameters.

## Preregistered formalization family

The source does not yet support one unique deterministic rule. Therefore any numerical successor must be selected from this frozen, source-anchored family only:

- Underlying: NIFTY weekly options.
- Core: iron-fly / short-straddle with balanced protection.
- Initial illustrated wing width: 200 index points.
- Entry horizon candidates: expiry minus 4, 3 or 2 trading sessions, reflecting the source's stated 2–4 day holding window.
- Initial strike placement candidates: ATM, one strike above ATM, one strike below ATM.
- Adjustment trigger: the source's 60% mark, with the exact metric treated as unresolved until formalized.
- First adjustment candidates: directional roll of the short straddle versus a one-leg directional adjustment, only where the source evidence supports the variant.
- Second adjustment candidate: one-strike-inside / deeper-ITM directional roll as explicitly illustrated.
- Exit anchor: 15:00 on expiry day is source-illustrated; earlier discretionary exits are not allowed in the deterministic test unless separately registered.
- Lot ratio: 1:1:1:1 unless source evidence establishes otherwise.

This is a formalization family, not a claim that every cell is the presenter's exact rule.

## Gate to numerical testing

Phase 30 can open only when:
- every formalization cell has a deterministic entry, trigger, adjustment and exit definition;
- historical NIFTY expiry and lot-size mapping is verified;
- required contract rows exist on entry, adjustment and exit dates;
- execution price model, Paytm Money/NSE transaction costs and Base/Stress slippage are registered;
- no future information enters signal or adjustment decisions.

## Planned statistics for Phase 30

Weekly net P&L after all costs, median weekly net, profitable-week rate, worst week, profit factor, maximum drawdown, expected shortfall/CVaR, trade count, capital efficiency, and nested WFA/OOS plus later-period validation.

## Stop condition

Stop Phase 29.4 when every rule field is either:
- frozen as explicit source evidence,
- frozen as a clearly declared formalization choice from the preregistered family, or
- recorded as a blocker.

Do not start open-ended parameter search.
