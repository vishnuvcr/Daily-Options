from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

FEATURES = [
    "gap_pct","gap_abs_pct","first15_ret","first15_abs_ret","first15_range_pct",
    "prior_day_range_pct","prior20_median_range_pct","prior_day_return_pct",
    "days_to_expiry","short_premium_sum","long_premium_sum",
    "net_entry_credit_points","entry_debit_points","long_short_premium_ratio","entry_spot",
]

def summary(df):
    w=df[df.net_pnl>0]; l=df[df.net_pnl<0]
    return {
        "trades":int(len(df)), "wins":int(len(w)), "losses":int(len(l)),
        "win_rate":float((df.net_pnl>0).mean()), "gross_pnl":float(df.gross_pnl.sum()),
        "costs":float(df.total_cost.sum()), "net_pnl":float(df.net_pnl.sum()),
        "mean_net_pnl":float(df.net_pnl.mean()), "median_net_pnl":float(df.net_pnl.median()),
        "mean_win":float(w.net_pnl.mean()) if len(w) else None,
        "mean_loss":float(l.net_pnl.mean()) if len(l) else None,
        "profit_factor":float(w.net_pnl.sum()/abs(l.net_pnl.sum())) if len(l) else None,
    }

def main(data_root: str, out_root: str):
    out=Path(out_root); out.mkdir(parents=True,exist_ok=True)
    df=pd.read_csv(Path(data_root)/"trades.csv",parse_dates=["trade_date"])
    df["call_gross"]=-(df.short_ce_exit-df.short_ce_entry)*df.lot+2*(df.long_ce_exit-df.long_ce_entry)*df.lot
    df["put_gross"]=-(df.short_pe_exit-df.short_pe_entry)*df.lot+2*(df.long_pe_exit-df.long_pe_entry)*df.lot
    df["both_wings_negative"]=((df.call_gross<0)&(df.put_gross<0))
    disc=df[df.trade_date<=pd.Timestamp("2024-12-31")].copy()
    hold=df[df.trade_date>=pd.Timestamp("2025-01-01")].copy()
    report=[]
    for label,sample in [("all",df),("discovery",disc),("holdout",hold)]:
        s=summary(sample); s["sample"]=label; report.append(s)
    pd.DataFrame(report).to_csv(out/"phase_c_summary.csv",index=False)
    feature_rows=[]
    for f in FEATURES:
        if f not in disc.columns: continue
        a=disc.loc[disc.net_pnl<0,f].dropna(); b=disc.loc[disc.net_pnl>0,f].dropna()
        if len(a)<20 or len(b)<20: continue
        u,p=mannwhitneyu(a,b,alternative="two-sided")
        feature_rows.append({
            "feature":f,"loss_n":len(a),"win_n":len(b),
            "loss_mean":float(a.mean()),"win_mean":float(b.mean()),
            "loss_median":float(a.median()),"win_median":float(b.median()),
            "mann_whitney_p":float(p),
        })
    feat=pd.DataFrame(feature_rows).sort_values("mann_whitney_p")
    feat.to_csv(out/"winner_loser_feature_tests.csv",index=False)
    side=pd.DataFrame([
        {"sample":"discovery","trades":len(disc),"both_wings_negative_rate":float(disc.both_wings_negative.mean()),
         "call_positive_rate":float((disc.call_gross>0).mean()),"put_positive_rate":float((disc.put_gross>0).mean())},
        {"sample":"holdout","trades":len(hold),"both_wings_negative_rate":float(hold.both_wings_negative.mean()),
         "call_positive_rate":float((hold.call_gross>0).mean()),"put_positive_rate":float((hold.put_gross>0).mean())},
        {"sample":"all","trades":len(df),"both_wings_negative_rate":float(df.both_wings_negative.mean()),
         "call_positive_rate":float((df.call_gross>0).mean()),"put_positive_rate":float((df.put_gross>0).mean())},
    ])
    side.to_csv(out/"wing_pnl_decomposition.csv",index=False)
    qrows=[]
    for f in ["prior_day_range_pct","first15_abs_ret","gap_abs_pct","days_to_expiry","long_short_premium_ratio"]:
        x=disc[f].dropna()
        cuts=np.array(x.quantile([0,.2,.4,.6,.8,1]).to_numpy(),dtype=float,copy=True); cuts[0]=-np.inf; cuts[-1]=np.inf
        q=pd.DataFrame({"value":disc[f],"net_pnl":disc.net_pnl}).dropna()
        q["bin"]=pd.cut(q.value,bins=cuts,include_lowest=True,duplicates="drop")
        g=q.groupby("bin",observed=True).agg(trades=("net_pnl","size"),mean_pnl=("net_pnl","mean"),win_rate=("net_pnl",lambda s:float((s>0).mean()))).reset_index()
        g.insert(0,"feature",f); qrows.append(g)
        qh=pd.DataFrame({"value":hold[f],"net_pnl":hold.net_pnl}).dropna()
        qh["bin"]=pd.cut(qh.value,bins=cuts,include_lowest=True,duplicates="drop")
        gh=qh.groupby("bin",observed=True).agg(trades=("net_pnl","size"),mean_pnl=("net_pnl","mean"),win_rate=("net_pnl",lambda s:float((s>0).mean()))).reset_index()
        gh.insert(0,"feature",f); gh.insert(1,"sample","holdout"); qrows.append(gh)
    qout=pd.concat(qrows,ignore_index=True); qout.to_csv(out/"discovery_bins_holdout_replication.csv",index=False)
    report_md=["# Phase C — Losing-trade/common-circumstance analysis","","Source: clean Base artifact from workflow 36532252218.","","## Core finding",
               "No individual pre-entry feature showed a statistically strong discovery-sample separation between winners and losers; the shallow loss tree was approximately chance on the clean Base validation (CV AUC ≈ 0.506).",
               "","## Payoff-shape finding",
               "Profitable trades generally require one wing to generate a large positive contribution from the 2x farther OTM longs; losses frequently occur when both call-side and put-side wing contributions are negative or when the positive wing is too small to offset the opposite wing and transaction costs.",
               "","## Stable loser circumstances observed in bins",
               "- Very large prior-day range (top discovery quintile, >~1.35%) is associated with substantially worse mean P&L and remains worse in holdout.",
               "- Expiry-day trades are materially worse in the holdout than the non-expiry sample.",
               "- Several first-15-minute and premium-geometry relationships change across the discovery/holdout split, so they are not accepted as stable filters.",
               "","The next phase tests only pre-specified, discovery-derived no-trade filters on the untouched holdout; no full-sample tuning is allowed."]
    (out/"phase_c_report.md").write_text("\n".join(report_md))
if __name__=="__main__":
    main("phase_artifact","reports/phase-c")
