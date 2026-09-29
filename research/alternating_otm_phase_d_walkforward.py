from pathlib import Path
import argparse, json
import pandas as pd
import numpy as np

THRESHOLD=0.00126795235
FOLDS=[
 ("2023", "2021-07-01","2022-12-31","2023-01-01","2023-12-31"),
 ("2024", "2021-07-01","2023-12-31","2024-01-01","2024-12-31"),
 ("2025", "2021-07-01","2024-12-31","2025-01-01","2025-12-31"),
 ("2026", "2021-07-01","2025-12-31","2026-01-01","2026-12-31"),
]
def stats(g, col):
    x=g[col]
    win=x[x>0].sum(); loss=x[x<0].sum()
    z=g.sort_values("trade_date").copy(); z["cum"]=z[col].cumsum(); z["dd"]=z["cum"]-z["cum"].cummax()
    return {"trades":len(g),"win_rate":float((x>0).mean()),"net_pnl":float(x.sum()),
            "mean_pnl":float(x.mean()),"median_pnl":float(x.median()),
            "profit_factor":float(win/abs(loss)) if loss<0 else None,
            "max_drawdown":float(z.dd.min()),"max_loss":float(x.min())}
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--base-artifact",required=True); ap.add_argument("--stress-artifact",required=True); ap.add_argument("--out",required=True)
    a=ap.parse_args(); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    b=pd.read_csv(Path(a.base_artifact)/"trades.csv",parse_dates=["trade_date"])
    s=pd.read_csv(Path(a.stress_artifact)/"trades.csv",parse_dates=["trade_date"])
    req=["trade_date","first15_abs_ret","net_pnl","gross_pnl","total_cost"]
    for c in req:
        if c not in b or c not in s: raise RuntimeError("missing "+c)
    if not b.trade_date.reset_index(drop=True).equals(s.trade_date.reset_index(drop=True)): raise RuntimeError("date alignment")
    m=b[req].copy().rename(columns={"net_pnl":"base_net","gross_pnl":"base_gross","total_cost":"base_cost"})
    m["stress_net"]=s.net_pnl.to_numpy(); m["stress_gross"]=s.gross_pnl.to_numpy(); m["stress_cost"]=s.total_cost.to_numpy()
    rows=[]
    for fold,_,train_end,test_start,test_end in FOLDS:
        test=m[(m.trade_date>=pd.Timestamp(test_start))&(m.trade_date<=pd.Timestamp(test_end))].copy()
        if test.empty: continue
        keep=test.first15_abs_ret.isna() | (test.first15_abs_ret>=THRESHOLD)
        for friction,col in [("base","base_net"),("stress","stress_net")]:
            allx=test.rename(columns={col:"pnl"}); filt=test.loc[keep].rename(columns={col:"pnl"})
            a0=stats(allx,"pnl"); a1=stats(filt,"pnl")
            rows.append({"fold":fold,"friction":friction,"baseline":a0,"filtered":a1,
                         "retained_share":len(filt)/len(test),
                         "net_improvement":a1["net_pnl"]-a0["net_pnl"],
                         "mean_improvement":a1["mean_pnl"]-a0["mean_pnl"]})
    (out/"walkforward_results.json").write_text(json.dumps(rows,indent=2))
    flat=[]
    for r in rows:
        flat.append({"fold":r["fold"],"friction":r["friction"],"trades_baseline":r["baseline"]["trades"],
                     "trades_filtered":r["filtered"]["trades"],"retained_share":r["retained_share"],
                     "baseline_win_rate":r["baseline"]["win_rate"],"filtered_win_rate":r["filtered"]["win_rate"],
                     "baseline_net":r["baseline"]["net_pnl"],"filtered_net":r["filtered"]["net_pnl"],
                     "net_improvement":r["net_improvement"],"baseline_pf":r["baseline"]["profit_factor"],
                     "filtered_pf":r["filtered"]["profit_factor"],"baseline_dd":r["baseline"]["max_drawdown"],
                     "filtered_dd":r["filtered"]["max_drawdown"],"filtered_max_loss":r["filtered"]["max_loss"]})
    pd.DataFrame(flat).to_csv(out/"walkforward_results.csv",index=False)
    # pooled test-period summary, descriptive only
    df=pd.DataFrame(flat)
    summary=[]
    for fr in ["base","stress"]:
        q=df[df.friction==fr]
        summary.append({"friction":fr,"folds":len(q),"positive_net_improvement_folds":int((q.net_improvement>0).sum()),
                        "total_baseline_net":float(q.baseline_net.sum()),"total_filtered_net":float(q.filtered_net.sum()),
                        "total_net_improvement":float(q.net_improvement.sum()),
                        "mean_fold_improvement":float(q.net_improvement.mean())})
    pd.DataFrame(summary).to_csv(out/"walkforward_summary.csv",index=False)
    result={"threshold":THRESHOLD,"folds":[x[0] for x in FOLDS],"rows":rows,"summary":summary}
    (out/"phase_d_result.json").write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
if __name__=="__main__": main()
