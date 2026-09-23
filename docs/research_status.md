# Research Status

Last updated: 2026-09-24

## Overall
Phase 3G — COMPLETE; FAIL_PRELIMINARY; RETIRED.

## Step log

### 2026-09-24 — Step 3G.2 Corrected Phase 3G result and retirement
- Corrected GitHub Actions run 35916973751 completed successfully after the WFA date-normalization fix.
- Base slippage (0.20 points/leg): all 128 variants had negative mean all-calendar-day net; best mean was Rs -61.11/lot/day.
- Stress slippage (0.40 points/leg): all 128 variants remained negative; best mean was Rs -79.55/lot/day.
- Corrected WFA: 13 test windows; base 1 positive / 13 and mean test-window net Rs -192.79; stress 0 positive / 13 and mean Rs -252.79.
- Bootstrap 95% intervals for mean test-window net remained fully below zero in both friction settings.
- Decision: Phase 3G is retired. No grid expansion is permitted.
- Next bounded hypothesis: derivative price-discovery / option-lead-lag using short-horizon ATM option price changes as the information source and defined-risk spreads as the execution vehicle.

## Previous phase record
See the earlier step log in the repository history for Phases 0–4 and their rejected families.

## Current phase
Phase 3G — COMPLETE; FAIL_PRELIMINARY; RETIRED.
