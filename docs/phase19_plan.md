# Phase 19 — Global Gap + Intraday Volatility Compression Condor

## Research question
Can overnight global-index information, combined with the NIFTY opening gap and intraday realized-volatility state, identify sessions in which a defined-risk NIFTY iron condor has favorable net expectancy after realistic costs and doubled slippage?

## Why this is distinct
Phase 14 tested global opening information primarily for directional continuation/reversion. Phase 18 tests a standalone low-jump/low-RV iron-condor regime. Phase 19 tests the interaction: global information is used only as a pre-open regime classifier, while the option structure is selected only after an intraday confirmation of volatility compression.

## Frozen grid
2 global thresholds × 2 NIFTY gap thresholds × 2 agreement states × 2 entry times: 10:15 and 13:30 IST × 2 short offsets × 2 wing widths × 2 holds × 2 stops = 512 cells.

Global state:
- standardized latest pre-India S&P 500 / Nasdaq / Nikkei return composite;
- threshold 0.5 or 1.0 standard deviations.

NIFTY gap:
- absolute open-vs-prior-close gap threshold 0.25% or 0.50%.

Regime:
- global gap direction agrees with NIFTY opening gap, or disagrees.

Entry:
- 10:15 / 11:00 / 13:30 IST.
- exact-expiry TradeMarkk data.
- earliest common four-leg quote within 3 minutes after signal.

Risk:
- short offsets 1 or 2 strikes;
- wing widths 1 or 2;
- holds 30 or 60 minutes;
- stops 1.25x or 1.50x entry credit;
- target fixed at 50% credit.
- base/stress slippage ₹0.20/₹0.40 per option leg.

## Promotion
Base and stress must be positive; at least one untouched WFA window must reach ₹1,000 net per active lot/day; no single window may dominate; no result-driven tuning.


## Literature rationale

Recent NIFTY research reports positive variance-risk-premium behavior and strong persistence, while also emphasizing left-tail asymmetry and realistic friction; a 2024 Journal of Futures Markets study documents day/night asymmetry in NIFTY option returns and weaker effects on jump days. These findings motivate a regime classifier that avoids large jumps and uses pre-open global information only as a state variable. See: https://ssrn.com/abstract=6530119 ; https://doi.org/10.1002/fut.22512 .
