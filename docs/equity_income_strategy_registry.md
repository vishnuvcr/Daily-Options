# Equity Income strategy registry

This registry is intentionally a template until the Python archive has enumerated the complete channel.

Each row will correspond to one distinct strategy hypothesis, not merely one video.

Required fields:

| field | meaning |
|---|---|
| strategy_id | stable canonical identifier |
| source_video_ids | all videos that describe the strategy |
| title_set | source video titles |
| strategy_name | canonical research name |
| underlying | NIFTY / BANKNIFTY / stock / futures / other |
| timeframe | weekly / monthly / expiry-day / event |
| payoff_family | canonical structure family |
| entry_rule | exact reconstructed rule |
| strike_rule | exact strike construction |
| adjustment_rule | exact adjustment trigger/action |
| stop_rule | exact stop logic |
| target_rule | exact profit-taking logic |
| exit_rule | time-based or event-based exit |
| capital_rule | fixed reference position size / margin |
| source_fidelity | SOURCE-EXPLICIT / SOURCE-INFERRED / UNSPECIFIED / CONFLICTING |
| data_status | READY / DATA-LIMITED / UNRESOLVED |
| duplicate_group | canonical family grouping |
| phase_status | PENDING / RECONSTRUCTING / TESTING / VALIDATED / RETIRED |

Promotion is based on the weekly research plan, not on video claims.
