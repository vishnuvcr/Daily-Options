#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from datetime import date
import argparse, json, math
import duckdb
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from research.phase31_7_oi_volume_microstructure import lot_size, charge, price_key

START = date(2021, 7, 1)
END = date(2026, 8, 31)
FEATURES = ("SKEW_Z", "SMILE_Z")
THRESHOLDS = (1.0, 1.5)
HORIZONS = ("H10_30", "H13_30", "H15_10")
HORIZON_TIMES = {"H10_30": "10:30:00", "H13_30": "13:30:00", "H15_10": "15:10:00"}
NULL_SEEDS = (101, 202, 303, 404, 505)
WARMUP = 60
ATM_STEP = 50
WING = 100
INNER = 50
DATA_REVISION = "51ca58c"

def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def bs_price(spot: float, strike: float, t: float, sigma: float, call: bool) -> float:
    if min(spot, strike, t, sigma) <= 0:
        return max(spot - strike, 0.0) if call else max(strike - spot, 0.0)
    d1 = (math.log(spot / strike) + 0.5 * sigma * sigma * t) / (sigma * math.sqrt(t))
    d2 = d1 - sigma * math.sqrt(t)
    if call:
        return spot * norm_cdf(d1) - strike * norm_cdf(d2)
    return strike * norm_cdf(-d2) - spot * norm_cdf(-d1)

def implied_vol(spot: float, strike: float, t: float, target: float, call: bool) -> float | None:
    if not all(np.isfinite([spot, strike, t, target])) or min(spot, strike, t, target) <= 0:
        return None
    intrinsic = max(spot - strike, 0.0) if call else max(strike - spot, 0.0)
    upper = spot if call else strike
    # A tiny tolerance permits rounded OHLC values at the no-arbitrage boundary.
    if target + 1e-8 < intrinsic or target - 1e-8 > upper:
        return None
    lo, hi = 1e-5, 5.0
    if bs_price(spot, strike, t, hi, call) < target:
        return None
    for _ in range(90):
        mid = 0.5 * (lo + hi)
        p = bs_price(spot, strike, t, mid, call)
        if p < target:
            lo = mid
        else:
            hi = mid
    iv = 0.5 * (lo + hi)
    return iv if np.isfinite(iv) and 0 < iv < 5.0 else None

def load_index(root: Path) -> pd.DataFrame:
    con = duckdb.connect()
    p = str(root / "index/NIFTY.parquet").replace("'", "''")
    q = f"""
      SELECT CAST(timestamp AS TIMESTAMP) ts,
             CAST(close AS DOUBLE) close_px
      FROM read_parquet('{p}')
      WHERE CAST(timestamp AS DATE) BETWEEN DATE '{START}' AND DATE '{END}'
      ORDER BY ts
    """
    x = con.execute(q).df()
    con.close()
    x["ts"] = pd.to_datetime(x["ts"])
    x["date"] = x.ts.dt.date
    x["time"] = x.ts.dt.strftime("%H:%M:%S")
    x = x[x.time == "09:30:00"].copy()
    return x.drop_duplicates("date").sort_values("date").reset_index(drop=True)

def expiry_files(root: Path) -> dict[date, Path]:
    out = {}
    for p in sorted((root / "options/NIFTY").glob("*.parquet")):
        try:
            out[pd.Timestamp(p.stem).date()] = p
        except Exception:
            continue
    return out

def attach_expiry(index_df: pd.DataFrame, expiry_map: dict[date, Path]) -> pd.DataFrame:
    exps = sorted(expiry_map)
    out = index_df.copy()
    out["expiry"] = [
        next((e for e in exps if e > d), None)  # strictly next expiry
        for d in out["date"]
    ]
    out["atm"] = (out["close_px"] / ATM_STEP).round() * ATM_STEP
    return out

def quote_time_row(q: pd.DataFrame, time_str: str, field: str) -> dict[tuple, float]:
    x = q[q["local_time"] == time_str].copy()
    return {(r.date, r.option_type, float(r.strike)): float(getattr(r, field)) for r in x.itertuples(index=False)}

def load_quotes(root: Path, panel: pd.DataFrame, expiry_map: dict[date, Path]) -> pd.DataFrame:
    rows = []
    con = duckdb.connect()
    con.execute("SET TimeZone='Asia/Kolkata'")
    work = panel.dropna(subset=["expiry", "atm"]).copy()
    for expiry, g in work.groupby("expiry"):
        path = expiry_map[expiry]
        dates = sorted(g["date"].tolist())
        strikes = sorted(set(float(v) for v in g["atm"]) |
                         set(float(v) + WING for v in g["atm"]) |
                         set(float(v) - WING for v in g["atm"]) |
                         set(float(v) + INNER for v in g["atm"]) |
                         set(float(v) - INNER for v in g["atm"]))
        date_sql = ",".join(f"DATE '{d}'" for d in dates)
        strike_sql = ",".join(str(v) for v in strikes)
        p = str(path).replace("'", "''")
        q = f"""
          SELECT CAST(timestamp AS TIMESTAMP) ts,
                 CAST(CAST(timestamp AS TIMESTAMP) AS DATE) date,
                 strftime(CAST(timestamp AS TIMESTAMP),'%H:%M:%S') local_time,
                 UPPER(CAST(option_type AS VARCHAR)) option_type,
                 CAST(strike AS DOUBLE) strike,
                 CAST(open AS DOUBLE) open_px,
                 CAST(close AS DOUBLE) close_px,
                 CAST(volume AS DOUBLE) volume,
                 CAST(open_interest AS DOUBLE) oi
          FROM read_parquet('{p}')
          WHERE CAST(timestamp AS DATE) IN ({date_sql})
            AND strike IN ({strike_sql})
            AND UPPER(CAST(option_type AS VARCHAR)) IN ('CE','PE')
            AND strftime(CAST(timestamp AS TIMESTAMP),'%H:%M:%S')
                IN ('09:30:00','09:31:00','10:30:00','13:30:00','15:10:00')
        """
        z = con.execute(q).df()
        rows.append(z)
    con.close()
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(
        columns=["ts","date","local_time","option_type","strike","open_px","close_px","volume","oi"]
    )

def build_surface(panel: pd.DataFrame, quotes: pd.DataFrame) -> pd.DataFrame:
    x = panel.copy()
    x["surface_valid"] = False
    x["iv_atm_ce"] = np.nan
    x["iv_atm_pe"] = np.nan
    x["iv_put100"] = np.nan
    x["iv_call100"] = np.nan
    quote_idx = quotes.set_index(["date","local_time","option_type","strike"])
    for i, r in x.iterrows():
        if pd.isna(r.expiry):
            continue
        d = r["date"]; atm = float(r["atm"]); expiry = pd.Timestamp(r["expiry"]).date()
        t = max((pd.Timestamp(f"{expiry} 15:30:00") - pd.Timestamp(f"{d} 09:30:00")).total_seconds() / 31536000.0, 1e-8)
        vals = {}
        ok = True
        for typ, strike, col in (
            ("CE", atm, "iv_atm_ce"),
            ("PE", atm, "iv_atm_pe"),
            ("PE", atm - WING, "iv_put100"),
            ("CE", atm + WING, "iv_call100"),
        ):
            try:
                px = float(quote_idx.loc[(d, "09:30:00", typ, strike), "close_px"])
            except Exception:
                ok = False
                break
            iv = implied_vol(float(r.close_px), strike, t, px, typ == "CE")
            if iv is None:
                ok = False
                break
            vals[col] = iv * 100.0
        if ok:
            x.at[i, "surface_valid"] = True
            for k, v in vals.items():
                x.at[i, k] = v
    x["skew_volpts"] = x["iv_put100"] - x["iv_call100"]
    x["smile_volpts"] = ((x["iv_put100"] + x["iv_call100"]) / 2.0
                         - (x["iv_atm_ce"] + x["iv_atm_pe"]) / 2.0)
    for raw, zcol in (("skew_volpts","SKEW_Z"),("smile_volpts","SMILE_Z")):
        prior = x[raw].shift(1)
        mu = prior.rolling(WARMUP, min_periods=WARMUP).mean()
        sd = prior.rolling(WARMUP, min_periods=WARMUP).std(ddof=1)
        x[zcol] = (x[raw] - mu) / sd
    x["prior_surface_date"] = x["date"].shift(1)
    x["barrier_ok"] = x["prior_surface_date"].notna() & (
        pd.to_datetime(x["prior_surface_date"]) < pd.to_datetime(x["date"])
    )
    x["feature_eligible"] = x[list(FEATURES)].notna().all(axis=1)
    return x

def data_gate(panel: pd.DataFrame, quotes: pd.DataFrame, expiry_map: dict[date, Path]) -> dict:
    warm = panel.iloc[WARMUP:].copy()
    eligible_expiry = warm["expiry"].notna()
    surface_cov = float(warm["surface_valid"].mean()) if len(warm) else 0.0
    iv_complete = int(warm["surface_valid"].sum())
    barrier_violations = int((panel["feature_eligible"] & ~panel["barrier_ok"]).sum())
    feature_sessions = int(panel["feature_eligible"].sum())
    return {
        "status": "PASS" if (
            len(warm) and float(eligible_expiry.mean()) >= 0.95
            and surface_cov >= 0.95
            and barrier_violations == 0
        ) else "FAIL",
        "raw_nifty_09_30_sessions": int(len(panel)),
        "warmup_sessions": int(min(WARMUP, len(panel))),
        "feature_eligible_sessions": feature_sessions,
        "warmup_expiry_coverage": float(eligible_expiry.mean()) if len(warm) else 0.0,
        "surface_quote_iv_coverage": surface_cov,
        "surface_complete_sessions": iv_complete,
        "prior_surface_barrier_violations": barrier_violations,
        "expiry_file_count": len(expiry_map),
        "required_surface_coverage": 0.95,
        "study_start": str(START),
        "study_end": str(END),
        "dataset_revision": DATA_REVISION,
        "option_cache_files_observed": int(quotes["date"].nunique()) if not quotes.empty else 0,
    }

def build_signals(panel: pd.DataFrame, null_seed: int | None = None) -> pd.DataFrame:
    x = panel.copy()
    if null_seed is not None:
        rng = np.random.default_rng(null_seed)
        for f in FEATURES:
            vals = x[f].to_numpy(copy=True)
            rng.shuffle(vals)
            x[f] = vals
    rows = []
    for feature in FEATURES:
        for threshold in THRESHOLDS:
            for horizon in HORIZONS:
                z = x[x[feature].abs() >= threshold].copy()
                if z.empty:
                    continue
                z["feature"] = feature
                z["threshold"] = threshold
                z["horizon"] = horizon
                z["signal_value"] = z[feature]
                z["signal_sign"] = np.where(z["signal_value"] > 0, "HIGH", "LOW")
                rows.append(z)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()

def legs_for_signal(feature: str, signal_value: float, atm: int) -> list[tuple[str,int,str]]:
    if feature == "SKEW_Z":
        positive = [
            ("CE", atm + INNER, "BUY"),
            ("CE", atm + WING, "SELL"),
            ("PE", atm - WING, "SELL"),
            ("PE", atm - INNER, "BUY"),
        ]
    else:
        positive = [
            ("PE", atm - INNER, "SELL"),
            ("PE", atm - WING, "BUY"),
            ("CE", atm + INNER, "SELL"),
            ("CE", atm + WING, "BUY"),
        ]
    if signal_value >= 0:
        return positive
    return [(typ, strike, "SELL" if action == "BUY" else "BUY") for typ, strike, action in positive]

def price_lookup(quotes: pd.DataFrame) -> dict[tuple,date]:
    out = {}
    for r in quotes.itertuples(index=False):
        px_open = float(r.open_px) if pd.notna(r.open_px) else np.nan
        px_close = float(r.close_px) if pd.notna(r.close_px) else np.nan
        px = px_open if r.local_time == "09:31:00" else px_close
        if pd.notna(px) and px > 0:
            out[(r.date, r.local_time, r.option_type, float(r.strike))] = px
    return out

def trade_from_signal(r, prices: dict, slip: float):
    d = pd.Timestamp(r.date).date()
    legs = legs_for_signal(r.feature, float(r.signal_value), int(r.atm))
    lot = lot_size(pd.Timestamp(r.expiry).date())
    exit_time = HORIZON_TIMES[r.horizon]
    raw = execgross = slippage_cost = transaction_costs = 0.0
    leg_rows = []
    for typ, strike, action in legs:
        ep = prices.get((d, "09:31:00", typ, float(strike)))
        xp = prices.get((d, exit_time, typ, float(strike)))
        if ep is None or xp is None:
            return None
        if action == "BUY":
            ee, xx = ep + slip, max(0.0, xp - slip)
            rp, eg = (xp - ep) * lot, (xx - ee) * lot
            exit_action = "SELL"
        else:
            ee, xx = max(0.0, ep - slip), xp + slip
            rp, eg = (ep - xp) * lot, (ee - xx) * lot
            exit_action = "BUY"
        tc = charge(ee, action, 1, lot, d) + charge(xx, exit_action, 1, lot, d)
        raw += rp
        execgross += eg
        slippage_cost += rp - eg
        transaction_costs += tc
        leg_rows.append({"type":typ,"strike":strike,"action":action,"entry":ep,"exit":xp})
    return {
        "day": str(d),
        "expiry": str(pd.Timestamp(r.expiry).date()),
        "feature": r.feature,
        "threshold": float(r.threshold),
        "horizon": r.horizon,
        "signal_value": float(r.signal_value),
        "signal_sign": r.signal_sign,
        "atm": int(r.atm),
        "raw_gross": raw,
        "execution_gross": execgross,
        "slippage_cost": slippage_cost,
        "transaction_costs": transaction_costs,
        "net_pnl": execgross - transaction_costs,
        "legs": json.dumps(leg_rows, separators=(",",":")),
    }

def add_summary_rows(trades: pd.DataFrame, friction: str) -> pd.DataFrame:
    rows = []
    for feature in FEATURES:
        for threshold in THRESHOLDS:
            for horizon in HORIZONS:
                g = trades[(trades.feature == feature)
                           & (trades.threshold == threshold)
                           & (trades.horizon == horizon)] if not trades.empty else trades.iloc[0:0]
                if g.empty:
                    rows.append({"feature":feature,"threshold":threshold,"horizon":horizon,"friction":friction,
                                 "trades":0,"weeks":0,"total_net":0.0,"mean_weekly_net":0.0,
                                 "median_weekly_net":0.0,"positive_week_rate":0.0,"worst_trade":np.nan,
                                 "worst_week":np.nan,"max_drawdown":np.nan,"raw_gross":0.0,
                                 "total_slippage":0.0,"total_transaction_costs":0.0})
                    continue
                wk = g.assign(week=pd.to_datetime(g.day).dt.to_period("W-SUN").astype(str)).groupby("week").net_pnl.sum()
                eq = wk.sort_index().cumsum()
                dd = eq - eq.cummax()
                rows.append({"feature":feature,"threshold":threshold,"horizon":horizon,"friction":friction,
                             "trades":int(len(g)),"weeks":int(len(wk)),
                             "total_net":float(g.net_pnl.sum()),"mean_weekly_net":float(wk.mean()),
                             "median_weekly_net":float(wk.median()),
                             "positive_week_rate":float((wk > 0).mean()),
                             "worst_trade":float(g.net_pnl.min()),"worst_week":float(wk.min()),
                             "max_drawdown":float(dd.min()),
                             "raw_gross":float(g.raw_gross.sum()),
                             "total_slippage":float(g.slippage_cost.sum()),
                             "total_transaction_costs":float(g.transaction_costs.sum())})
    return pd.DataFrame(rows)

def bootstrap_intervals(trades: pd.DataFrame, summary: pd.DataFrame, friction: str, n: int = 1000, seed: int = 32026) -> pd.DataFrame:
    rows = []
    rng = np.random.default_rng(seed)
    for r in summary.itertuples(index=False):
        g = trades[(trades.feature==r.feature)&(trades.threshold==r.threshold)&(trades.horizon==r.horizon)] if not trades.empty else trades.iloc[0:0]
        if g.empty:
            rows.append({**r._asdict(),"bootstrap_lo":np.nan,"bootstrap_hi":np.nan})
            continue
        wk = g.assign(week=pd.to_datetime(g.day).dt.to_period("W-SUN").astype(str)).groupby("week").net_pnl.sum().to_numpy(float)
        samples = rng.choice(wk, size=(n, len(wk)), replace=True).mean(axis=1)
        rows.append({**r._asdict(),"bootstrap_lo":float(np.quantile(samples,0.025)),
                     "bootstrap_hi":float(np.quantile(samples,0.975))})
    return pd.DataFrame(rows)

def write_plots(summary_base, summary_stress, trades_base, out: Path):
    plt.figure(figsize=(12,6))
    labels = [f"{r.feature}:{r.threshold:g}:{r.horizon}" for r in summary_base.itertuples()]
    x = np.arange(len(labels))
    plt.bar(x - 0.18, summary_base.mean_weekly_net, width=0.36, label="Base")
    plt.bar(x + 0.18, summary_stress.mean_weekly_net, width=0.36, label="Stress")
    plt.axhline(5000, linestyle="--", linewidth=1)
    plt.xticks(x, labels, rotation=70, ha="right", fontsize=7)
    plt.ylabel("Mean weekly net P&L (₹)")
    plt.title("Phase 32 frozen discovery: weekly economics")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out/"mean_weekly_net_base_stress.png", dpi=160)
    plt.close()

    if not trades_base.empty:
        best = summary_base.sort_values("mean_weekly_net", ascending=False).iloc[0]
        g = trades_base[(trades_base.feature==best.feature)&(trades_base.threshold==best.threshold)&(trades_base.horizon==best.horizon)]
        wk = g.assign(week=pd.to_datetime(g.day).dt.to_period("W-SUN").astype(str)).groupby("week").net_pnl.sum().sort_index().cumsum()
        plt.figure(figsize=(11,5))
        plot_dates = pd.PeriodIndex(wk.index, freq="W-SUN").to_timestamp(how="end")
        plt.plot(plot_dates, wk.values)
        plt.axhline(0, linestyle="--", linewidth=1)
        plt.ylabel("Cumulative weekly net P&L (₹)")
        plt.title(f"Phase 32 best Base cell: {best.feature} | |z|≥{best.threshold:g} | {best.horizon}")
        plt.tight_layout()
        plt.savefig(out/"best_base_cumulative.png", dpi=160)
        plt.close()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/cache/phase31_trademarkk")
    ap.add_argument("--out", default="reports/phase32")
    ap.add_argument("--slippage", type=float, default=0.20)
    ap.add_argument("--gate-only", action="store_true")
    args = ap.parse_args()

    root = Path(args.data)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    idx = load_index(root)
    exps = expiry_files(root)
    panel = attach_expiry(idx, exps)
    quotes = load_quotes(root, panel, exps)
    panel = build_surface(panel, quotes)
    panel.to_csv(out/"surface_feature_panel.csv", index=False)
    gate = data_gate(panel, quotes, exps)
    (out/"data_gate.json").write_text(json.dumps(gate, indent=2, default=str), encoding="utf-8")
    (out/"source_manifest.json").write_text(json.dumps({
        "dataset_repo":"thetrademarkk/india-index-options-1m",
        "revision":DATA_REVISION,
        "study_start":str(START),
        "study_end":str(END),
        "source_urls":[
            "https://huggingface.co/datasets/thetrademarkk/india-index-options-1m",
            "https://www.nseindia.com/option-chain",
            "https://www.nseindia.com/all-reports-derivatives"
        ]
    }, indent=2), encoding="utf-8")

    if args.gate_only or gate["status"] != "PASS":
        print(json.dumps(gate, indent=2, default=str))
        return

    sig = build_signals(panel)
    sig.to_csv(out/"true_signals.csv", index=False)
    prices = price_lookup(quotes)

    cov_rows = []
    for key, g in sig.groupby(["feature","threshold","horizon"]):
        complete = 0
        for r in g.itertuples(index=False):
            d = pd.Timestamp(r.date).date()
            complete += int(all(
                (d, tm, typ, float(strike)) in prices
                for typ, strike, action in legs_for_signal(r.feature,float(r.signal_value),int(r.atm))
                for tm in ("09:31:00", HORIZON_TIMES[r.horizon])
            ))
        cov_rows.append({
            "feature":key[0],"threshold":float(key[1]),"horizon":key[2],
            "signals":int(len(g)),"complete_price_coverage":int(complete),
            "coverage_rate":float(complete/len(g)) if len(g) else 0.0
        })
    coverage = pd.DataFrame(cov_rows)
    coverage.to_csv(out/"price_coverage.csv", index=False)

    rows = []
    for r in sig.itertuples(index=False):
        t = trade_from_signal(r, prices, args.slippage)
        if t:
            rows.append(t)
    trades = pd.DataFrame(rows)
    friction = "base" if args.slippage == 0.20 else "stress"
    trades.to_csv(out/f"trades_{friction}.csv", index=False)
    summary = add_summary_rows(trades, friction)
    summary.to_csv(out/f"true_cell_summary_{friction}.csv", index=False)
    weekly = trades.assign(week=pd.to_datetime(trades.day).dt.to_period("W-SUN").astype(str)).groupby(
        ["feature","threshold","horizon","week"], as_index=False).net_pnl.sum()
    weekly.to_csv(out/f"weekly_{friction}.csv", index=False)

    null_rows = []
    for seed in NULL_SEEDS:
        ns = build_signals(panel, null_seed=seed)
        for r in ns.itertuples(index=False):
            t = trade_from_signal(r, prices, args.slippage)
            if t:
                t["null_seed"] = seed
                null_rows.append(t)
    null_trades = pd.DataFrame(null_rows)
    null_trades.to_csv(out/f"null_trades_{friction}.csv", index=False)
    null_summary = []
    for seed in NULL_SEEDS:
        g = null_trades[null_trades.null_seed == seed] if not null_trades.empty else null_trades.iloc[0:0]
        q = add_summary_rows(g, friction)
        q.insert(1, "null_seed", seed)
        null_summary.append(q)
    pd.concat(null_summary, ignore_index=True).to_csv(out/f"null_summary_{friction}.csv", index=False)

    ci = bootstrap_intervals(trades, summary, friction)
    ci.to_csv(out/f"bootstrap_summary_{friction}.csv", index=False)

    if friction == "stress":
        base_dir = out.parent / "base"
        if (base_dir/"true_cell_summary_base.csv").exists():
            sb = pd.read_csv(base_dir/"true_cell_summary_base.csv")
            tb = pd.read_csv(base_dir/"trades_base.csv")
            ss = pd.read_csv(out/"true_cell_summary_stress.csv")
            write_plots(sb, ss, tb, out.parent)

    print(json.dumps(gate, indent=2, default=str))

if __name__ == "__main__":
    main()
