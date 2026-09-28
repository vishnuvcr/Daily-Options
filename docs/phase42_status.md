# Phase 42 Status

**State: PREREGISTERED / ENGINEERING**

Branch: `phase-42-option-day-night-asymmetry-v1`

Phase 41 is closed DATA-LIMITED. Phase 42 is a distinct family based on prior-session option day–night return asymmetry.

### Required phases
1. Unit tests
2. Pinned source acquisition/reuse
3. Feature data gate
4. Base discovery
5. Stress discovery
6. Five-seed null controls
7. Accounting and artifact validation
8. Final manuscript/closure

No result is accepted until the complete sequence passes.


## Rerun checkpoint — E0417
Run 36468978862 was quarantined before any P&L because the gate code attempted ATM construction from a missing prior-session NIFTY close. E0417 is fixed by an explicit finite-price guard; the hypothesis, gates, dates, thresholds, execution and friction model remain unchanged. Fresh authoritative rerun required.
