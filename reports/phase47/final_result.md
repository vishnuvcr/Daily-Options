# Phase 47 — Opening-Gap Magnitude Normalized by Prior-Day Range Result

## Authoritative execution

- Workflow: **36538234322**
- Branch: phase-47-gap-range-normalization-v1
- Artifact: **11019930108**
- Artifact SHA-256: **18abce8a6f8c72bf2e3bc7962570818ebe5880501832450b6e0d7093d165d54b**

## Data integrity

- Study sessions: 1,228
- Feature-eligible sessions: **1,219 / 1,228 = 99.267%**
- Prior-range validity: **100%** among eligible sessions
- Expiry mapping: **100%**
- Prior-information violations: **0**
- 267 exact-expiry option files available
- Execution coverage across all true cells: **98.56% to 100%**
- Base and Stress accounting: **reconciled**

## True-cell results

| State | Mapping | Exit | Base mean/wk | Base median/wk | Base positive weeks | Stress mean/wk | Stress median/wk | Stress positive weeks |
|---|---|---|---:|---:|---:|---:|---:|---:|
| SMALL_REL_GAP | CONTINUE | 10:30 | -₹274 | -₹440 | 36.8% | -₹323 | -₹480 | 36.8% |
| SMALL_REL_GAP | CONTINUE | 15:10 | -₹771 | -₹1,012 | 31.6% | -₹819 | -₹1,072 | 31.6% |
| SMALL_REL_GAP | FADE | 10:30 | -₹14 | ₹86 | 52.6% | -₹63 | ₹46 | 52.6% |
| SMALL_REL_GAP | FADE | 15:10 | ₹391 | ₹540 | 63.2% | ₹343 | ₹500 | 63.2% |
| MEDIUM_REL_GAP | CONTINUE | 10:30 | -₹513 | -₹454 | 25.0% | -₹563 | -₹484 | 18.8% |
| MEDIUM_REL_GAP | CONTINUE | 15:10 | -₹1,223 | -₹1,360 | 25.0% | -₹1,271 | -₹1,400 | 25.0% |
| MEDIUM_REL_GAP | FADE | 10:30 | -₹60 | -₹175 | 31.3% | -₹109 | -₹222 | 31.3% |
| **MEDIUM_REL_GAP** | **FADE** | **15:10** | **₹714** | **₹301** | **62.5%** | **₹666** | **₹271** | **62.5%** |
| LARGE_REL_GAP | CONTINUE | 10:30 | -₹687 | -₹714 | 29.7% | -₹881 | -₹861 | 29.0% |
| LARGE_REL_GAP | CONTINUE | 15:10 | -₹851 | -₹1,468 | 36.3% | -₹1,042 | -₹1,639 | 35.5% |
| LARGE_REL_GAP | FADE | 10:30 | -₹669 | -₹779 | 34.4% | -₹864 | -₹973 | 30.9% |
| LARGE_REL_GAP | FADE | 15:10 | -₹727 | -₹1,266 | 37.5% | -₹918 | -₹1,462 | 35.5% |

No true cell met the full dual-friction promotion gate.

## Null-control comparison

For the best true cell, MEDIUM_REL_GAP / FADE / 15:10:

- Base true mean weekly net: **₹714**
- Five matched null means: approximately **-₹1,065, ₹399, -₹483, -₹173, -₹844**
- Mean matched-null benchmark: **-₹433**
- Stress true mean weekly net: **₹666**
- Five matched null means: approximately **-₹1,110, ₹354, -₹526, -₹216, -₹889**
- Mean matched-null benchmark: **-₹478**

The true cell therefore outperformed its matched null average, but the absolute economics were far below the ₹5,000/week promotion threshold and the weekly median/positive-week criteria also failed.

## Decision

**CLOSED — NEGATIVE DISCOVERY.**

The prior-day-range normalization contains some descriptive signal for fading small/medium relative gaps into the 15:10 exit, but the effect is far too small and inconsistent to justify WFA/OOS.

No threshold, state boundary, exit, or mapping retuning is authorized.

## Strengths

- Chronologically complete one-minute NIFTY/option study window.
- Prior-only feature construction with zero information-barrier violations.
- Exact historical expiry and lot-size handling.
- Base and doubled-slippage Stress.
- Full 12-cell finite grid plus 5 fixed permutation nulls per cell.
- Execution coverage remained above the frozen 95% threshold.

## Limitations

- The relative-gap state is a simple univariate contextual feature and does not capture news or global overnight information.
- Large-gap state dominates the sample, while small/medium states have fewer sessions.
- No WFA/OOS is justified because the discovery gate did not clear.
