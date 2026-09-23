from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from research.cost_model import OptionCostModel
from research.contracts import nifty_lot_size

LOT = 65
RISK_FREE = 0.06
ANNUAL_MINUTES = 252 * 375


def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def bs_call(s: float, k: float, t: float, r: float, sigma: float) -> float:
    if t <= 0:
        return max(s - k, 0.0)
    if sigma <= 0:
        return max(s - k * math.exp(-r * t), 0.0)
    d1 = (math.log(s / k) + (r + 0.5 * sigma * sigma) * t) / (sigma * math.sqrt(t))
    d2 = d1 - sigma * math.sqrt(t)
    return s * norm_cdf(d1) - k * math.exp(-r * t) * norm_cdf(d2)


def bs_put(s: float, k: float, t: float, r: float, sigma: float) -> float:
    return bs_call(s, k, t, r, sigma) - s + k * math.exp(-r * t)


def implied_straddle_vol(s: float, k: float, t: float, straddle: float) -> float:
    intrinsic = max(s - k, 0.0) + max(k - s, 0.0)
    if not np.isfinite(straddle) or straddle <= intrinsic or s <= 0 or k <= 0:
        return np.nan
    lo, hi = 1e-4, 5.0
    for _ in range(80):
        mid = (lo + hi) / 2
        model = bs_call(s, k, t, RISK_FREE, mid) + bs_put(s, k, t, RISK_FREE, mid)
        if model > straddle:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def load(path: Path):
    spot = pd.read_excel(path, sheet_name="Spot_1min")
    opt = pd.read_excel(path, sheet_name="ATM_Options_1min")

    spot["timestamp"] = pd.to_datetime(
        spot["Date"].astype(str) + " " + spot["Time"].astype(str)
    )
    opt["timestamp"] = (
        pd.to_datetime(opt["Timestamp"], utc=True)
        .dt.tz_convert("Asia/Kolkata")
        .dt.tz_localize(None)
    )

    spot = spot.rename(
        columns={"Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"}
    )
    opt = opt.rename(
        columns={
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
            "Type": "option_type",
            "Strike": "strike",
            "Expiry": "expiry",
        }
    )
    opt["option_type"] = opt["option_type"].astype(str).str.upper().replace({"CALL": "CE", "PUT": "PE"})
    opt["expiry"] = pd.to_datetime(opt["expiry"], errors="coerce")

    for col in ["open", "high", "low", "close", "volume", "strike"]:
        opt[col] = pd.to_numeric(opt[col], errors="coerce")

    return (
        spot.dropna(subset=["timestamp", "close"]).sort_values("timestamp"),
        opt.dropna(subset=["timestamp", "close", "strike", "expiry"]).sort_values("timestamp"),
    )


def vrp_at_entry(ds: pd.DataFrame, do: pd.DataFrame, entry_time: pd.Timestamp):
    srow = ds[ds.timestamp <= entry_time].tail(1)
    if srow.empty:
        return None

    s = float(srow.iloc[0].close)
    history = ds[(ds.timestamp < entry_time) & (ds.timestamp >= entry_time - pd.Timedelta(minutes=30))].close
    if len(history) < 15:
        return None

    rv = float(history.pct_change().dropna().std() * math.sqrt(ANNUAL_MINUTES))
    q = do[(do.timestamp >= entry_time) & (do.timestamp <= entry_time + pd.Timedelta(minutes=5)) & (do.close > 0)].copy()
    if q.empty:
        return None

    strike = float(q.strike.iloc[(q.strike - s).abs().argmin()])
    ce = q[(q.option_type == "CE") & (q.strike == strike)].sort_values("timestamp")
    pe = q[(q.option_type == "PE") & (q.strike == strike)].sort_values("timestamp")
    if ce.empty or pe.empty:
        return None

    common = sorted(set(ce.timestamp) & set(pe.timestamp))
    if not common:
        return None

    t = common[0]
    ce_px = float(ce.loc[ce.timestamp == t, "close"].iloc[0])
    pe_px = float(pe.loc[pe.timestamp == t, "close"].iloc[0])
    expiry = pd.Timestamp(ce.iloc[0].expiry)
    years = max((expiry - t) / pd.Timedelta(days=365.25), 1 / 3650)
    iv = implied_straddle_vol(s, strike, float(years), ce_px + pe_px)
    if not np.isfinite(iv):
        return None

    return {"vrp": iv - rv, "iv": iv, "rv": rv, "strike": strike}


def simulate(path: pd.DataFrame, entry: float, stop_mult: float, target_decay: float, hold: int):
    stop = entry * stop_mult
    target = entry * (1.0 - target_decay)
    exit_px = None
    exit_time = None
    reason = "time"

    for ts, row in path.sort_values("timestamp").set_index("timestamp").iterrows():
        hi = float(row.high)
        lo = float(row.low)
        close = float(row.close)

        if hi >= stop:
            exit_px, exit_time, reason = stop, ts, "stop"
            break
        if lo <= target:
            exit_px, exit_time, reason = target, ts, "target"
            break

        exit_px, exit_time = close, ts

    return exit_time, exit_px, reason


def main(data: Path, out: Path):
    spot, opt = load(data)
    out.mkdir(parents=True, exist_ok=True)
    cm = OptionCostModel()

    spot_days = {d: ds for d, ds in spot.groupby(spot.timestamp.dt.date)}
    opt_days = {d: do for d, do in opt.groupby(opt.timestamp.dt.date)}

    rows = []
    best_trade_frames = []

    for vrp_threshold in (0.00, 0.02, 0.04, 0.06, 0.08):
        trades = []

        for d, ds in spot_days.items():
            do = opt_days.get(d)
            if do is None:
                continue

            entry_time = pd.Timestamp(d) + pd.Timedelta(hours=9, minutes=30)
            regime = vrp_at_entry(ds, do, entry_time)
            if regime is None or regime["vrp"] < vrp_threshold:
                continue

            strike = regime["strike"]
            q = do[
                (do.timestamp >= entry_time)
                & (do.timestamp <= entry_time + pd.Timedelta(minutes=5))
                & (do.strike == strike)
                & (do.close > 0)
            ].copy()

            ce = q[q.option_type == "CE"].sort_values("timestamp")
            pe = q[q.option_type == "PE"].sort_values("timestamp")
            common = sorted(set(ce.timestamp) & set(pe.timestamp))
            if not common:
                continue

            et = common[0]
            call_entry = float(ce.loc[ce.timestamp == et, "close"].iloc[0])
            put_entry = float(pe.loc[pe.timestamp == et, "close"].iloc[0])
            entry = call_entry + put_entry
            path = do[
                (do.timestamp > et)
                & (do.timestamp <= et + pd.Timedelta(minutes=180))
                & (do.strike == strike)
            ]
            pivot = path.pivot_table(index="timestamp", columns="option_type", values=["high", "low", "close"], aggfunc="last")
            if pivot.empty or not {"CE", "PE"}.issubset(set(pivot["close"].columns)):
                continue

            pivot = pivot.dropna(subset=[("close", "CE"), ("close", "PE")])
            if pivot.empty:
                continue

            spread_path = pd.DataFrame(
                {
                    "timestamp": pivot.index,
                    "high": pivot[("high", "CE")].to_numpy() + pivot[("high", "PE")].to_numpy(),
                    "low": pivot[("low", "CE")].to_numpy() + pivot[("low", "PE")].to_numpy(),
                    "close": pivot[("close", "CE")].to_numpy() + pivot[("close", "PE")].to_numpy(),
                }
            )
            xt, exit_straddle, reason = simulate(
                spread_path,
                entry,
                stop_mult=2.0,
                target_decay=0.50,
                hold=180,
            )
            if xt is None:
                continue

            exit_row = pivot.loc[xt]
            call_exit = float(exit_row[("close", "CE")])
            put_exit = float(exit_row[("close", "PE")])
            net = cm.short_straddle_net_pnl(
                call_entry,
                put_entry,
                call_exit,
                put_exit,
                LOT,
            )
            trades.append(
                {
                    "date": str(d),
                    "entry_time": et.isoformat(),
                    "exit_time": xt.isoformat(),
                    "strike": strike,
                    "vrp": float(regime["vrp"]),
                    "iv": float(regime["iv"]),
                    "rv": float(regime["rv"]),
                    "entry_straddle": entry,
                    "exit_straddle": float(exit_straddle),
                    "net_pnl": float(net),
                    "reason": reason,
                }
            )

        if trades:
            frame = pd.DataFrame(trades)
            best_trade_frames.append(frame)
            daily = frame.groupby("date").net_pnl.sum()
            wins = frame.loc[frame.net_pnl > 0, "net_pnl"].sum()
            losses = -frame.loc[frame.net_pnl < 0, "net_pnl"].sum()
            rows.append(
                {
                    "vrp_threshold": vrp_threshold,
                    "trades": len(frame),
                    "win_rate": float((frame.net_pnl > 0).mean()),
                    "mean_active_day": float(daily.mean()),
                    "mean_all_day": float(frame.net_pnl.sum() / len(spot_days)),
                    "profit_factor": float(wins / losses) if losses else 999.0,
                    "total_net": float(frame.net_pnl.sum()),
                }
            )

    leaderboard = pd.DataFrame(rows)
    if not leaderboard.empty:
        leaderboard = leaderboard.sort_values("mean_all_day", ascending=False)
        pd.concat(best_trade_frames, ignore_index=True).to_csv(out / "short_straddle_vrp_trades.csv", index=False)

    leaderboard.to_csv(out / "short_straddle_vrp_leaderboard.csv", index=False)

    result = {
        "dataset": str(data),
        "trading_days": len(spot_days),
        "variants_tested": 5,
        "lot_size": LOT,
        "target_inr_per_day": 1000.0,
        "top": leaderboard.iloc[0].to_dict() if len(leaderboard) else None,
        "gate": "PASS_PRELIMINARY" if len(leaderboard) and leaderboard.iloc[0].mean_all_day >= 1000 else "FAIL_PRELIMINARY",
    }
    (out / "short_straddle_vrp_summary.json").write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("reports"))
    args = parser.parse_args()
    main(args.data, args.out)
