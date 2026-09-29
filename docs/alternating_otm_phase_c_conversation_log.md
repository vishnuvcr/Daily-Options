# Conversation Log — Alternating OTM Buy/Sell Phase C

2026-09-29: User said "Ok proceed" after the alternating BUY-1/SELL-2 variant was shown to raise win rate materially but remain negative after costs. Phase C was initiated to test a frozen, pre-entry tail-loss exclusion family. The selection rule and discovery/holdout boundary were written before execution.

2026-09-29: First Phase C run 36536750155 failed on a warm-up NaN implementation check. EALTC-001 was logged and corrected without changing the research specification.

2026-09-29: Authoritative Phase C run 36536840710 completed successfully. Discovery-only selection chose first15_abs_ret >= 0.126795% (45th percentile). On untouched 2025+ holdout, Base net P&L became +₹34,446 with 63.16% win rate; Stress remained -₹1,518 with 60.29% win rate. Phase C is closed without promotion and no further threshold tuning on the same holdout is authorized.
