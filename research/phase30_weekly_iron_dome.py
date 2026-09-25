#!/usr/bin/env python3
"""Phase 30 deterministic weekly Iron Dome backtest."""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

START_DATE = date(2021, 7, 1)
END_DATE = date(2026, 8, 4)
WING = 200
STRIKE_STEP = 50
ENTRY_OFFSETS = (-4, -3, -2)
TRIGGERS = ("WING_60", "RISK_60")
ADJUSTMENTS = ("RECENTER_BOTH", "ONE_STRIKE_INSIDE")
BASE_SLIP = 0.20
STRESS_SLIP = 0.40


@dataclass
class Position:
    side: str
    strike: int
    option_type: str
    entry_ts: pd.Timestamp
    entry_price: float
    qty: int


@dataclass
class Order:
    ts: pd.Timestamp
    action: str
    option_type: str
    strike: int
    price: float
    qty: int
    expiry: date


def lot_size(expiry: date) -> int:
    if expiry < date(2021, 7, 1):
        return 50
    if expiry < date(2024, 4, 26):
        return 50
    if expiry < date(2024, 11, 21):
        return 25
    if expiry < date(2026, 1, 6):
        return 75
    return 65


def cell_id(entry_offset: int, trigger: str, adjustment: str) -> str:
    return f"E{abs(entry_offset):02d}_{trigger}_{adjustment}"


def expiry_files(root: Path):
    out = []
    for p in sorted((root / "options" / "NIFTY").glob("*.parquet")):
        try:
            d = pd.Timestamp(p.stem).date()
        except Exception:
            continue
        if START_DATE <= d <= END_DATE:
            out.append((d, p))
    return out


def trading_sessions(index_df: pd.DataFrame):
    dates = pd.to_datetime(index_df["trading_day"]).dt.date.drop_duplicates().sort_values().tolist()
    return dates


def prior_session_dates(sessions: list[date], expiry: date):
    prior = [d for d in sessions if d < expiry]
    if len(prior) < 4:
        return None
    return prior[-4], prior[-3], prior[-2]


def nearest_strike(spot: float) -> int:
    return int(round(float(spot) / STRIKE_STEP) * STRIKE_STEP)


def next_minute_open(series: pd.DataFrame, ts: pd.Timestamp):
    z = series[series["ts"] > ts].head(1)
    if z.empty:
        return None
    return float(z.iloc[0]["open"]), pd.Timestamp(z.iloc[0]["ts"])


def last_close_at_or_before(series: pd.DataFrame, ts: pd.Timestamp):
    z = series[series["ts"] <= ts].tail(1)
    if z.empty:
        return None
    return float(z.iloc[0]["close"]), pd.Timestamp(z.iloc[0]["ts"])


def option_series(options: pd.DataFrame, strike: int, option_type: str, start: pd.Timestamp, end: pd.Timestamp):
    z = options[
        (options["strike"] == float(strike))
        & (options["option_type"] == option_type)
        & (options["timestamp"] >= start)
        & (options["timestamp"] <= end)
        & options["open"].notna()
        & options["close"].notna()
        & (options["open"] > 0)
        & (options["close"] > 0)
    ][["timestamp", "open", "close"]].copy()
    if z.empty:
        return pd.DataFrame(columns=["ts", "open", "close"])
    z = z.rename(columns={"timestamp": "ts"}).sort_values("ts").drop_duplicates("ts")
    return z.reset_index(drop=True)


def get_spot_at(spot: pd.DataFrame, ts: pd.Timestamp):
    z = spot[spot["ts"] <= ts].tail(1)
    if z.empty:
        return None
    return float(z.iloc[0]["close"])


def execute_order(
    orders: list[Order],
    option_series_map: dict,
    action: str,
    strike: int,
    option_type: str,
    signal_ts: pd.Timestamp,
    lot: int,
    slippage: float,
    expiry: date,
):
    key = (int(strike), option_type)
    s = option_series_map.get(key)
    if s is None or s.empty:
        return None
    fill = next_minute_open(s, signal_ts)
    if fill is None:
        return None
    raw, fill_ts = fill
    px = raw + slippage if action == "BUY" else raw - slippage
    if px <= 0 or not np.isfinite(px):
        return None
    qty = lot
    orders.append(Order(fill_ts, action, option_type, int(strike), float(px), qty, expiry))
    return Position(
        side="LONG" if action == "BUY" else "SHORT",
        strike=int(strike),
        option_type=option_type,
        entry_ts=fill_ts,
        entry_price=float(px),
        qty=qty,
    )


def close_position(orders, option_series_map, pos: Position, signal_ts, lot, slippage, expiry):
    action = "SELL" if pos.side == "LONG" else "BUY"
    return execute_order(orders, option_series_map, action, pos.strike, pos.option_type, signal_ts, lot, slippage, expiry)


def mark_value(pos: Position, current_price: float) -> float:
    if pos.side == "LONG":
        return current_price * pos.qty
    return -current_price * pos.qty


def position_pnl(pos: Position, current_price: float) -> float:
    if pos.side == "LONG":
        return (current_price - pos.entry_price) * pos.qty
    return (pos.entry_price - current_price) * pos.qty


def portfolio_current_pnl(positions: list[Position], series_map, ts: pd.Timestamp) -> float | None:
    total = 0.0
    for p in positions:
        s = series_map.get((p.strike, p.option_type))
        if s is None:
            return None
        mark = last_close_at_or_before(s, ts)
        if mark is None:
            return None
        total += position_pnl(p, mark[0])
    return total


def max_loss_budget(positions: list[Position], expiry: date) -> float:
    # Conservative intrinsic-only worst-case loss of the currently open
    # position, measured from its own entry cashflows. This keeps the RISK_60
    # trigger dimensionally consistent and resets naturally after adjustment.
    strikes = sorted({p.strike for p in positions})
    test_spots = [0.0] + [float(x) for x in strikes] + [float(x + 1) for x in strikes]
    base_cash = sum(
        (p.entry_price * p.qty) if p.side == "SHORT" else (-p.entry_price * p.qty)
        for p in positions
    )
    worst = 0.0
    for spot in test_spots:
        future = base_cash
        for p in positions:
            intrinsic = max(0.0, spot - p.strike) if p.option_type == "CE" else max(0.0, p.strike - spot)
            future += intrinsic * p.qty if p.side == "LONG" else -intrinsic * p.qty
        worst = min(worst, future)
    return max(1.0, -worst)


def turnover_and_costs(orders: list[Order], expiry: date):
    if not orders:
        return 0.0, 0.0
    gross_turnover = sum(o.price * o.qty for o in orders)
    sell_turnover = sum(o.price * o.qty for o in orders if o.action == "SELL")
    buy_turnover = sum(o.price * o.qty for o in orders if o.action == "BUY")
    brokerage = 20.0 * len(orders)
    exchange = 0.0
    sebi = gross_turnover * 0.000001
    stamp = 0.0
    stt = 0.0
    for o in orders:
        if o.ts.date() >= date(2026, 3, 1):
            exchange += o.price * o.qty * 0.000355299
        else:
            exchange += o.price * o.qty * 0.0003503
        if o.action == "SELL":
            stt_rate = 0.0015 if o.ts.date() >= date(2026, 4, 1) else 0.001
            stt += o.price * o.qty * stt_rate
        else:
            stamp += o.price * o.qty * 0.00003
    gst = 0.18 * (brokerage + exchange + sebi)
    return brokerage + exchange + sebi + stt + stamp + gst, sell_turnover + buy_turnover


def order_cashflow(orders: list[Order]) -> float:
    # Positive cash = premium received on sale; negative = premium paid on buy.
    return sum(o.price * o.qty if o.action == "SELL" else -o.price * o.qty for o in orders)


def simulate(options: pd.DataFrame, spot: pd.DataFrame, expiry: date, entry_date: date, entry_offset: int, trigger: str, adjustment: str, slippage: float):
    entry_signal = pd.Timestamp(f"{entry_date} 09:30:00")
    expiry_exit = pd.Timestamp(f"{expiry} 15:00:00")
    spot_entry = get_spot_at(spot, pd.Timestamp(f"{entry_date} 09:29:00"))
    if spot_entry is None:
        return None
    center = nearest_strike(spot_entry) + STRIKE_STEP
    option_map = {}
    for side, strike in [("CE", center), ("PE", center), ("CE", center + WING), ("PE", center - WING)]:
        option_map[(strike, side)] = option_series(options, strike, side, pd.Timestamp(f"{entry_date} 09:29:00"), expiry_exit)
    if any(x.empty for x in option_map.values()):
        return None

    lot = lot_size(expiry)
    orders: list[Order] = []
    positions: list[Position] = []

    # Entry: sell CE, sell PE, buy wings.
    for action, side, strike in [
        ("SELL", "CE", center),
        ("SELL", "PE", center),
        ("BUY", "CE", center + WING),
        ("BUY", "PE", center - WING),
    ]:
        p = execute_order(orders, option_map, action, strike, side, entry_signal, lot, slippage, expiry)
        if p is None:
            return None
        positions.append(p)

    trigger_count = 0
    realized_cash = 0.0

    all_timestamps = spot[
        (spot["ts"] >= pd.Timestamp(f"{entry_date} 09:30:00"))
        & (spot["ts"] < expiry_exit)
    ][["ts", "close"]].drop_duplicates("ts").sort_values("ts")

    while trigger_count < 2 and not all_timestamps.empty:
        triggered = None
        budget = max_loss_budget(positions, expiry)
        for row in all_timestamps.itertuples(index=False):
            ts = pd.Timestamp(row.ts)
            if ts <= entry_signal:
                continue
            s = float(row.close)
            current_center = int(round(np.mean([p.strike for p in positions if p.option_type == "CE" or p.option_type == "PE"])))
            up = s >= current_center + 120
            down = s <= current_center - 120
            if trigger == "WING_60":
                fire = up or down
            else:
                mkt = portfolio_current_pnl(positions, option_map, ts)
                if mkt is None:
                    continue
                fire = mkt <= -(0.60 * budget)
            if fire:
                direction = "UP" if up and not down else "DOWN" if down and not up else ("UP" if s >= current_center else "DOWN")
                triggered = (ts, s, direction)
                break

        if triggered is None:
            break

        trigger_ts, trigger_spot, direction = triggered
        # Remove the timestamp window before the trigger for the next search.
        all_timestamps = all_timestamps[all_timestamps["ts"] > trigger_ts].reset_index(drop=True)

        # Refresh option_map for any strikes that may be introduced by the adjustment.
        def ensure_series(strike, side):
            key = (int(strike), side)
            if key not in option_map:
                option_map[key] = option_series(options, int(strike), side, trigger_ts, expiry_exit)
            return option_map[key]

        old_positions = list(positions)
        new_positions = []

        if adjustment == "RECENTER_BOTH":
            for p in old_positions:
                q = close_position(orders, option_map, p, trigger_ts, lot, slippage, expiry)
                if q is None:
                    return None
            # New center uses the trigger-time spot, before the next-minute fills.
            new_center = nearest_strike(trigger_spot)
            for action, side, strike in [
                ("SELL", "CE", new_center),
                ("SELL", "PE", new_center),
                ("BUY", "CE", new_center + WING),
                ("BUY", "PE", new_center - WING),
            ]:
                ensure_series(strike, side)
                p = execute_order(orders, option_map, action, strike, side, trigger_ts, lot, slippage, expiry)
                if p is None:
                    return None
                new_positions.append(p)
        else:
            for p in old_positions:
                move_this = (direction == "UP" and p.option_type == "CE") or (direction == "DOWN" and p.option_type == "PE")
                if move_this and p.side in {"SHORT", "LONG"}:
                    q = close_position(orders, option_map, p, trigger_ts, lot, slippage, expiry)
                    if q is None:
                        return None
            new_positions = []
            for p in old_positions:
                move_this = (direction == "UP" and p.option_type == "CE") or (direction == "DOWN" and p.option_type == "PE")
                if not move_this:
                    new_positions.append(p)
            if direction == "UP":
                old_short = min([p.strike for p in old_positions if p.option_type == "CE"])
                new_short = old_short + STRIKE_STEP
                new_wing = new_short + WING
                ensure_series(new_short, "CE")
                ensure_series(new_wing, "CE")
                ps = execute_order(orders, option_map, "SELL", new_short, "CE", trigger_ts, lot, slippage, expiry)
                pl = execute_order(orders, option_map, "BUY", new_wing, "CE", trigger_ts, lot, slippage, expiry)
            else:
                old_short = max([p.strike for p in old_positions if p.option_type == "PE"])
                new_short = old_short - STRIKE_STEP
                new_wing = new_short - WING
                ensure_series(new_short, "PE")
                ensure_series(new_wing, "PE")
                ps = execute_order(orders, option_map, "SELL", new_short, "PE", trigger_ts, lot, slippage, expiry)
                pl = execute_order(orders, option_map, "BUY", new_wing, "PE", trigger_ts, lot, slippage, expiry)
            if ps is None or pl is None:
                return None
            new_positions.extend([ps, pl])

        positions = new_positions
        trigger_count += 1
        # Reset option_map is not necessary; existing series remain available.

    # Exit at 15:00 signal, fill at next minute if available.
    for p in list(positions):
        q = close_position(orders, option_map, p, expiry_exit, lot, slippage, expiry)
        if q is None:
            return None
    raw = order_cashflow(orders)
    costs, turnover = turnover_and_costs(orders, expiry)
    net = raw - costs
    return {
        "cell_id": cell_id(entry_offset, trigger, adjustment),
        "entry_date": entry_date.isoformat(),
        "expiry": expiry.isoformat(),
        "entry_offset": entry_offset,
        "trigger": trigger,
        "adjustment": adjustment,
        "lot": lot,
        "adjustments": trigger_count,
        "orders": len(orders),
        "gross_cashflow": raw,
        "costs": costs,
        "net_pnl": net,
        "turnover": turnover,
    }


def metrics(trades: pd.DataFrame, slippage: float):
    out = {"slippage": slippage, "trades": int(len(trades))}
    if trades.empty:
        out.update({
            "traded_weeks": 0,
            "mean_weekly_net": None,
            "median_weekly_net": None,
            "profitable_week_rate": None,
            "weeks_ge_5000_rate": None,
            "worst_week": None,
            "max_drawdown": None,
            "profit_factor": None,
            "cvar95": None,
            "target_qualified": False,
        })
        return out
    x = trades.sort_values(["expiry", "entry_date"]).copy()
    weekly = x.groupby(["cell_id", "expiry"], as_index=False)["net_pnl"].sum()
    vals = weekly["net_pnl"].astype(float)
    positive = vals[vals > 0].sum()
    negative = -vals[vals < 0].sum()
    cumulative = vals.cumsum()
    dd = cumulative - cumulative.cummax()
    out.update({
        "traded_weeks": int(len(vals)),
        "mean_weekly_net": float(vals.mean()),
        "median_weekly_net": float(vals.median()),
        "profitable_week_rate": float((vals > 0).mean()),
        "weeks_ge_5000_rate": float((vals >= 5000).mean()),
        "worst_week": float(vals.min()),
        "max_drawdown": float(dd.min()),
        "profit_factor": float(positive / negative) if negative > 0 else None,
        "cvar95": float(vals.nsmallest(max(1, int(np.ceil(len(vals) * 0.05))).sum() / max(1, int(np.ceil(len(vals) * 0.05)))),
        "target_qualified": bool(
            len(vals) >= 100
            and vals.mean() >= 5000
            and vals.median() >= 5000
            and (vals >= 5000).mean() >= 0.75
        ),
    })
    return out


def run(data_root: Path, out: Path, slippage: float):
    out.mkdir(parents=True, exist_ok=True)
    root = Path(data_root)
    idx = root / "index" / "NIFTY.parquet"
    if not idx.exists():
        raise FileNotFoundError(idx)

    con = duckdb.connect()
    con.execute("SET TimeZone='Asia/Kolkata'")
    spot = con.execute(
        f"""
        SELECT CAST(timestamp AS TIMESTAMP) ts,
               CAST(trading_day AS DATE) trading_day,
               CAST(close AS DOUBLE) close
        FROM read_parquet('{idx}')
        WHERE CAST(trading_day AS DATE) BETWEEN DATE '{START_DATE}' AND DATE '{END_DATE}'
          AND close > 0
        ORDER BY ts
        """
    ).df()
    con.close()
    spot["ts"] = pd.to_datetime(spot["ts"])
    sessions = trading_sessions(spot)
    files = expiry_files(root)

    rows = []
    coverage = []
    for expiry, path in files:
        offsets = prior_session_dates(sessions, expiry)
        if offsets is None:
            continue
        for offset, entry_date in zip(ENTRY_OFFSETS, offsets):
            if entry_date < START_DATE or entry_date > END_DATE:
                continue
            con = duckdb.connect()
            con.execute("SET TimeZone='Asia/Kolkata'")
            options = con.execute(
                f"""
                SELECT CAST(timestamp AS TIMESTAMP) timestamp,
                       CAST(trading_day AS DATE) trading_day,
                       CAST(strike AS DOUBLE) strike,
                       UPPER(CAST(option_type AS VARCHAR)) option_type,
                       CAST(open AS DOUBLE) open,
                       CAST(close AS DOUBLE) close
                FROM read_parquet('{path}')
                WHERE CAST(trading_day AS DATE) BETWEEN DATE '{entry_date}' AND DATE '{expiry}'
                  AND close > 0
                ORDER BY timestamp, strike, option_type
                """
            ).df()
            con.close()
            if options.empty:
                coverage.append({"expiry": str(expiry), "entry_date": str(entry_date), "status": "NO_OPTION_ROWS"})
                continue
            spot_window = spot[
                (spot["ts"] >= pd.Timestamp(f"{entry_date} 09:25:00"))
                & (spot["ts"] <= pd.Timestamp(f"{expiry} 15:05:00"))
            ][["ts","close"]].copy()
            for trigger in TRIGGERS:
                for adjustment in ADJUSTMENTS:
                    try:
                        r = simulate(options, spot_window, expiry, entry_date, offset, trigger, adjustment, slippage)
                        if r is None:
                            coverage.append({"expiry": str(expiry), "entry_date": str(entry_date), "cell_id": cell_id(offset, trigger, adjustment), "status": "NO_EXECUTION"})
                        else:
                            rows.append(r)
                            coverage.append({"expiry": str(expiry), "entry_date": str(entry_date), "cell_id": r["cell_id"], "status": "OK", "adjustments": r["adjustments"]})
                    except Exception as exc:
                        coverage.append({"expiry": str(expiry), "entry_date": str(entry_date), "cell_id": cell_id(offset, trigger, adjustment), "status": "ERROR", "error": repr(exc)})

    trades = pd.DataFrame(rows)
    if not trades.empty:
        trades.to_csv(out / "phase30_trades.csv", index=False)
    (out / "phase30_coverage.json").write_text(json.dumps(coverage, indent=2), encoding="utf-8")
    summary = {
        "phase": "30",
        "slippage": slippage,
        "trade_rows": int(len(trades)),
        "cells": [cell_id(e,t,a) for e in ENTRY_OFFSETS for t in TRIGGERS for a in ADJUSTMENTS],
        "metrics": [],
    }
    if not trades.empty:
        for cid, g in trades.groupby("cell_id"):
            m = metrics(g, slippage)
            m["cell_id"] = cid
            summary["metrics"].append(m)
        summary["metrics"] = sorted(summary["metrics"], key=lambda x: x["mean_weekly_net"] if x["mean_weekly_net"] is not None else -1e18, reverse=True)
    (out / "phase30_summary.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--slippage", type=float, default=BASE_SLIP)
    args = ap.parse_args()
    print(json.dumps(run(args.data, args.out, args.slippage), indent=2))


if __name__ == "__main__":
    main()
