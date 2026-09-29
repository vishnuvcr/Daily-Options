from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor, export_text
from sklearn.model_selection import StratifiedKFold, cross_val_score

FEATURES=[
    "gap_abs_pct","first15_abs_ret","first15_range_pct","prior_day_range_pct",
    "prior20_median_range_pct","prior_day_return_pct","days_to_expiry",
    "short_premium_sum","long_premium_sum","net_entry_credit_points",
    "entry_debit_points","long_short_premium_ratio","entry_spot"
]
DISCOVERY_END=pd.Timestamp("2024-12-31")
HOLDOUT_START=pd.Timestamp("2025-01-01")
FILTER_RANGE=0.013145164120942354
FILTER_DTE=1.5

def summarize(df: pd.DataFrame) -> dict:
    w=df[df.net_pnl>0]; l=df[df.net_pnl<0]
    return {
        "trades": int(len(df)),
        "wins": int(len(w)),
        "losses": int(len(l)),
        "win_rate": float((df.net_pnl>0).mean()) if len(df) else None,
        "net_pnl": float(df.net_pnl.sum()),
        "mean_net_pnl": float(df.net_pnl.mean()),
        "median_net_pnl": float(df.net_pnl.median()),
        "mean_win": float(w.net_pnl.mean()) if len(w) else None,
        "mean_loss": float(l.net_pnl.mean()) if len(l) else None,
    }

def feature_stats(df: pd.DataFrame) -> pd.DataFrame:
    d=df[df.trade_date<=DISCOVERY_END].copy()
    rows=[]
    for f in FEATURES:
        a=d.loc[d.net_pnl>0,f].dropna()
        b=d.loc[d.net_pnl<0,f].dropna()
        if len(a)<20 or len(b)<20: continue
        u,p=mannwhitneyu(a,b,alternative="two-sided")
        sd=float(d[f].std())
        rows.append({
            "feature":f,
            "win_mean":float(a.mean()),"loss_mean":float(b.mean()),
            "win_median":float(a.median()),"loss_median":float(b.median()),
            "mean_diff":float(a.mean()-b.mean()),
            "standardized_mean_diff":float((a.mean()-b.mean())/sd) if sd>0 else None,
            "mannwhitney_p":float(p),
            "wins_n":int(len(a)),"losses_n":int(len(b))
        })
    return pd.DataFrame(rows).sort_values(["mannwhitney_p","standardized_mean_diff"],ascending=[True,False])

def quintile_bins(df: pd.DataFrame) -> pd.DataFrame:
    d=df[df.trade_date<=DISCOVERY_END].copy()
    h=df[df.trade_date>=HOLDOUT_START].copy()
    rows=[]
    for f in FEATURES:
        x=d[f].dropna()
        if len(x)<50: continue
        cuts=np.array(x.quantile([0,.2,.4,.6,.8,1]).to_numpy(),dtype=float,copy=True)
        cuts[0]=-np.inf; cuts[-1]=np.inf
        for label,z in [("discovery",d),("holdout",h)]:
            q=z[[f,"net_pnl"]].dropna().copy()
            if q.empty: continue
            q["bin"]=pd.cut(q[f],bins=cuts,include_lowest=True,duplicates="drop")
            g=q.groupby("bin",observed=True).agg(
                trades=("net_pnl","size"),mean_pnl=("net_pnl","mean"),
                median_pnl=("net_pnl","median"),
                win_rate=("net_pnl",lambda s:float((s>0).mean())),
                loss_rate=("net_pnl",lambda s:float((s<0).mean())),
                total_pnl=("net_pnl","sum")
            ).reset_index()
            g.insert(0,"feature",f); g.insert(1,"sample",label)
            g.insert(2,"cut_values",json.dumps(cuts.tolist()))
            rows.append(g)
    return pd.concat(rows,ignore_index=True) if rows else pd.DataFrame()

def leg_diagnostics(df: pd.DataFrame) -> pd.DataFrame:
    rows=[]
    for r in df.itertuples(index=False):
        rows.append({
            "short_ce":-(r.short_ce_exit-r.short_ce_entry)*r.lot,
            "long_ce":2*(r.long_ce_exit-r.long_ce_entry)*r.lot,
            "short_pe":-(r.short_pe_exit-r.short_pe_entry)*r.lot,
            "long_pe":2*(r.long_pe_exit-r.long_pe_entry)*r.lot,
        })
    return pd.DataFrame(rows)

def trees(df: pd.DataFrame, out: Path) -> dict:
    d=df[df.trade_date<=DISCOVERY_END].copy()
    (out).mkdir(parents=True,exist_ok=True)
    z=d.dropna(subset=FEATURES+["net_pnl"]).copy()
    X=z[FEATURES]
    y=(z.net_pnl<0).astype(int)
    clf=DecisionTreeClassifier(max_depth=3,min_samples_leaf=50,random_state=1)
    cv=StratifiedKFold(n_splits=5,shuffle=False)
    auc=cross_val_score(clf,X,y,cv=cv,scoring="roc_auc")
    clf.fit(X,y)
    (out/"loss_tree.txt").write_text(export_text(clf,feature_names=FEATURES))
    reg=DecisionTreeRegressor(max_depth=3,min_samples_leaf=50,random_state=1)
    reg.fit(X,z.net_pnl)
    z["leaf"]=reg.apply(X)
    h=df[df.trade_date>=HOLDOUT_START].copy()
    h_complete=h.dropna(subset=FEATURES).copy()
    h_complete["leaf"]=reg.apply(h_complete[FEATURES])
    dstats=z.groupby("leaf").agg(trades=("net_pnl","size"),mean_pnl=("net_pnl","mean"),win_rate=("net_pnl",lambda s:float((s>0).mean())),total_pnl=("net_pnl","sum")).reset_index()
    hstats=h_complete.groupby("leaf").agg(holdout_trades=("net_pnl","size"),holdout_mean_pnl=("net_pnl","mean"),holdout_win_rate=("net_pnl",lambda s:float((s>0).mean())),holdout_total_pnl=("net_pnl","sum")).reset_index()
    dstats.merge(hstats,on="leaf",how="left").to_csv(out/"regression_tree_leaf_stats.csv",index=False)
    (out/"loss_tree_cv.json").write_text(json.dumps({
        "auc_mean":float(auc.mean()),"auc_std":float(auc.std()),
        "max_depth":3,"min_samples_leaf":50
    },indent=2))
    return {"classifier_auc_mean":float(auc.mean()),"classifier_auc_std":float(auc.std())}

def candidate_filter(df: pd.DataFrame) -> dict:
    rule=(df.prior_day_range_pct>FILTER_RANGE)&(df.days_to_expiry<=FILTER_DTE)
    result={}
    for sample,mask in [("discovery",df.trade_date<=DISCOVERY_END),("holdout",df.trade_date>=HOLDOUT_START)]:
        all_s=df[mask].copy()
        bad=all_s[rule & mask]
        keep=all_s[~rule & mask]
        result[sample]={"candidate_blocked":summarize(bad),"candidate_kept":summarize(keep)}
    return result

def run(inp_base: str, inp_stress: str, out_dir: str):
    out=Path(out_dir); out.mkdir(parents=True,exist_ok=True)
    reports=[]
    baseline={}
    for label,root in [("base",Path(inp_base)),("stress",Path(inp_stress))]:
        df=pd.read_csv(root/"trades.csv",parse_dates=["trade_date"])
        baseline[label]=summarize(df)
        fs=feature_stats(df); fs.insert(0,"friction",label); fs.to_csv(out/f"winner_loser_features_{label}.csv",index=False)
        qb=quintile_bins(df); qb.to_csv(out/f"feature_bins_{label}.csv",index=False)
        leg=leg_diagnostics(df)
        for group,mask in [("wins",df.net_pnl>0),("losses",df.net_pnl<0)]:
            m=leg.loc[mask]
            row={"friction":label,"group":group,"n":int(len(m))}
            row.update({f"{c}_mean":float(m[c].mean()) for c in m.columns})
            reports.append(row)
        tinfo=trees(df,out/f"{label}_trees"); tinfo["friction"]=label
        tinfo.update(candidate_filter(df))
        (out/f"candidate_filter_{label}.json").write_text(json.dumps(tinfo,indent=2))
    pd.DataFrame(reports).to_csv(out/"leg_contribution_winners_vs_losers.csv",index=False)
    (out/"baseline_summary.json").write_text(json.dumps(baseline,indent=2))
    md=[
        "# Phase C — Loser/common-circumstance analysis",
        "",
        "Discovery window: 2021-07-01 through 2024-12-31. Holdout: 2025-01-01 onward.",
        "",
        "## Clean baseline",
        pd.DataFrame(baseline).T.to_markdown(),
        "",
        "## Interpretation",
        "- Winners are generally driven by one-sided wing expansion with simultaneous decay/containment of the corresponding short OTM1 leg; both wings needing to appreciate at once is uncommon.",
        "- The strongest repeatable loser regime found in the discovery-only regression tree is prior-day range > 1.314516% combined with <= 1.5 calendar days to expiry.",
        "- This rule is a candidate avoidance condition only. It is not operational until the untouched holdout confirms the same direction.",
        "- The shallow loss classifier is not treated as predictive unless its discovery and holdout behavior remains stable; ROC-AUC near 0.5 is non-informative.",
    ]
    (out/"phase_c_summary.md").write_text("\n".join(md))
    return baseline

if __name__=="__main__":
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--base",required=True)
    ap.add_argument("--stress",required=True)
    ap.add_argument("--out",required=True)
    a=ap.parse_args()
    print(json.dumps(run(a.base,a.stress,a.out),indent=2))
