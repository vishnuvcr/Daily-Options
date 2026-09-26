from __future__ import annotations
import argparse, json
from pathlib import Path
import pandas as pd

KEYS=["definition","expiry_choice","strike_choice","gap","wait","risk","time_exit"]

def aggregate(root: Path, out: Path, regime: str):
    files=sorted(root.glob(f"**/{regime}/leaderboard.csv"))
    if not files:
        # artifact folders may flatten the regime one level
        files=sorted(root.glob("**/leaderboard.csv"))
        files=[p for p in files if regime in str(p)]
    if not files: raise RuntimeError(f"No {regime} shard leaderboards found under {root}")
    dfs=[pd.read_csv(p) for p in files]
    df=pd.concat(dfs,ignore_index=True)
    if df[KEYS].duplicated().any(): raise RuntimeError(f"Duplicate registered cell in {regime} aggregate")
    expected=6480
    if len(df)!=expected: raise RuntimeError(f"{regime} aggregate has {len(df)} cells, expected {expected}")
    out.mkdir(parents=True,exist_ok=True)
    df.sort_values(["gate","mean_weekly_net"],ascending=[False,False]).to_csv(out/"leaderboard.csv",index=False)
    best=df.iloc[0].to_dict()
    summary={
        "regime":regime,
        "registered_cells":expected,
        "aggregated_cells":len(df),
        "passed_gate":int(df["gate"].astype(bool).sum()),
        "best":best,
        "shard_files":len(files),
        "pnl_authorized":True
    }
    (out/"summary.json").write_text(json.dumps(summary,indent=2,default=str)+"\n")
    diag={"regime":regime,"shard_files":[str(x) for x in files],
          "duplicate_cells":int(df[KEYS].duplicated().sum()),
          "aggregated_cells":len(df)}
    (out/"diagnostics.json").write_text(json.dumps(diag,indent=2,default=str)+"\n")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,required=True); ap.add_argument("--out-root",type=Path,required=True)
    args=ap.parse_args()
    aggregate(args.root,args.out_root/"base","base")
    aggregate(args.root,args.out_root/"stress","stress")
