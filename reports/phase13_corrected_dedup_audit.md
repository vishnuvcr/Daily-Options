# Phase 13 v1 — Corrected Deduplication Audit

## Audit trigger

A retrospective audit of the authoritative Phase 13 artifact found that every row in both Base and Stress trade files was duplicated exactly twice. The source implementation includes `risk_id` in the unique setup key and then independently loops over both risk profiles before merging outcomes back on `risk_id`, creating duplicate final rows.

This audit does not retune any parameter. It only removes exact duplicate trade records from the authoritative artifact and recomputes the frozen leaderboard and the same nested walk-forward selection rule.

## Corrected full-sample result

| Metric | Base | Stress |
|---|---:|---:|
| Raw trade rows | 79,456 | 79,456 |
| Exact unique trade rows | 39,728 | 39,728 |
| Best variant | w10|z1.5|vp80|14:45:00|LONG|MONTH|h10|r0 | same |
| Best trades | 153 | 153 |
| Best active days | 153 | 153 |
| Mean active-day net | ₹142.72 | ₹112.72 |
| Median active-day net | ₹-6.53 | ₹-36.53 |
| Win rate | 49.67% | 47.06% |
| Profit factor | 1.597 | 1.443 |
| Max drawdown | ₹-8,731.86 | ₹-9,391.86 |
| Total net | ₹21,836.87 | ₹17,246.87 |
| Target-qualified variants | 0 | 0 |

## Corrected nested walk-forward

The original frozen train/validation/test schedule and selection rule were retained exactly.

Base test-window means:
- ₹49.98
- ₹510.46
- ₹49.74
- ₹-116.02
- ₹114.96

Stress test-window means:
- ₹19.98
- ₹480.46
- ₹19.74
- ₹-146.02
- ₹84.96

Corrected WFA summary:
- Base: 4/5 positive, 0/5 ≥ ₹1,000; mean test-window net ₹121.82.
- Stress: 4/5 positive, 0/5 ≥ ₹1,000; mean test-window net ₹91.82.

## Decision

The published Phase 13 result of ₹285.45 base / ₹225.45 stress was invalid because it counted each trade twice.

The corrected Phase 13 family is **not promoted** and remains below the ₹1,000 net/active-lot/day target. No parameter retuning is authorized on this retrospective correction.

## Engineering correction required

The simulator must generate exactly one outcome for each input `risk_id` rather than expanding both risk profiles for a setup that already contains `risk_id`. A regression test should assert one output row per input setup/risk key.
