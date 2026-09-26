from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

KEYS = [
    "entry_day", "entry_time", "expiry_choice", "strike_method",
    "trigger", "action", "risk",
]


def regime_from_path(path: Path) -> str:
    parts = [p.lower() for p in path.parts]
    if any(p.endswith("-base") or p.endswith("_base") for p in parts):
        return "base"
    if any(p.endswith("-stress") or p.endswith("_stress") for p in parts):
        return "stress"
    raise RuntimeError(f"Cannot infer regime from {path}")


def fold_from_path(path: Path) -> int:
    for part in path.parts:
        if part.startswith("fold_"):
            return int(part.split("_", 1)[1])
    raise RuntimeError(f"Cannot infer fold from {path}")


def stage_from_path(path: Path) -> str:
    return "train" if "train" in path.parts else "oos"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--out-root", type=Path, required=True)
    args = ap.parse_args()

    lbs = sorted(args.root.rglob("leaderboard.csv"))
    weeklies = sorted(args.root.rglob("weekly.csv"))
    if len(lbs) != 144:
        raise RuntimeError(f"Expected 144 leaderboard files, got {len(lbs)}")
    if len(weeklies) != 144:
        raise RuntimeError(f"Expected 144 weekly files, got {len(weeklies)}")

    lb_frames = []
    for f in lbs:
        z = pd.read_csv(f)
        z["regime"] = regime_from_path(f)
        z["fold"] = fold_from_path(f)
        z["stage"] = stage_from_path(f)
        lb_frames.append(z)
    all_lb = pd.concat(lb_frames, ignore_index=True)
    if len(all_lb) != 72 * 120:
        raise RuntimeError(f"Expected 8640 leaderboard rows, got {len(all_lb)}")

    for fold in (1, 2, 3):
        for stage in ("train", "oos"):
            for regime in ("base", "stress"):
                z = all_lb[(all_lb.fold == fold) & (all_lb.stage == stage) & (all_lb.regime == regime)].copy()
                if len(z) != 720:
                    raise RuntimeError(f"fold={fold} stage={stage} regime={regime}: expected 720, got {len(z)}")
                if z.duplicated(KEYS).any():
                    raise RuntimeError(f"Duplicate WFA cell in fold={fold} stage={stage} regime={regime}")
                out = args.out_root / f"fold_{fold}" / stage / regime
                out.mkdir(parents=True, exist_ok=True)
                z.sort_values(["gate", "mean_weekly_net"], ascending=[False, False]).to_csv(out / "leaderboard.csv", index=False)

    wk_frames = []
    for f in weeklies:
        z = pd.read_csv(f)
        if z.empty:
            continue
        z["regime"] = regime_from_path(f)
        z["fold"] = fold_from_path(f)
        z["stage"] = stage_from_path(f)
        wk_frames.append(z)
    if not wk_frames:
        raise RuntimeError("No weekly WFA records found")
    all_wk = pd.concat(wk_frames, ignore_index=True)
    all_wk.to_csv(args.out_root / "weekly_all.csv", index=False)

    selected = []
    for fold in (1, 2, 3):
        base = all_lb[(all_lb.fold == fold) & (all_lb.stage == "train") & (all_lb.regime == "base")].set_index(KEYS)
        stress = all_lb[(all_lb.fold == fold) & (all_lb.stage == "train") & (all_lb.regime == "stress")].set_index(KEYS)
        for key in base.index.intersection(stress.index):
            if bool(base.loc[key, "gate"]) and bool(stress.loc[key, "gate"]):
                rec = dict(zip(KEYS, key))
                rec["fold"] = fold
                selected.append(rec)

    selected_df = pd.DataFrame(selected)
    selected_df.to_csv(args.out_root / "training_selected_cells.csv", index=False)

    survivors = []
    if not selected_df.empty:
        for key, sel in selected_df.groupby(KEYS):
            folds = sorted(sel["fold"].astype(int).tolist())
            rec = dict(zip(KEYS, key))
            rec["folds_selected"] = ",".join(str(x) for x in folds)
            rec["fold_count"] = len(folds)
            pass_all = len(folds) >= 2

            for regime in ("base", "stress"):
                wk = all_wk[(all_wk.stage == "oos") & (all_wk.regime == regime) & (all_wk.fold.isin(folds))].copy()
                for k, v in zip(KEYS, key):
                    wk = wk[wk[k] == v]
                wk = wk.sort_values(["fold", "week"])
                expected_weeks = 12 * len(folds)
                vals = pd.to_numeric(wk["net_pnl"], errors="coerce").dropna()
                coverage = float(len(vals) / expected_weeks) if expected_weeks else 0.0

                if len(vals):
                    q05 = float(vals.quantile(0.05))
                    tail = vals[vals <= q05]
                    gross_pos = float(vals[vals > 0].sum())
                    gross_neg = float(-vals[vals < 0].sum())
                    eq = vals.cumsum()
                    dd = eq - eq.cummax()
                    metrics = {
                        "weeks": int(len(vals)),
                        "execution_coverage": coverage,
                        "mean": float(vals.mean()),
                        "median": float(vals.median()),
                        "win_rate": float((vals > 0).mean()),
                        "profit_factor": float(gross_pos / gross_neg) if gross_neg else float("inf"),
                        "max_drawdown": float(dd.min()),
                        "q05": q05,
                        "es05": float(tail.mean()) if len(tail) else q05,
                        "net_pnl": float(vals.sum()),
                        "costs": float(pd.to_numeric(wk["cost"], errors="coerce").sum()),
                        "avg_capital_proxy": float(pd.to_numeric(wk["capital_proxy"], errors="coerce").mean()),
                        "peak_capital_proxy": float(pd.to_numeric(wk["capital_proxy"], errors="coerce").max()),
                    }
                else:
                    metrics = {
                        "weeks": 0, "execution_coverage": 0.0, "mean": 0.0, "median": 0.0,
                        "win_rate": 0.0, "profit_factor": 0.0, "max_drawdown": 0.0,
                        "q05": 0.0, "es05": 0.0, "net_pnl": 0.0, "costs": 0.0,
                        "avg_capital_proxy": 0.0, "peak_capital_proxy": 0.0,
                    }
                for mk, mv in metrics.items():
                    rec[f"{regime}_oos_{mk}"] = mv

                ok = (
                    metrics["weeks"] >= 16
                    and metrics["execution_coverage"] >= 0.80
                    and metrics["mean"] >= 5000
                    and metrics["median"] >= 5000
                    and metrics["win_rate"] >= 0.70
                )
                pass_all = pass_all and ok

            if pass_all:
                rec["wfa_survivor"] = True
                survivors.append(rec)

    survivors_df = pd.DataFrame(survivors)
    if survivors_df.empty:
        survivors_df = pd.DataFrame(columns=KEYS + ["folds_selected", "fold_count", "wfa_survivor"])
    survivors_df.to_csv(args.out_root / "wfa_survivors.csv", index=False)

    overall = {
        "training_selected_fold_cell_rows": int(len(selected_df)),
        "distinct_cells_selected": int(len(selected_df.groupby(KEYS))) if not selected_df.empty else 0,
        "wfa_survivors": int(len(survivors_df)),
        "pnl_authorized": True,
    }
    args.out_root.mkdir(parents=True, exist_ok=True)
    (args.out_root / "overall_summary.json").write_text(json.dumps(overall, indent=2) + "\n")
    print(json.dumps(overall, indent=2))


if __name__ == "__main__":
    main()
