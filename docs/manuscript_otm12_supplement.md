# Supplement — OTM12 Ratio Backspread Reproducibility and Data Dictionary

## Feature dictionary
| Feature | Definition | Allowed for entry filter? |
|---|---|---|
| gap_pct | 09:15 NIFTY open vs previous close | Yes |
| first15_ret | 09:29 close vs 09:15 open | Yes |
| first15_range_pct | 09:15–09:29 high-low range / 09:15 open | Yes |
| prior_day_range_pct | Previous full-session high-low / previous close | Yes |
| prior20_median_range_pct | Median of prior 20 previous-day ranges | Yes |
| prior_day_return_pct | Previous close / previous open - 1 | Yes |
| days_to_expiry | Calendar days from trade date to chosen expiry | Yes |
| short_premium_sum | Entry premium of the two short OTM1 legs | Yes |
| long_premium_sum | Entry premium of the two 2× long OTM2 legs | Yes |
| net_entry_credit_points | Short premium minus long premium | Yes |
| entry_debit_points | Long premium minus short premium | Yes |
| long_short_premium_ratio | Long premium divided by short premium | Yes |
| entry_spot | 09:30 NIFTY reference | Yes |
| leg exit contributions | Realized contribution of each option leg | No — diagnostic only |

## Cost model
The workflow applies four-leg round-trip brokerage, exchange charges, SEBI charges, stamp duty, GST, date-aware option STT, and slippage. Base slippage is ₹0.20 per option price point per side; Stress is ₹0.40.

## Execution integrity
The clean run produced 1,209 complete four-leg trades. Selection diagnostics recorded 8 sessions without an entry quote, 5 with a missing short-call exit, 1 with a missing long-call exit, and 4 with mixed exit-mark times. All completed trades used the 15:15 exit timestamp.

## Reproducibility rule
No future work should modify the Phase-C cutoff after seeing Phase-D results. Any change in strike-selection logic, timestamp, exit, cost assumptions or filter threshold must begin a new research branch and a new holdout.
