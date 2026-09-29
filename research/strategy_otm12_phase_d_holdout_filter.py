from __future__ import annotations
from pathlib import Path
import pandas as pd
import numpy as np

def metrics(df):
    w=df[df.net_pnl>0]; l=df[df.net_pnl<0]
    return {
        "trades":int(len(df)),
        "retention":float(len(df)),
        "net_pnl":float(df.net_pnl.sum()),
        "mean_pnl":float(df.net_pnl.mean()),
        "median_pnl":float(df.net_pnl.median()),
        "win_rate":float((df.net_pnl>0).mean()),
        "profit_factor":float(w.net_pnl.sum()/abs(l.net_pnl.sum())) if len(l) else None,
        "costs":float(df.total_cost.sum()),
        "gross_pnl":float(df.gross_pnl.sum()),
    }

def eval_rule(df, rule):
    x=df.copy()
    x["sample"]=np.where(x.trade_date<=pd.Timestamp("2024-12-31"),"discovery","holdout")
    out=[]
    for sample in ["discovery","holdout","all"]:
        s=x if sample=="all" else x[x["sample"]==sample]
        base=metrics(s); base["rule"]=rule; base["sample"]=sample; base["base_trades"]=len(s); out.append(base)
    return out

def main():
    out=Path("reports/phase-d"); out.mkdir(parents=True,exist_ok=True)
    base=pd.read_csv("base_artifact/trades.csv",parse_dates=["trade_date"])
    stress=pd.read_csv("stress_artifact/trades.csv",parse_dates=["trade_date"])
    discovery=base[base.trade_date<=pd.Timestamp("2024-12-31")]
    threshold=float(discovery.prior_day_range_pct.quantile(.8))
    rules={
      "baseline": lambda d: pd.Series(True,index=d.index),
      "exclude_expiry_day": lambda d: ~d.expiry_day.astype(bool),
      "exclude_top20_prior_day_range": lambda d: d.prior_day_range_pct <= threshold,
      "exclude_expiry_or_top20_prior_range": lambda d: (~d.expiry_day.astype(bool)) & (d.prior_day_range_pct <= threshold),
    }
    rows=[]
    for friction,name in [(base,"base"),(stress,"stress")]:
        for rule,fn in rules.items():
            m=fn(friction).fillna(False)
            selected=friction[m].copy()
            outm=metrics(selected); outm.update({"friction":name,"rule":rule,"sample_all":len(friction),
                                                 "threshold_prior_day_range_pct":threshold})
            disc_sel=selected[selected.trade_date<=pd.Timestamp("2024-12-31")]
            hold_sel=selected[selected.trade_date>=pd.Timestamp("2025-01-01")]
            outm["discovery_net_pnl"]=float(disc_sel.net_pnl.sum())
            outm["holdout_net_pnl"]=float(hold_sel.net_pnl.sum())
            outm["holdout_mean_pnl"]=float(hold_sel.net_pnl.mean()) if len(hold_sel) else np.nan
            outm["holdout_win_rate"]=float((hold_sel.net_pnl>0).mean()) if len(hold_sel) else np.nan
            outm["holdout_trades"]=int(len(hold_sel))
            rows.append(outm)
    result=pd.DataFrame(rows)
    result["retention_pct"]=result["trades"]/result["sample_all"]
    result.to_csv(out/"frozen_filter_probe.csv",index=False)
    # A concise decision table
    h=result[result.rule!="baseline"].copy()
    h["holdout_positive_expectancy"]=h.holdout_mean_pnl>0
    h.to_csv(out/"holdout_filter_decision.csv",index=False)
    md=[
      "# Phase D — Frozen holdout filter probe","",
      f"Discovery threshold for prior-day range top quintile: {threshold:.6f} ({threshold*100:.3f}%).",
      "Rules were frozen before reading holdout results: exclude expiry-day; exclude top 20% prior-day range; require both exclusions.",
      "","## Interpretation",
      "A filter is considered evidence of a useful improvement only if the untouched 2025-01-01 onward holdout has positive mean net P&L after the same friction model and does not achieve that result by an extreme collapse in trade count.",
      "The baseline is retained for direct comparison; no additional thresholds were searched."
    ]
    (out/"phase_d_report.md").write_text("\n".join(md))
if __name__=="__main__":
    main()
