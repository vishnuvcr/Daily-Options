#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

ENTRY_OFFSETS = (-4, -3, -2)
TRIGGERS = ("WING_60", "RISK_60")
ADJUSTMENTS = ("RECENTER_BOTH", "ONE_STRIKE_INSIDE")
WING_POINTS = 200
STRIKE_INTERVAL = 50
MAX_ADJUSTMENTS = 2
ENTRY_CLOCK = "09:30:00"
EXIT_CLOCK = "15:00:00"
START_DATE = date(2021, 7, 1)
END_DATE = date(2026, 8, 4)
WEEKLY_TARGET = 5000.0
POSITIVE_WEEK_RATE_TARGET = 0.70
EXECUTION_COVERAGE_TARGET = 0.80

# Conservative fixed brokerage assumption for the frozen research comparison.
# The current public Paytm Money F&O FAQ lists ₹10 per unique executed order;
# ₹20/order is retained here as the conservative preregistered reference.
BROKERAGE_PER_ORDER = 20.0

@dataclass(frozen=True)
class Cell:
    entry_offset: int
    trigger: str
    adjustment: str

    @property
    def cell_id(self) -> str:
        return f"ID30_{abs(self.entry_offset):02d}_{self.trigger}_{self.adjustment}"

def cells():
    return [Cell(e, t, a) for e in ENTRY_OFFSETS for t in TRIGGERS for a in ADJUSTMENTS]

def lot_size(expiry):
    d = pd.Timestamp(expiry).date()
    if d < date(2024, 4, 26):
        return 50
    if d < date(2024, 11, 21):
        return 25
    if d < date(2026, 1, 6):
        return 75
    return 65

def round_strike(x):
    return int(math.floor(float(x) / STRIKE_INTERVAL + 0.5) * STRIKE_INTERVAL)

def expiry_files(root: Path):
    files = []
    for p in sorted((root / "options" / "NIFTY").glob("*.parquet")):
        try:
            d = pd.Timestamp(p.stem).date()
        except Exception:
            continue
        if START_DATE <= d <= END_DATE:
            files.append((d, p))
    if not files:
        raise FileNotFoundError("No exact-expiry NIFTY files in the requested research window")
    return files

def load_sessions(con, index_path: Path):
    sql = f"""
    SELECT DISTINCT CAST(trading_day AS DATE) AS trade_date
    FROM read_parquet('{str(index_path).replace("'", "''")}')
    WHERE CAST(trading_day AS DATE) BETWEEN DATE '2021-07-01' AND DATE '2026-08-04'
    ORDER BY trade_date
    """
    x = con.execute(sql).df()
    return [pd.Timestamp(v).date() for v in x["trade_date"].tolist()]

def session_offset(session_dates, expiry, offset):
    prior = [d for d in session_dates if d < expiry]
    if len(prior) < abs(offset):
        return None
    return prior[offset]

def load_spot(con, index_path, start_ts, end_ts):
    sql = f"""
    SELECT CAST(timestamp AS TIMESTAMP) AS ts,
           CAST(close AS DOUBLE) AS close_px
    FROM read_parquet('{str(index_path).replace("'", "''")}')
    -- Exact-expiry parquet already identifies the contract.
    -- Preserve the full timestamp range through expiry; do not filter by trading_day.
    WHERE CAST(timestamp AS TIMESTAMP) BETWEEN TIMESTAMP '{start_ts}' AND TIMESTAMP '{end_ts}'
    ORDER BY ts
    """
    x = con.execute(sql).df()
    if x.empty:
        return x
    x["ts"] = pd.to_datetime(x["ts"]).dt.floor("min")
    return x.drop_duplicates("ts").sort_values("ts")

def load_option_series(con, path, _trade_day, strike, side, start_ts, end_ts):
    sql = f"""
    SELECT CAST(timestamp AS TIMESTAMP) AS ts,
           CAST(open AS DOUBLE) AS open_px,
           CAST(close AS DOUBLE) AS close_px
    FROM read_parquet('{str(path).replace("'", "''")}')
    WHERE CAST(timestamp AS TIMESTAMP) BETWEEN TIMESTAMP '{start_ts}' AND TIMESTAMP '{end_ts}'
      AND CAST(strike AS DOUBLE) = {float(strike)}
      AND UPPER(CAST(option_type AS VARCHAR)) = '{side}'
      AND close > 0
    ORDER BY ts
    """
    x = con.execute(sql).df()
    if x.empty:
        return pd.DataFrame(columns=["ts", "open_px", "close_px"])
    x["ts"] = pd.to_datetime(x["ts"]).dt.floor("min")
    return x.drop_duplicates("ts").sort_values("ts")

def price_at(s, ts, field="open_px"):
    z = s[s.ts >= pd.Timestamp(ts)]
    if z.empty:
        return None
    v = z.iloc[0][field]
    return None if pd.isna(v) or v <= 0 else float(v)

def mark_at(s, ts, field="close_px"):
    z = s[s.ts <= pd.Timestamp(ts)]
    if z.empty:
        return None
    v = z.iloc[-1][field]
    return None if pd.isna(v) or v <= 0 else float(v)

def execution_cash(price, side, qty, lot, slippage):
    if side == "SELL":
        return (price - slippage) * qty * lot
    return -(price + slippage) * qty * lot

def order_cost(price, side, qty, lot, order_date):
    gross = price * qty * lot
    stt_rate = 0.001 if order_date < date(2026, 4, 1) else 0.0015
    exchange_rate = 0.0003503 if order_date < date(2026, 3, 1) else 0.000355299
    brokerage = BROKERAGE_PER_ORDER
    sebi = gross * 0.000001
    exchange = gross * exchange_rate
    stt = gross * stt_rate if side == "SELL" else 0.0
    stamp = gross * 0.00003 if side == "BUY" else 0.0
    gst = 0.18 * (brokerage + exchange + sebi)
    return brokerage + exchange + sebi + stt + stamp + gst

def apply_order(trade, leg, price, action, ts, slippage):
    side = {
        "OPEN_SHORT": "SELL",
        "CLOSE_SHORT": "BUY",
        "OPEN_LONG": "BUY",
        "CLOSE_LONG": "SELL",
    }[action]
    trade["cash"] += execution_cash(price, side, leg["qty"], leg["lot"], slippage)
    trade["costs"] += order_cost(price, side, leg["qty"], leg["lot"], pd.Timestamp(ts).date())

def current_equity(trade, legs, ts):
    equity = trade["cash"]
    for leg in legs:
        if not leg["active"]:
            continue
        mark = mark_at(leg["series"], ts, "close_px")
        if mark is None:
            return None
        sign = -1.0 if leg["position"] == "SHORT" else 1.0
        equity += sign * mark * leg["qty"] * leg["lot"]
    return equity

def max_loss_inr(legs):
    if not legs:
        return 0.0
    lot = legs[0]["lot"]
    strikes = sorted(float(l["strike"]) for l in legs)
    lo = min(strikes) - 500
    hi = max(strikes) + 500
    grid = np.arange(lo, hi + STRIKE_INTERVAL, STRIKE_INTERVAL, dtype=float)
    entry_cash = 0.0
    for leg in legs:
        sign_cash = 1.0 if leg["position"] == "SHORT" else -1.0
        entry_cash += sign_cash * leg["entry_price"] * leg["qty"] * lot
    worst = 0.0
    for spot in grid:
        value = entry_cash
        for leg in legs:
            intrinsic = max(spot - leg["strike"], 0.0) if leg["side"] == "CE" else max(leg["strike"] - spot, 0.0)
            sign = -1.0 if leg["position"] == "SHORT" else 1.0
            value += sign * intrinsic * leg["qty"] * lot
        worst = min(worst, value)
    return max(0.0, -worst)

def new_structure(con, expiry_path, data_day, exec_ts, end_ts, center, lot):
    specs = [
        ("CE", float(center), "SHORT", 1),
        ("PE", float(center), "SHORT", 1),
        ("CE", float(center + WING_POINTS), "LONG", 1),
        ("PE", float(center - WING_POINTS), "LONG", 1),
    ]
    legs = []
    for side, strike, position, qty in specs:
        series = load_option_series(con, expiry_path, data_day, strike, side, exec_ts, end_ts)
        px = price_at(series, exec_ts, "open_px")
        if px is None:
            return None
        legs.append({
            "side": side,
            "strike": strike,
            "position": position,
            "qty": qty,
            "lot": lot,
            "entry_price": px,
            "series": series,
            "active": True,
        })
    return legs

def close_leg(trade, leg, ts, slippage):
    px = price_at(leg["series"], ts, "open_px")
    if px is None:
        px = mark_at(leg["series"], ts, "close_px")
    if px is None:
        return False
    action = "CLOSE_SHORT" if leg["position"] == "SHORT" else "CLOSE_LONG"
    apply_order(trade, leg, px, action, ts, slippage)
    leg["active"] = False
    leg["exit_price"] = px
    return True

def open_active_structure(trade, legs, exec_ts, slippage):
    for leg in legs:
        action = "OPEN_LONG" if leg["position"] == "LONG" else "OPEN_SHORT"
        apply_order(trade, leg, leg["entry_price"], action, exec_ts, slippage)

def cycle_anchor(trade, legs):
    value = trade["cash"]
    for leg in legs:
        if leg["active"]:
            sign = -1.0 if leg["position"] == "SHORT" else 1.0
            value += sign * leg["entry_price"] * leg["qty"] * leg["lot"]
    return value

def build_setup(con, index_path, expiry_path, expiry, entry_date, entry_offset):
    signal_ts = pd.Timestamp(f"{entry_date} {ENTRY_CLOCK}")
    fill_ts = signal_ts + pd.Timedelta(minutes=1)
    spot = load_spot(con, index_path, f"{entry_date} 09:30:00", f"{expiry} 15:01:00")
    if spot.empty:
        return None
    spot_signal = mark_at(spot, signal_ts, "close_px")
    if spot_signal is None:
        return None
    lot = lot_size(expiry)
    center = round_strike(spot_signal) + STRIKE_INTERVAL
    end_ts = f"{expiry} 15:31:00"
    initial = new_structure(con, expiry_path, entry_date, fill_ts, end_ts, center, lot)
    if initial is None:
        return None
    return {
        "expiry": expiry,
        "entry_date": entry_date,
        "entry_offset": entry_offset,
        "lot": lot,
        "signal_ts": signal_ts,
        "fill_ts": fill_ts,
        "spot": spot,
        "expiry_path": expiry_path,
        "initial_center": center,
        "initial_legs": initial,
        "end_ts": end_ts,
    }

def build_mark_panel(spot, legs, start_ts, end_ts):
    start_ts = pd.Timestamp(start_ts)
    end_ts = pd.Timestamp(end_ts)
    base = spot[(spot.ts >= start_ts) & (spot.ts <= end_ts)][["ts", "close_px"]].copy()
    if base.empty:
        return pd.DataFrame()
    base = base.rename(columns={"close_px": "spot"}).sort_values("ts")
    for i, leg in enumerate(legs):
        if not leg["active"]:
            continue
        z = leg["series"][
            (leg["series"].ts >= start_ts) & (leg["series"].ts <= end_ts)
        ][["ts", "close_px"]].copy()
        if z.empty:
            return pd.DataFrame()
        z = z.rename(columns={"close_px": f"leg_{i}"}).sort_values("ts")
        base = pd.merge_asof(base, z, on="ts", direction="backward")
    active_names = [f"leg_{i}" for i, leg in enumerate(legs) if leg["active"]]
    if not active_names:
        return pd.DataFrame()
    return base.dropna(subset=["spot"] + active_names).sort_values("ts")


def first_trigger(panel, active, trigger, center_ref, cycle_start, cycle_max):
    if panel.empty:
        return None
    spot = panel["spot"].to_numpy(dtype=float)
    if trigger == "WING_60":
        delta = spot - float(center_ref)
        mask = (delta >= 120.0) | (delta <= -120.0)
    else:
        equity = np.full(len(panel), float(cycle_start), dtype=float)
        for i, leg in enumerate(active):
            if not leg["active"]:
                continue
            sign = -1.0 if leg["position"] == "SHORT" else 1.0
            equity = (
                equity
                + sign * panel[f"leg_{i}"].to_numpy(dtype=float)
                * float(leg["qty"]) * float(leg["lot"])
            )
        mask = equity <= float(cycle_start) - 0.60 * float(cycle_max)
    hits = np.flatnonzero(mask)
    if len(hits) == 0:
        return None
    j = int(hits[0])
    delta = float(spot[j] - float(center_ref))
    challenged = "CE" if delta >= 0 else "PE"
    return {
        "ts": pd.Timestamp(panel.iloc[j]["ts"]),
        "spot": float(spot[j]),
        "challenged": challenged,
    }



def clone_initial_legs(legs):
    """Create a fresh leg-state list for one parameter cell without copying market series."""
    cloned = []
    for leg in legs:
        item = dict(leg)
        item["series"] = leg["series"]
        item["active"] = True
        item.pop("exit_price", None)
        cloned.append(item)
    return cloned
def run_cell(con, setup, trigger, adjustment, slippage, initial_panel=None):
    trade = {"cash": 0.0, "costs": 0.0, "adjustments": 0}
    active = clone_initial_legs(setup["initial_legs"])
    open_active_structure(trade, active, setup["fill_ts"], slippage)
    center_ref = float(setup["initial_center"])
    cycle_start = cycle_anchor(trade, active)
    cycle_max = max_loss_inr(active)
    exit_signal = pd.Timestamp(f"{setup['expiry']} {EXIT_CLOCK}")
    start_ts = setup["fill_ts"]
    first_cycle = True

    while trade["adjustments"] <= MAX_ADJUSTMENTS:
        panel = initial_panel if first_cycle and initial_panel is not None else build_mark_panel(
            setup["spot"], active, start_ts, exit_signal
        )
        first_cycle = False
        hit = first_trigger(panel, active, trigger, center_ref, cycle_start, cycle_max)
        if hit is None or trade["adjustments"] >= MAX_ADJUSTMENTS:
            break

        exec_ts = hit["ts"] + pd.Timedelta(minutes=1)
        data_day = hit["ts"].date()
        challenged = hit["challenged"]
        if adjustment == "RECENTER_BOTH":
            for leg in active:
                if leg["active"] and not close_leg(trade, leg, exec_ts, slippage):
                    return None
            new_center = round_strike(hit["spot"])
            new_legs = new_structure(
                con,
                setup["expiry_path"],
                data_day,
                exec_ts,
                setup["end_ts"],
                new_center,
                setup["lot"],
            )
            if new_legs is None:
                return None
            open_active_structure(trade, new_legs, exec_ts, slippage)
            active = new_legs
            center_ref = float(new_center)
        else:
            target_idx = None
            target_strike = None
            for i, leg in enumerate(active):
                if leg["active"] and leg["position"] == "SHORT" and leg["side"] == challenged:
                    target_idx = i
                    # "One strike inside" = one strike deeper ITM:
                    # challenged CE -> lower strike; challenged PE -> higher strike.
                    target_strike = (
                        leg["strike"] - STRIKE_INTERVAL
                        if challenged == "CE"
                        else leg["strike"] + STRIKE_INTERVAL
                    )
                    break
            if target_idx is None:
                return None
            old_leg = active[target_idx]
            if not close_leg(trade, old_leg, exec_ts, slippage):
                return None
            series = load_option_series(
                con,
                setup["expiry_path"],
                data_day,
                target_strike,
                challenged,
                exec_ts,
                setup["end_ts"],
            )
            px = price_at(series, exec_ts, "open_px")
            if px is None:
                return None
            new_leg = {
                "side": challenged,
                "strike": float(target_strike),
                "position": "SHORT",
                "qty": 1,
                "lot": setup["lot"],
                "entry_price": px,
                "series": series,
                "active": True,
            }
            active[target_idx] = new_leg
            apply_order(trade, new_leg, px, "OPEN_SHORT", exec_ts, slippage)

        trade["adjustments"] += 1
        cycle_start = cycle_anchor(trade, active)
        cycle_max = max_loss_inr([x for x in active if x["active"]])
        start_ts = exec_ts

    exit_ts = exit_signal + pd.Timedelta(minutes=1)
    for leg in active:
        if leg["active"] and not close_leg(trade, leg, exit_ts, slippage):
            return None

    return {
        "expiry": str(setup["expiry"]),
        "entry_date": str(setup["entry_date"]),
        "entry_offset": setup["entry_offset"],
        "trigger": trigger,
        "adjustment": adjustment,
        "cell_id": f"ID30_{abs(setup['entry_offset']):02d}_{trigger}_{adjustment}",
        "lot": setup["lot"],
        "net_pnl": float(trade["cash"] - trade["costs"]),
        "adjustments": int(trade["adjustments"]),
        "brokerage_cost": float(trade["costs"]),
    }
def max_drawdown(values):
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        return 0.0
    cumulative = np.cumsum(arr)
    peaks = np.maximum.accumulate(np.r_[0.0, cumulative])
    return float(np.max(peaks[1:] - cumulative))


def profit_factor(values):
    arr = np.asarray(values, dtype=float)
    gains = float(arr[arr > 0].sum())
    losses = float(-arr[arr < 0].sum())
    if losses == 0.0:
        return float('inf') if gains > 0.0 else 0.0
    return gains / losses


def expected_shortfall(values, alpha=0.95):
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        return 0.0
    cutoff = float(np.quantile(arr, 1.0 - alpha))
    tail = arr[arr <= cutoff]
    return float(tail.mean()) if tail.size else cutoff


def run(data: Path, out: Path, slippage: float):
    out.mkdir(parents=True, exist_ok=True)
    index_path = data / "index" / "NIFTY.parquet"
    files = expiry_files(data)
    con = duckdb.connect()
    con.execute("SET TimeZone='Asia/Kolkata'")
    sessions = load_sessions(con, index_path)

    setups = 0
    rows = []
    total_expiries = len(files)

    for expiry, path in files:
        for offset in ENTRY_OFFSETS:
            entry_date = session_offset(sessions, expiry, offset)
            if entry_date is None:
                continue
            setup = build_setup(con, index_path, path, expiry, entry_date, offset)
            if setup is None:
                continue
            setups += 1
            initial_panel = build_mark_panel(
                setup["spot"], setup["initial_legs"], setup["fill_ts"], pd.Timestamp(f"{setup['expiry']} {EXIT_CLOCK}")
            )
            if initial_panel.empty:
                continue
            for trigger in TRIGGERS:
                for adjustment in ADJUSTMENTS:
                    result = run_cell(
                        con, setup, trigger, adjustment, slippage, initial_panel=initial_panel
                    )
                    if result is not None:
                        rows.append(result)

    con.close()
    trades = pd.DataFrame(rows)

    coverage = {
        "eligible_expiry_files": total_expiries,
        "executable_setup_count": setups,
        "observed_result_rows": int(len(trades)),
        "data_window_start": str(START_DATE),
        "data_window_end": str(END_DATE),
    }

    if trades.empty:
        summary = {
            "status": "NO_RESULTS",
            "slippage": slippage,
            "weekly_target": WEEKLY_TARGET,
            "positive_week_rate_target": POSITIVE_WEEK_RATE_TARGET,
            "execution_coverage_target": EXECUTION_COVERAGE_TARGET,
            "coverage": coverage,
        }
        (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        return summary

    trades.to_csv(out / "trades.csv", index=False)
    eligible = total_expiries
    board = trades.groupby(["cell_id", "entry_offset", "trigger", "adjustment"]).agg(
        executed_weeks=("net_pnl", "size"),
        mean_weekly_net=("net_pnl", "mean"),
        median_weekly_net=("net_pnl", "median"),
        positive_week_rate=("net_pnl", lambda x: float((x > 0).mean())),
        total_net=("net_pnl", "sum"),
        worst_week=("net_pnl", "min"),
    ).reset_index()
    metric_rows = []
    for keys, group in trades.groupby(["cell_id", "entry_offset", "trigger", "adjustment"], sort=False):
        values = group["net_pnl"].to_numpy(dtype=float)
        metric_rows.append({
            "cell_id": keys[0],
            "entry_offset": int(keys[1]),
            "trigger": keys[2],
            "adjustment": keys[3],
            "profit_factor": profit_factor(values),
            "weekly_max_drawdown": max_drawdown(values),
            "expected_shortfall_95": expected_shortfall(values, 0.95),
        })
    board = board.merge(
        pd.DataFrame(metric_rows),
        on=["cell_id", "entry_offset", "trigger", "adjustment"],
        how="left",
    )
    board["executed_week_coverage"] = board["executed_weeks"] / max(eligible, 1)
    board["target_pass_mean"] = board["mean_weekly_net"] >= WEEKLY_TARGET
    board["target_pass_median"] = board["median_weekly_net"] >= WEEKLY_TARGET
    board["target_pass_positive_rate"] = board["positive_week_rate"] >= POSITIVE_WEEK_RATE_TARGET
    board["target_pass_execution_coverage"] = board["executed_week_coverage"] >= EXECUTION_COVERAGE_TARGET
    board["preliminary_pass"] = board[[
        "target_pass_mean",
        "target_pass_median",
        "target_pass_positive_rate",
        "target_pass_execution_coverage",
    ]].all(axis=1)
    board.to_csv(out / "leaderboard.csv", index=False)

    trades["year"] = pd.to_datetime(trades["expiry"]).dt.year
    yearly = trades.groupby(["cell_id", "year"]).agg(
        weeks=("net_pnl", "size"),
        mean_weekly_net=("net_pnl", "mean"),
        median_weekly_net=("net_pnl", "median"),
        positive_week_rate=("net_pnl", lambda x: float((x > 0).mean())),
        total_net=("net_pnl", "sum"),
        worst_week=("net_pnl", "min"),
    ).reset_index()
    yearly.to_csv(out / "yearly.csv", index=False)

    weekly = trades.sort_values(["cell_id", "expiry"])[[
        "cell_id", "expiry", "entry_date", "entry_offset", "trigger", "adjustment", "lot", "net_pnl", "adjustments"
    ]]
    weekly.to_csv(out / "weekly.csv", index=False)

    best = board.sort_values(["mean_weekly_net", "median_weekly_net"], ascending=False).iloc[0].to_dict()
    summary = {
        "status": "COMPLETE",
        "slippage": slippage,
        "weekly_target": WEEKLY_TARGET,
        "positive_week_rate_target": POSITIVE_WEEK_RATE_TARGET,
        "execution_coverage_target": EXECUTION_COVERAGE_TARGET,
        "cell_count": 12,
        "reference_position_size": "1 NIFTY lot per leg in the frozen 1:1:1:1 four-leg structure",
        "brokerage_per_order_assumption": BROKERAGE_PER_ORDER,
        "eligible_expiry_files": eligible,
        "executable_setup_count": setups,
        "result_rows": int(len(trades)),
        "preliminary_pass_cells": int(board["preliminary_pass"].sum()),
        "best": best,
        "coverage": coverage,
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    return summary

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--slippage", type=float, required=True)
    args = ap.parse_args()
    print(json.dumps(run(args.data, args.out, args.slippage), indent=2, default=str))
