from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from research.contracts import nifty_lot_size
from research.cost_model import OptionCostModel

ANNUAL_MINUTES = 252 * 375
RISK_FREE = 0.06


@dataclass(frozen=True)
class Config:
    entry_minutes: int
    stop_mult: float
    target_decay: float
    hold_minutes: int
    gap_max: float | None
    first15_range_max: float | None
    vrp_min: float | None


def load(path: Path):
    spot = pd.read_excel(path, sheet_name="Spot_1min")
    opt = pd.read_excel(path, sheet_name="ATM_Options_1min")
    spot["timestamp"] = pd.to_datetime(spot["Date"].astype(str) + " " + spot["Time"].astype(str))
    opt["timestamp"] = pd.to_datetime(opt["Timestamp"], utc=True).dt.tz_convert("Asia/Kolkata").dt.tz_localize(None)
    spot = spot.rename(columns={"Open":"open","High":"high","Low":"low","Close":"close","Volume":"volume"})
    opt = opt.rename(columns={"Open":"open","High":"high","Low":"low","Close":"close","Volume":"volume","Type":"option_type","Strike":"strike","Expiry":"expiry"})
    opt["option_type"] = opt["option_type"].astype(str).str.upper().replace({"CALL":"CE","PUT":"PE"})
    opt["expiry"] = pd.to_datetime(opt["expiry"], errors="coerce")
    for c in ["open","high","low","close","volume","strike"]:
        opt[c] = pd.to_numeric(opt[c], errors="coerce")
    return (
        spot.dropna(subset=["timestamp","close"]).sort_values("timestamp"),
        opt.dropna(subset=["timestamp","close","strike","expiry"]).sort_values("timestamp"),
    )


def implied_vol_from_straddle(s: float, k: float, years: float, premium: float) -> float:
    if s <= 0 or k <= 0 or premium <= 0 or years <= 0:
        return np.nan

    def cdf(x):
        return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

    def call(sig):
        if sig <= 0:
            return max(s - k * math.exp(-RISK_FREE * years), 0.0)
        d1 = (math.log(s/k) + (RISK_FREE + 0.5*sig*sig)*years) / (sig*math.sqrt(years))
        d2 = d1 - sig*math.sqrt(years)
        return s*cdf(d1) - k*math.exp(-RISK_FREE*years)*cdf(d2)

    intrinsic = max(s-k, 0.0) + max(k-s, 0.0)
    if premium <= intrinsic:
        return np.nan

    lo, hi = 1e-4, 5.0
    for _ in range(60):
        mid = (lo + hi) / 2
        model = call(mid) + (call(mid) - s + k*math.exp(-RISK_FREE*years))
        if model > premium:
            hi = mid
        else:
            lo = mid
    return (lo+hi)/2


def build_days(spot, opt):
    spot_days = {d: ds.copy() for d, ds in spot.groupby(spot.timestamp.dt.date)}
    opt_days = {d: do.copy() for d, do in opt.groupby(opt.timestamp.dt.date)}
    days = []

    for d, ds in spot_days.items():
        do = opt_days.get(d)
        if do is None:
            continue
        ds = ds.sort_values("timestamp").copy()
        do = do.sort_values("timestamp").copy()
        prev_day = spot[spot.timestamp.dt.date < d].sort_values("timestamp")
        prev_close = float(prev_day.close.iloc[-1]) if not prev_day.empty else np.nan

        for entry_minutes in (15, 30, 45, 60, 75, 90, 105):
            entry_time = pd.Timestamp(d) + pd.Timedelta(hours=9, minutes=15+entry_minutes)
            q = do[(do.timestamp >= entry_time) & (do.timestamp <= entry_time + pd.Timedelta(minutes=3)) & (do.close > 0)]
            if q.empty:
                continue

            srow = ds[ds.timestamp <= entry_time].tail(1)
            if srow.empty:
                continue
            spot_px = float(srow.close.iloc[0])
            strikes = q.strike.dropna().unique()
            if len(strikes) == 0:
                continue
            strike = float(min(strikes, key=lambda x: abs(x-spot_px)))

            ce = q[(q.option_type=="CE") & (q.strike==strike)].sort_values("timestamp")
            pe = q[(q.option_type=="PE") & (q.strike==strike)].sort_values("timestamp")
            common = sorted(set(ce.timestamp) & set(pe.timestamp))
            if not common:
                continue
            et = common[0]
            ce0 = float(ce.loc[ce.timestamp==et, "close"].iloc[0])
            pe0 = float(pe.loc[pe.timestamp==et, "close"].iloc[0])
            entry = ce0 + pe0
            if entry <= 0:
                continue

            hist = ds[(ds.timestamp < et) & (ds.timestamp >= et - pd.Timedelta(minutes=30))].close
            rv = float(hist.pct_change().dropna().std() * math.sqrt(ANNUAL_MINUTES)) if len(hist) >= 15 else np.nan

            expiry = pd.Timestamp(ce.iloc[0].expiry)
            years = max((expiry - et) / pd.Timedelta(days=365.25), 1/3650)
            iv = implied_vol_from_straddle(spot_px, strike, float(years), entry)
            vrp = iv-rv if np.isfinite(iv) and np.isfinite(rv) else np.nan

            open_px = float(ds[ds.timestamp.dt.time <= pd.Timestamp("09:15").time()].close.iloc[0]) if False else float(ds.open.iloc[0])
            gap = abs((open_px-prev_close)/prev_close) if np.isfinite(prev_close) and prev_close else np.nan

            first15_end = pd.Timestamp(d) + pd.Timedelta(hours=9, minutes=30)
            r15 = ds[(ds.timestamp >= pd.Timestamp(d)+pd.Timedelta(hours=9, minutes=15)) & (ds.timestamp < first15_end)]
            first15_range = float((r15.high.max()-r15.low.min())/spot_px) if not r15.empty else np.nan

            path = do[(do.timestamp > et) & (do.timestamp <= et + pd.Timedelta(minutes=240)) & (do.strike==strike)]
            piv = path.pivot_table(index="timestamp", columns="option_type", values=["high","low","close"], aggfunc="last")
            if piv.empty or not {"CE","PE"}.issubset(set(piv["close"].columns)):
                continue
            piv = piv.dropna(subset=[("close","CE"),("close","PE")])
            if piv.empty:
                continue

            days.append({
                "date": d, "entry_minutes": entry_minutes, "entry_time": et,
                "strike": strike, "entry": entry, "gap": gap,
                "first15_range": first15_range, "iv": iv, "rv": rv, "vrp": vrp,
                "piv": piv, "lot": nifty_lot_size(d),
            })

    return days, len(spot_days)


def simulate(row, stop_mult, target_decay, hold_minutes):
    piv = row["piv"]
    end = row["entry_time"] + pd.Timedelta(minutes=hold_minutes)
    piv = piv[piv.index <= end]
    entry = row["entry"]
    stop = entry * stop_mult
    target = entry * (1-target_decay)
    xt = None
    exit_val = None
    reason = "time"

    for t, r in piv.iterrows():
        hi = float(r[("high","CE")] + r[("high","PE")])
        lo = float(r[("low","CE")] + r[("low","PE")])
        close = float(r[("close","CE")] + r[("close","PE")])
        if hi >= stop:
            xt, exit_val, reason = t, stop, "stop"
            break
        if lo <= target:
            xt, exit_val, reason = t, target, "target"
            break
        xt, exit_val = t, close

    return xt, exit_val, reason


def evaluate(rows, configs, all_days):
    cm = OptionCostModel()
    results = []
    trades_store = []

    for cfg in configs:
        trade_pnl = {}
        records = []
        for row in rows:
            if row["entry_minutes"] != cfg.entry_minutes:
                continue
            if cfg.gap_max is not None and (not np.isfinite(row["gap"]) or row["gap"] > cfg.gap_max):
                continue
            if cfg.first15_range_max is not None and (not np.isfinite(row["first15_range"]) or row["first15_range"] > cfg.first15_range_max):
                continue
            if cfg.vrp_min is not None and (not np.isfinite(row["vrp"]) or row["vrp"] < cfg.vrp_min):
                continue

            xt, exit_val, reason = simulate(row, cfg.stop_mult, cfg.target_decay, cfg.hold_minutes)
            if xt is None:
                continue

            piv = row["piv"]
            er = piv.loc[xt]
            ce_exit = float(er[("close","CE")])
            pe_exit = float(er[("close","PE")])
            # Conservative: use actual close at the exit minute even when the stop/target
            # was touched intrabar; this prevents target-touch optimism.
            net = cm.short_straddle_net_pnl(
                float(row["entry"] - pe_exit),
                float(pe_exit),
                float(ce_exit),
                float(0.0),
                row["lot"],
            )
            # Replace the leg accounting above with an explicit short-straddle call.
            gross = (row["entry"] - (ce_exit+pe_exit)) * row["lot"]
            turnover = (row["entry"] + ce_exit + pe_exit) * row["lot"]
            brokerage = 4.0 * cm.brokerage_per_order
            exchange = turnover * cm.exchange_rate
            sebi = turnover * cm.sebi_rate
            stt = row["entry"] * row["lot"] * cm.stt_sell_rate
            stamp = (ce_exit+pe_exit) * row["lot"] * cm.stamp_buy_rate
            gst = cm.gst_rate * (brokerage + exchange + sebi)
            slippage = 4.0 * 0.20 * row["lot"]
            net = gross - (brokerage+exchange+sebi+stt+stamp+gst+slippage)

            trade_pnl[row["date"]] = trade_pnl.get(row["date"], 0.0) + net
            records.append({
                "date": str(row["date"]), "entry_time": row["entry_time"].isoformat(),
                "entry_minutes": cfg.entry_minutes, "stop_mult": cfg.stop_mult,
                "target_decay": cfg.target_decay, "hold_minutes": cfg.hold_minutes,
                "gap_max": cfg.gap_max, "first15_range_max": cfg.first15_range_max,
                "vrp_min": cfg.vrp_min, "entry_straddle": row["entry"],
                "exit_straddle": ce_exit+pe_exit, "net_pnl": net, "reason": reason,
                "lot_size": row["lot"], "vrp": row["vrp"],
            })

        daily = pd.Series(trade_pnl, dtype=float)
        all_daily = pd.Series(0.0, index=sorted(set(row["date"] for row in rows)))
        if not daily.empty:
            all_daily.loc[daily.index] = daily
        if len(records) < max(60, int(0.5*all_days)):
            continue

        eq = all_daily.cumsum()
        dd = eq - eq.cummax()
        results.append({
            "entry_minutes": cfg.entry_minutes, "stop_mult": cfg.stop_mult,
            "target_decay": cfg.target_decay, "hold_minutes": cfg.hold_minutes,
            "gap_max": cfg.gap_max, "first15_range_max": cfg.first15_range_max,
            "vrp_min": cfg.vrp_min, "trades": len(records),
            "coverage": len(records)/all_days,
            "mean_day_net": float(all_daily.mean()),
            "median_day_net": float(all_daily.median()),
            "p10_day_net": float(all_daily.quantile(0.10)),
            "positive_day_rate": float((all_daily>0).mean()),
            "max_drawdown": float(dd.min()),
            "profit_factor": float(sum(x for x in all_daily if x>0)/-sum(x for x in all_daily if x<0)) if (all_daily<0).any() else 999.0,
        })
        if cfg.gap_max is not None or cfg.first15_range_max is not None or cfg.vrp_min is not None:
            trades_store.extend(records)

    board = pd.DataFrame(results)
    if board.empty:
        return board, pd.DataFrame()

    board["target_reached"] = board["mean_day_net"] >= 1000
    board["stability_rank"] = (
        board["mean_day_net"].rank(ascending=False, method="min")
        + board["positive_day_rate"].rank(ascending=False, method="min")
        - board["max_drawdown"].abs().rank(ascending=False, method="min")
    )
    board = board.sort_values(
        ["target_reached","mean_day_net","positive_day_rate","max_drawdown"],
        ascending=[False,False,False,False],
    )
    return board, pd.DataFrame(trades_store)


def main(data: Path, out: Path):
    spot, opt = load(data)
    rows, all_days = build_days(spot, opt)

    base = [
        Config(e,s,t,h,None,None,None)
        for e in (15,30,45,60,75,90,105)
        for s in (1.4,1.6,1.8,2.0)
        for t in (0.25,0.35,0.45,0.55,0.65)
        for h in (60,90,120,180)
    ]
    board_base, _ = evaluate(rows, base, all_days)
    top_base = board_base.head(25) if not board_base.empty else pd.DataFrame()

    filtered = []
    for _, r in top_base.iterrows():
        for gap in (0.003,0.005,0.008):
            for r15 in (0.002,0.003,0.004,0.005):
                for vrp in (None,0.00,0.02,0.04,0.06):
                    filtered.append(Config(
                        int(r.entry_minutes), float(r.stop_mult), float(r.target_decay),
                        int(r.hold_minutes), gap, r15, vrp
                    ))

    board_filter, trades = evaluate(rows, filtered, all_days)
    out.mkdir(parents=True, exist_ok=True)
    board_base.head(100).to_csv(out/"straddle_grid_base.csv", index=False)
    board_filter.head(250).to_csv(out/"straddle_grid_filtered.csv", index=False)
    if not trades.empty:
        trades.to_csv(out/"straddle_grid_filtered_trades.csv", index=False)

    promoted = board_filter[board_filter.target_reached] if not board_filter.empty else pd.DataFrame()
    summary = {
        "dataset": str(data),
        "calendar_days": all_days,
        "entry_observations": len(rows),
        "base_variants_tested": len(base),
        "filtered_variants_tested": len(filtered),
        "target_daily_net_inr": 1000.0,
        "target_qualified_count": int(len(promoted)),
        "best_mean_day": float(board_filter.iloc[0].mean_day_net) if not board_filter.empty else None,
        "best_positive_day_rate": float(board_filter.iloc[0].positive_day_rate) if not board_filter.empty else None,
        "best_max_drawdown": float(board_filter.iloc[0].max_drawdown) if not board_filter.empty else None,
        "best": board_filter.iloc[0].to_dict() if not board_filter.empty else None,
    }
    (out/"straddle_grid_summary.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=Path("reports"))
    args = ap.parse_args()
    main(args.data, args.out)
