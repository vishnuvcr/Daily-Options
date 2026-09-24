from pathlib import Path
import argparse
import pandas as pd
import research.phase21_regime_switch_gamma_vega_v1 as p21

_original_regime_table = p21.regime_table

def regime_table_date_safe(root: Path, global_root: Path) -> pd.DataFrame:
    out = _original_regime_table(root, global_root).copy()
    out["trade_date"] = pd.to_datetime(out["trade_date"]).dt.date
    return out

p21.regime_table = regime_table_date_safe

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--global-root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--slippage", type=float, default=0.20)
    args = ap.parse_args()
    p21.run(args.data, args.global_root, args.out, args.slippage)
