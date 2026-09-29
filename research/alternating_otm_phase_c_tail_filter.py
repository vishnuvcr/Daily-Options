from __future__ import annotations

import json
from pathlib import Path
import pandas as pd
import numpy as np

DISCOVERY_END = pd.Timestamp("2024-12-31")
HOLDOUT_START = pd.Timestamp("2025-01-01")
QUANTILES = [0.30, 0.35, 0.40, 0.45, 0.50]
FEATURES = {
    "first15_abs_ret": ">=",
    "gap_abs_pct": "<=",
    "prior20_median_range_pct": "<=",
    "prior_day_range_pct": "<=",
}
MIN_RETAIN = 0.50

def perf(df: pd.DataFrame) -> dict:
    wins = df.loc[df.net_pnl > 0, "net_pnl"]
    losses = df.loc[df.net_pnl < 0, "net_pnl"]
    net = float(df.net_pnl.sum())
    return {
        "trades": int(len(df)),
        "win_rate": float((df.net_pnl > 0).mean()) if len(df) else float("nan"),
        "gross_pnl": float(df.gross_pnl.sum()) if "gross_pnl" in df else float("nan"),
        "costs": float(df.total_cost.sum()) if "total_cost" in df else float("nan"),
        "net_pnl": net,
        "mean_pnl": float(df.net_pnl.mean()) if len(df) else float("nan"),
        "median_pnl": float(df.net_pnl.median()) if len(df) else float("nan"),
        "profit_factor": float(wins.sum() / abs(losses.sum())) if len(losses) and losses.sum() < 0 else float("nan"),
        "max_loss": float(df.net_pnl.min()) if len(df) else float("nan"),
    }

def add_drawdown(df: pd.DataFrame) -> pd.DataFrame:
    z = df.sort_values("trade_date").copy()
    z["cum_net"] = z.net_pnl.cumsum()
    z["peak"] = z.cum_net.cummax()
    z["drawdown"] = z.cum_net - z.peak
    return z

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-artifact", required=True)
    ap.add_argument("--stress-artifact", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    base = pd.read_csv(Path(args.base_artifact) / "trades.csv", parse_dates=["trade_date"])
    stress = pd.read_csv(Path(args.stress_artifact) / "trades.csv", parse_dates=["trade_date"])

    required = [
        "trade_date", "gap_abs_pct", "first15_abs_ret",
        "prior20_median_range_pct", "prior_day_range_pct",
        "net_pnl", "gross_pnl", "total_cost"
    ]
    for c in required:
        if c not in base.columns or c not in stress.columns:
            raise RuntimeError(f"Missing required column: {c}")

    if len(base) != len(stress):
        raise RuntimeError("Base/Stress trade counts differ")
    if not base.trade_date.reset_index(drop=True).equals(stress.trade_date.reset_index(drop=True)):
        raise RuntimeError("Base/Stress trade-date alignment differs")

    merged = base[required].copy()
    merged = merged.rename(columns={"net_pnl": "net_pnl_base", "gross_pnl": "gross_pnl_base", "total_cost": "cost_base"})
    merged["net_pnl_stress"] = stress.net_pnl.to_numpy()
    merged["gross_pnl_stress"] = stress.gross_pnl.to_numpy()
    merged["cost_stress"] = stress.total_cost.to_numpy()

    if merged.trade_date.duplicated().any():
        raise RuntimeError("Duplicate trade dates detected")

    discovery = merged.loc[merged.trade_date <= DISCOVERY_END].copy()
    holdout = merged.loc[merged.trade_date >= HOLDOUT_START].copy()
    if len(discovery) < 500 or len(holdout) < 100:
        raise RuntimeError(f"Unexpected split sizes: discovery={len(discovery)}, holdout={len(holdout)}")

    missing_report = {
        f: {
            "discovery_missing": int(discovery[f].isna().sum()),
            "holdout_missing": int(holdout[f].isna().sum()),
        }
        for f in FEATURES
    }
    (out / "feature_missingness.json").write_text(json.dumps(missing_report, indent=2))

    rows = []
    baselines = {
        "base": discovery.net_pnl_base.sum(),
        "stress": discovery.net_pnl_stress.sum(),
    }
    baseline_wins = {
        "base": float((discovery.net_pnl_base > 0).mean()),
        "stress": float((discovery.net_pnl_stress > 0).mean()),
    }

    for feature, op in FEATURES.items():
        for q in QUANTILES:
            threshold = float(discovery[feature].quantile(q))
            available_d = discovery[feature].notna()
            available_h = holdout[feature].notna()

            if op == ">=":
                cond_d = discovery[feature] >= threshold
                cond_h = holdout[feature] >= threshold
            else:
                cond_d = discovery[feature] <= threshold
                cond_h = holdout[feature] <= threshold

            # Missing values are retained rather than treated as an economic signal.
            keep_d = (~available_d) | cond_d
            keep_h = (~available_h) | cond_h

            d_b = discovery.loc[keep_d]
            d_s = discovery.loc[keep_d]

            base_improvement = float(d_b.net_pnl_base.sum() - baselines["base"])
            stress_improvement = float(d_s.net_pnl_stress.sum() - baselines["stress"])
            base_retain = float(len(d_b) / len(discovery))
            stress_retain = float(len(d_s) / len(discovery))
            eligible = (
                base_retain >= MIN_RETAIN
                and stress_retain >= MIN_RETAIN
                and base_improvement > 0
                and stress_improvement > 0
            )
            rows.append({
                "feature": feature,
                "operator": op,
                "quantile": q,
                "threshold": threshold,
                "discovery_trades": len(d_b),
                "discovery_retain_pct": base_retain,
                "discovery_base_win_rate": float((d_b.net_pnl_base > 0).mean()),
                "discovery_stress_win_rate": float((d_s.net_pnl_stress > 0).mean()),
                "discovery_base_net": float(d_b.net_pnl_base.sum()),
                "discovery_stress_net": float(d_s.net_pnl_stress.sum()),
                "base_improvement": base_improvement,
                "stress_improvement": stress_improvement,
                "mean_improvement": (base_improvement + stress_improvement) / 2.0,
                "min_improvement": min(base_improvement, stress_improvement),
                "eligible": eligible,
                "holdout_trade_count_under_rule": int(holdout.loc[keep_h].shape[0]),
            })

    candidates = pd.DataFrame(rows)
    candidates.to_csv(out / "candidate_grid_discovery.csv", index=False)

    eligible = candidates.loc[candidates.eligible].copy()
    if eligible.empty:
        raise RuntimeError("No eligible discovery candidate")

    eligible = eligible.sort_values(
        ["mean_improvement", "min_improvement", "discovery_retain_pct",
         "discovery_base_win_rate", "discovery_stress_win_rate"],
        ascending=[False, False, False, False, False],
    ).reset_index(drop=True)
    selected = eligible.iloc[0].to_dict()
    (out / "selected_rule.json").write_text(json.dumps(selected, indent=2))

    selected_feature = selected["feature"]
    selected_op = selected["operator"]
    selected_threshold = float(selected["threshold"])

    if selected_op == ">=":
        hold_cond = holdout[selected_feature] >= selected_threshold
    else:
        hold_cond = holdout[selected_feature] <= selected_threshold
    hold_keep = (~holdout[selected_feature].notna()) | hold_cond
    hold = holdout.loc[hold_keep].copy()

    selected_hold_rows = []
    for friction, net_col, gross_col, cost_col in [
        ("base", "net_pnl_base", "gross_pnl_base", "cost_base"),
        ("stress", "net_pnl_stress", "gross_pnl_stress", "cost_stress"),
    ]:
        z = hold.rename(columns={net_col: "net_pnl", gross_col: "gross_pnl", cost_col: "total_cost"}).copy()
        s = perf(z)
        z = add_drawdown(z)
        s["max_drawdown"] = float(z.drawdown.min())
        s["friction"] = friction
        s["selected_feature"] = selected_feature
        s["selected_operator"] = selected_op
        s["selected_threshold"] = selected_threshold
        s["retained_share"] = float(len(z) / len(holdout))
        selected_hold_rows.append(s)
    hold_summary = pd.DataFrame(selected_hold_rows)
    hold_summary.to_csv(out / "selected_holdout_summary.csv", index=False)

    annual_rows = []
    for friction, net_col in [("base", "net_pnl_base"), ("stress", "net_pnl_stress")]:
        tmp = hold.copy()
        tmp["year"] = tmp.trade_date.dt.year
        for year, g in tmp.groupby("year"):
            annual_rows.append({
                "friction": friction,
                "year": int(year),
                "trades": int(len(g)),
                "net_pnl": float(g[net_col].sum()),
                "win_rate": float((g[net_col] > 0).mean()),
                "mean_pnl": float(g[net_col].mean()),
            })
    pd.DataFrame(annual_rows).to_csv(out / "selected_holdout_annual.csv", index=False)

    sens_rows = []
    for q in [0.40, 0.45, 0.50]:
        thr = float(discovery[selected_feature].quantile(q))
        k = holdout[selected_feature] >= thr if selected_op == ">=" else holdout[selected_feature] <= thr
        k = (~holdout[selected_feature].notna()) | k
        for friction, net_col in [("base", "net_pnl_base"), ("stress", "net_pnl_stress")]:
            g = holdout.loc[k]
            sens_rows.append({
                "friction": friction,
                "quantile": q,
                "threshold": thr,
                "trades": int(len(g)),
                "retained_share": float(len(g) / len(holdout)),
                "win_rate": float((g[net_col] > 0).mean()),
                "net_pnl": float(g[net_col].sum()),
                "mean_pnl": float(g[net_col].mean()),
            })
    pd.DataFrame(sens_rows).to_csv(out / "selected_rule_sensitivity.csv", index=False)

    result = {
        "status": "completed",
        "discovery_trades": len(discovery),
        "holdout_trades": len(holdout),
        "baseline_discovery_win_rate": baseline_wins,
        "selected_rule": {
            "feature": selected_feature,
            "operator": selected_op,
            "threshold": selected_threshold,
            "selection_quantile": selected["quantile"],
        },
        "holdout_selected": hold_summary.to_dict(orient="records"),
    }
    (out / "phase_c_result.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
