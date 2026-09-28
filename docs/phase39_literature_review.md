# Phase 39 — Literature Review

## Motivation
Phase 39 is motivated by the documented information content of option-implied volatility and by evidence that option-market information can matter especially close to market opening. The review is used to define the hypothesis and its limitations, not to presume profitability.

## 1. Implied versus realized volatility in NIFTY
Panda, Swain and Malhotra (2008) study S&P CNX Nifty index options and report that implied volatility contains more information about future realized volatility than past realized volatility in their sample. This supports testing an option-implied-versus-realized relation rather than using historical volatility alone.

Source: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1512552

Padhi and Shaikh (2014) examine NSE Nifty index options and report that call and put implied volatility contains information about future realized return volatility. Their econometric treatment explicitly addresses measurement error, highlighting that implied-volatility signals should not be interpreted as noiseless forecasts.

Source: https://ideas.repec.org/a/taf/jbemgt/v15y2014i5p915-934.html

Shaikh and Padhi (2015) report evidence from Indian index options that implied volatility can contain useful information for future volatility and discuss Granger-causality results. This is evidence for predictive content at the volatility level, not evidence for a profitable opening debit-spread strategy after costs.

Source: https://ideas.repec.org/a/ase/jtsrta/v22y2015i1p69-88id28.html

Patra (2025) uses daily NIFTY options data from 2020–2025 and reports predictive information in ATM and OTM/skew-based option features for longer-horizon variance forecasts. This is recent contextual evidence that modern NIFTY option data contain volatility information, but its forecasting horizon differs from Phase 39's first-15-minute horizon.

Source: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5748922

Agarwal (2026) studies a large NIFTY one-minute option dataset and documents the structure of the NIFTY variance-risk premium using ATM-implied volatility and realized volatility. The work is a recent preprint and should be treated as preliminary rather than peer-reviewed validation of any trading rule.

Source: https://papers.ssrn.com/sol3/Delivery.cfm/6530119.pdf?abstractid=6530119&mirid=1&type=2

## 2. Opening and short-horizon information in option markets
Liu, Hsieh and Tu (2017) examine Taiwan index options and find that implied-volatility and option-volume information from the early 15-minute pre-opening session can predict spot index/ETF returns for up to ten minutes after the spot market opens. Their market is Taiwan rather than India, but the study provides a mechanism-based rationale for examining opening-period option information without assuming the result transfers to NIFTY.

Source: https://www.sciencedirect.com/science/article/pii/S1062940817301213

## 3. Indian opening-market microstructure context
Research on the Indian market documents distinctive opening volatility and price-discovery dynamics around the NSE opening call auction. Such evidence motivates a short, explicitly defined opening interval instead of treating the entire trading day as homogeneous.

Source: https://www.sciencedirect.com/science/article/pii/S105752191500023X

## 4. Phase 39's contribution
Phase 39 does not copy an existing option strategy. It constructs a dimensionless MOVE_RATIO that compares the realized first-15-minute NIFTY move with an option-implied move scaled to the same 15-minute horizon. The use of a strictly prior 60-session z-score prevents the state threshold from adapting to future observations, and the fixed CONTINUE/FADE pair prevents directional mapping from being selected after seeing P&L.

## 5. Literature-to-method mapping
| Literature observation | Phase 39 control |
|---|---|
| Implied volatility contains information about future realized volatility | Compare contemporaneous implied move with realized opening move |
| Opening-period option information can relate to very short-horizon spot returns | Use only information available by 09:30 and enter at 09:31 |
| IV is measured with model/price error | Require both CE and PE IV inputs and apply explicit coverage gates |
| Market effects can vary by regime | Report HIGH/LOW dislocation states separately without tuning thresholds |
| Trading costs can erase gross effects | Apply fixed brokerage, statutory charges and Base/Stress slippage |

## 6. Key limitations from the literature
- NIFTY and Taiwan evidence may not transfer to the current NIFTY microstructure.
- Published studies often use daily or pre-opening samples rather than the exact 09:15–09:29/09:30 construction used here.
- Black-Scholes/Black-76 IV inherits model assumptions and input-price noise.
- Statistical predictability of volatility does not imply a profitable defined-risk option strategy after transaction costs.
- Recent 2025–2026 sources cited here include SSRN preprints; their claims should be treated as preliminary until independently replicated.

## References
1. Panda, S. P., Swain, N., & Malhotra, D. K. (2008). Relationship Between Implied and Realized Volatility of S&P CNX Index in India. Frontiers in Finance and Economics 5(1), 85–105.
2. Padhi, P., & Shaikh, I. (2014). On the relationship of implied, realized and historical volatility: evidence from NSE equity index options. Journal of Business Economics and Management, 15(5), 915–934.
3. Shaikh, I., & Padhi, P. (2015). A Study of Market Efficiency from Option Prices Evidence from the National Stock Exchange of India. Journal Transition Studies Review, 22(1), 69–88.
4. Liu, W., Hsieh, W.-L. G., & Tu, A. H. (2017). Does the early bird catch the worm? The information content of Taiwan’s index option trading in the early 15-min pre-opening session. North American Journal of Economics and Finance, 41, 168–189. DOI: 10.1016/j.najef.2017.04.004.
5. Patra, M. (2025). Volatility Modelling for Indian Markets. SSRN 5748922.
6. Agarwal, Y. (2026). The Variance Risk Premium in Nifty 50: A Structural Anatomy Across Nine Empirical Filters. SSRN 6530119.
7. Impact of the introduction of call auction on price discovery: Evidence from the Indian stock market using high-frequency data. Journal of International Money and Finance / related NSE microstructure literature.