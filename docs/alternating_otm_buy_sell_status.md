# Status — Alternating OTM Buy/Sell Variant

Branch: `strategy/alternating-otm-buy-sell-v1`
Status: Phase A/B pending clean workflow.

Frozen variant:
- BUY 1 OTM1 CE
- SELL 2 OTM2 CE
- BUY 1 OTM1 PE
- SELL 2 OTM2 PE
- Same timestamps, expiry selection, lot sizing, costs and slippage as the original study.

Comparator:
- Original backspread: SELL 1 OTM1 + BUY 2 OTM2 on each side.
- Original clean result: Base -₹717,921.87; Stress -₹874,857.87; win rate 25.81% / 23.90%.

No conclusion about the alternating variant is accepted until its clean Base/Stress workflow completes.
