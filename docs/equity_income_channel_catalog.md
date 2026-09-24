# Equity Income YouTube Strategy Catalogue

Source channel: https://www.youtube.com/@equityincome
Channel description identifies options selling/buying, risk-managed NIFTY/BankNIFTY setups and weekly-income tactics. Current public indexing reports about 94 videos, but the catalogue below is a research sample, not a claim of exhaustiveness.

## Observed strategy hypotheses

| Candidate | Video/source | What is recoverable | Target fit | Initial overlap |
|---|---|---|---|---|
| VIX expected-range “Air Defense” | Retail Option Sellers Need This First - STRANGLE AIR DEFENSE SYSTEM | Use India VIX + time-to-expiry to estimate 1-sigma/2-sigma range; use the range for short strangles/iron condors; adjust as price approaches strikes. | High, can be made intraday | Distinct enough to test as dynamic strike-selection rule |
| Low-VIX weekly survival structure | Weekly Options Survival Strategy For Low Vix | Low-VIX weekly options structure with adjustment and stop-loss emphasis; exact leg rules require transcript/video reconstruction. | Medium after formalization | Likely overlaps short-vol families; deduplicate first |
| Low-VIX calendar | Low VIX? This Calendar Setup Saves Me | Calendar structure designed for low-VIX conditions with adjustment. | Medium/low for intraday target | New structure, but historical marking quality must be verified |
| Low-VIX diagonal | Retail Option Seller's Diagonal Setup for Low Vix | Diagonal setup for low VIX, with stop-loss and adjustments. | Medium | Distinct structure; executable intraday variant needs exact rules |
| Bear put spread | Bear Put Spread Attack Plan: When to Enter and How to Adjust | Bear put spread, entry/exit and adjustment framework, positioned as a low-monitoring approach. | High if converted to fixed intraday rules | Some overlap with debit-spread family; exact adjustment logic is the differentiator |
| Set & Strike weekly | Set & Strike Weekly Options Method for Working People | Iron-fly-centered weekly structure with additional legs/adjustments. | Low for direct intraday | Defined-risk income family; compare to existing credit/iron structures |
| NIFTY Jade Lizard | Income in 3 Markets? | NIFTY adaptation of Jade Lizard; total premium construction; upside risk can be removed when built correctly; downside remains a key risk; protective put can define downside. | Medium | Distinct structure; can be tested intraday only after exact entry/exit specification |
| Enhanced monthly call overlay | This Payoff Hits like a Missile | Transcript-indexed reconstruction: buy OTM call debit spread, sell a further OTM call chosen from a premium formula, then add an inside call as the short call decays; examples use monthly NIFTY. | Medium/low for strict intraday | Novel multi-leg overlay; currently monthly rather than intraday |
| Futures/strip | Futures Trading for People With Real Jobs | Video description references a futures “Strip” strategy in flat volatility. Exact rules need transcript reconstruction. | Medium as an underlying signal layer | Do not test until exact rules are recovered |
| Naked put | NAKED PUT SELLING RISK?WATCH THIS BEFORE YOU DECIDE | Risk-focused naked-put discussion; exact rules not recovered from accessible result. | Low | Catalogued; defined-risk conversion required before primary testing |

## Sources
- Equity Income channel: https://www.youtube.com/channel/UCxMt2GgYbO6-FCf0p4sAT0A
- “Income in 3 Markets?”: YouTube result published 2026-08-07.
- “STRANGLE AIR DEFENSE SYSTEM”: YouTube result published 2026-04-10.
- “Bear Put Spread Attack Plan”: YouTube result published 2026-01-04.
- “Weekly Options Survival Strategy For Low Vix”: YouTube result published 2026-01-13.
- “Futures Trading for People With Real Jobs”: YouTube result published 2025-12-31.
- “Retail Option Seller's Diagonal Setup for Low Vix”: YouTube result published 2025-12-26.
- “Low VIX? This Calendar Setup Saves Me”: YouTube result published 2025-09-22.
- “Set & Strike Weekly Options Method for Working People”: YouTube result published 2025-06-27.
- “This Payoff Hits like a Missile”: transcript/indexed reconstruction published/analysed in 2026-09; secondary transcript source.

## User-supplied video — formalized from transcript

### Falcon Spread — “Top Hedging Trick Public Won't Know”
- YouTube URL: https://youtu.be/Cl5i-lWAzeo
- Video title: **Falcon Spread - Top Hedging Trick Public Won't Know**.
- Channel: **Equity Income**.
- Published: **4 Jun 2025**.
- Duration: **14:33**.

#### Source-derived strategy rules supplied by the user
1. **Friday initial entry:** open a 5:3 ratio/diagonal strangle for the new weekly cycle. Sell 5 lots of the near/current-week CE and 5 lots of the near/current-week PE, targeting about **25 premium points per short leg**. Buy 3 lots of next-week CE and 3 lots of next-week PE, targeting about **25 premium points per long leg**.
2. **Monday defensive conversion:** after initial weekend/early-week decay, buy 5 lots of the near-week CE one strike above the original short CE strike and buy 5 lots of the near-week PE one strike below the original short PE strike. This caps the near-week short-call and short-put tails while retaining the 3-lot next-week long options.
3. **Risk control:** use a hard stop; the user-supplied transcript summary does not specify the hard-stop threshold numerically, so the backtest must preregister a finite threshold grid rather than invent a value.
4. **Time-out:** close the whole structure by **Wednesday** and do not hold into Thursday/0-DTE expiry.
5. **Premium discipline:** the source emphasizes the approximately **25-point premium zone** and warns against materially tightening the strangle by selling much richer/closer premiums such as 50 points.
6. **Economic intent:** capture weekend/early-week theta while reducing the left/right tail exposure after Monday's adjustment. This is a hypothesis, not evidence of profitability.

#### Formalization choices that are not claimed as source facts
- Friday signal time is not specified in the supplied transcript summary. Phase 24 will therefore test a small preregistered Friday-time sensitivity grid rather than silently selecting a time from results.
- The phrase “matching short premium” does not explicitly state whether the 3-lot far-week options use the same strikes as the near-week shorts or independently selected strikes. The primary reconstruction treats the structure as a **diagonal** and therefore selects far-week strikes independently at approximately the same 25-point premium target; a same-strike interpretation is retained as a sensitivity variant.
- “One strike above/below” means exactly one listed NIFTY strike increment from the original near-week short strike on the same option side.
- “By Wednesday” is implemented as the last available liquid minute on Wednesday before the close, with the exact execution convention fixed before numerical results are accepted.

#### Phase-24 test status
- **Status: READY FOR NUMERICAL VALIDATION.**
- Priority: **high** because the transcript now provides concrete entry, adjustment, expiry and risk-control mechanics for a named multi-leg structure that is distinct from the previously tested credit-spread families.
- No discretionary intraday adjustment will be inserted. Every trade leg, timestamp, strike, expiry, stop and cost must be represented explicitly in the simulator.

## Evidence rule
Descriptions and transcripts can specify a hypothesis. They do not establish profitability. Any numerical result must come from the repository's reproducible backtest pipeline with realistic costs and out-of-sample validation.
