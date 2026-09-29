from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd

DISCOVERY_END=pd.Timestamp("2024-12-31")
HOLDOUT_START=pd.Timestamp("2025-01-01")
RANGE_CUTOFF=0.013145164120942354
DTE_CUTOFF=1.5

def boot_mean_ci(x, seed=42, n_boot=20000):
    x=np.asarray(pd.Series(x).dropna(),dtype=float)
    if len(x)==0:
        return [None,None]
    rng=np.random.default_rng(seed)
    means=np.mean(rng.choice(x,size=(n_boot,len(x)),replace=True),axis=1)
    return [float(np.quantile(means,0.025)),float(np.quantile(means,0.975))]

def summarize(x):
    x=x.copy()
    return {
        "trades":int(len(x)),
        "wins":int((x.net_pnl>0).sum()),
        "losses":int((x.net_pnl<0).sum()),
        "win_rate":float((x.net_pnl>0).mean()) if len(x) else None,
        "net_pnl":float(x.net_pnl.sum()),
        "mean_net_pnl":float(x.net_pnl.mean()) if len(x) else None,
        "median_net_pnl":float(x.net_pnl.median()) if len(x) else None,
        "mean_ci95":boot_mean_ci(x.net_pnl),
    }

def evaluate(df):  # frozen holdout probe
    hold=df[df.trade_date>=HOLDOUT_START].copy()
    rule=(hold.prior_day_range_pct>RANGE_CUTOFF)&(hold.days_to_expiry<=DTE_CUTOFF)
    all_stats=summarize(hold)
    blocked=summarize(hold[rule])
    kept=summarize(hold[~rule])
    return {
        "holdout_all":all_stats,
        "holdout_blocked_by_frozen_filter":blocked,
        "holdout_kept_after_frozen_filter":kept,
        "blocked_fraction":float(rule.mean()),
        "net_pnl_improvement_from_filter":float(kept["net_pnl"]-all_stats["net_pnl"]),
        "mean_pnl_improvement_per_remaining_trade":float(kept["mean_net_pnl"]-all_stats["mean_net_pnl"]),
    }

def run(base_path,stress_path,out):
    out=Path(out); out.mkdir(parents=True,exist_ok=True)
    res={}
    for label,path in [("base",base_path),("stress",stress_path)]:
        df=pd.read_csv(Path(path)/"trades.csv",parse_dates=["trade_date"])
        r=evaluate(df); res[label]=r
        (out/f"holdout_filter_{label}.json").write_text(json.dumps(r,indent=2))
    (out/"frozen_filter_definition.md").write_text(
        "# Frozen Phase-D filter

"
        "Do not enter when prior-day full-session range > 1.314516% AND days to expiry <= 1.5 calendar days.

"
        "The thresholds were frozen from Phase-C discovery and were not changed using holdout data.\n"
    )
    (out/"phase_d_results.json").write_text(json.dumps(res,indent=2))
    md=["# Phase D — Frozen Holdout Filter Probe","","The candidate filter was fixed before reading holdout performance.",
        f"- prior-day range > {RANGE_CUTOFF*100:.6f}%",
        "- days to expiry <= 1.5 calendar days",
        ""]
    for label,r in res.items():
        md += [
            f"## {label.title()} friction",
            pd.DataFrame([r["holdout_all"],r["holdout_blocked_by_frozen_filter"],r["holdout_kept_after_frozen_filter"]],index=["all","blocked","kept"]).to_markdown(),
            f"- Blocked fraction: {r['blocked_fraction']*100:.2f}%",
            f"- Net P&L improvement from excluding blocked trades: ₹{r['net_pnl_improvement_from_filter']:,.2f}",
            f"- Mean net P&L improvement per retained trade: ₹{r['mean_pnl_improvement_per_remaining_trade']:,.2f}",
            ""
        ]
    md += ["## Decision rule","The filter is evidence of a loss-concentration regime, not evidence that the underlying strategy becomes profitable. A retained sample remaining net negative does not support declaring the strategy profitable."]
    (out/"phase_d_results.md").write_text("\n".join(md))
    return res

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--base",required=True); ap.add_argument("--stress",required=True); ap.add_argument("--out",required=True)
    a=ap.parse_args(); print(json.dumps(run(a.base,a.stress,a.out),indent=2))
