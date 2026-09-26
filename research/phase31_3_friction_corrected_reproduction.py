#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

import duckdb
import pandas as pd

ENTRY = "09:30:00"
EXIT = "15:10:00"
START_DATE = date(2021, 7, 1)
END_DATE = date(2026, 8, 31)
WEEKLY_TARGET = 5000.0


def lot_size(expiry):
    d = pd.Timestamp(expiry).date()
    if d < date(2024, 4, 26):
        return 50
    if d < date(2024, 11, 21):
        return 25
    if d < date(2026, 1, 6):
        return 75
    return 65


def nearest_strike(px):
    return int(round(float(px) / 50.0) * 50)


def load_index(con, path):
    q = f"""SELECT CAST(timestamp AS TIMESTAMP) ts, CAST(open AS DOUBLE) open_px
            FROM read_parquet('{str(path).replace("'", "''")}')
            WHERE CAST(timestamp AS TIMESTAMP) BETWEEN TIMESTAMP '{START_DATE} 09:30:00'
              AND TIMESTAMP '{END_DATE} 15:10:00'
            ORDER BY ts"""
    x = con.execute(q).df()
    x["ts"] = pd.to_datetime(x["ts"]).dt.floor("min")
    return x.drop_duplicates("ts").sort_values("ts")


def option_price(con, path, strike, side, ts, field):
    q = f"""SELECT CAST({field} AS DOUBLE) px
            FROM read_parquet('{str(path).replace("'", "''")}')
            WHERE CAST(timestamp AS TIMESTAMP) = TIMESTAMP '{ts}'
              AND CAST(strike AS DOUBLE) = {float(strike)}
              AND UPPER(CAST(option_type AS VARCHAR)) = '{side}'
              AND {field} > 0
            LIMIT 1"""
    x = con.execute(q).df()
    if x.empty or pd.isna(x.iloc[0].px):
        return None
    return float(x.iloc[0].px)


def costs(price, side, qty, lot, d):
    gross = float(price) * qty * lot
    stt = gross * (0.001 if d < date(2026, 4, 1) else 0.0015) if side == "SELL" else 0.0
    exchange = gross * (0.0003503 if d < date(2026, 3, 1) else 0.000355299)
    sebi = gross * 0.000001
    stamp = gross * 0.00003 if side == "BUY" else 0.0
    brokerage = 20.0
    gst = 0.18 * (brokerage + exchange + sebi)
    return brokerage + exchange + sebi + stt + stamp + gst


def trade_for_day(con,index,expiry_path,expiry,day,slippage):
    et=f"{day} {ENTRY}"; xt=f"{day} {EXIT}"
    r=index[index.ts==pd.Timestamp(et)]
    if r.empty: return None
    spot=float(r.iloc[0].open_px); atm=nearest_strike(spot); lot=lot_size(expiry)
    specs=[("CE",atm+200,"BUY",2),("PE",atm-200,"BUY",2),("PE",atm-400,"SELL",1)]
    legs=[]; raw_gross=0.0; execution_gross=0.0; transaction_costs=0.0; slippage_cost=0.0
    for side,strike,action,qty in specs:
        ep=option_price(con,expiry_path,strike,side,et,"open"); xp=option_price(con,expiry_path,strike,side,xt,"open")
        if ep is None or xp is None: return None
        if action=="BUY":
            exec_entry=ep+slippage
            exec_exit=max(0.0,xp-slippage)
            raw_pnl=(xp-ep)*qty*lot
            exec_pnl=(exec_exit-exec_entry)*qty*lot
            exit_side="SELL"
        else:
            exec_entry=max(0.0,ep-slippage)
            exec_exit=xp+slippage
            raw_pnl=(ep-xp)*qty*lot
            exec_pnl=(exec_entry-exec_exit)*qty*lot
            exit_side="BUY"
        tc=costs(exec_entry,action,qty,lot,pd.Timestamp(day).date())
        tc+=costs(exec_exit,exit_side,qty,lot,pd.Timestamp(day).date())
        sc=raw_pnl-exec_pnl
        raw_gross+=raw_pnl; execution_gross+=exec_pnl; transaction_costs+=tc; slippage_cost+=sc
        legs.append({"side":side,"strike":strike,"action":action,"qty_lots":qty,"quantity":qty*lot,
                     "entry_price_raw":ep,"exit_price_raw":xp,"entry_price_exec":exec_entry,
                     "exit_price_exec":exec_exit,"raw_pnl":raw_pnl,"execution_pnl":exec_pnl,
                     "slippage_cost":sc,"transaction_costs":tc})
    return {"trade_date":str(day),"expiry":str(expiry),"spot_0930":spot,"atm":atm,"lot_size":lot,
            "entry_time":et,"exit_time":xt,"gross_pnl_raw":raw_gross,
            "slippage_cost":slippage_cost,"transaction_costs":transaction_costs,
            "total_costs":slippage_cost+transaction_costs,"gross_pnl":execution_gross,
            "net_pnl":execution_gross-transaction_costs,"legs":json.dumps(legs,separators=(",",":"))}

def run(data: Path, out: Path, slippage: float):
    out.mkdir(parents=True, exist_ok=True)
    index_path = data / "index" / "NIFTY.parquet"
    expiry_files = {}
    for p in sorted((data / "options" / "NIFTY").glob("*.parquet")):
        try:
            d = pd.Timestamp(p.stem).date()
        except Exception:
            continue
        if START_DATE <= d <= END_DATE:
            expiry_files[d] = p
    if not expiry_files:
        raise RuntimeError("No exact-expiry NIFTY option files found")

    con = duckdb.connect()
    con.execute("SET TimeZone='Asia/Kolkata'")
    index = load_index(con, index_path)
    sessions = sorted(set(index.ts.dt.date))
    expiries = sorted(expiry_files)
    rows = []
    missing = []

    for day in sessions:
        if day < START_DATE or day > END_DATE:
            continue
        future = [e for e in expiries if e >= day]
        if not future:
            continue
        expiry = future[0]
        result = trade_for_day(con, index, expiry_files[expiry], expiry, day, slippage)
        if result is None:
            missing.append({"trade_date": str(day), "expiry": str(expiry)})
        else:
            rows.append(result)

    con.close()
    trades = pd.DataFrame(rows)
    if trades.empty:
        raise RuntimeError("No executable trades produced")

    trades["trade_date"] = pd.to_datetime(trades["trade_date"]).dt.date
    trades["week"] = pd.to_datetime(trades["trade_date"]).dt.to_period("W-SUN").astype(str)
    weekly = trades.groupby("week", as_index=False).agg(
        net_pnl=("net_pnl", "sum"), gross_pnl=("gross_pnl", "sum"),
        transaction_costs=("transaction_costs", "sum"), slippage_cost=("slippage_cost", "sum"),
        total_friction=("total_costs", "sum"), trading_days=("trade_date", "count")
    )
    weekly["positive"] = weekly.net_pnl > 0
    summary = {
        "status": "COMPLETE", "slippage": slippage,
        "trade_days": int(len(trades)), "weeks": int(len(weekly)),
        "mean_daily_net": float(trades.net_pnl.mean()),
        "median_daily_net": float(trades.net_pnl.median()),
        "mean_weekly_net": float(weekly.net_pnl.mean()),
        "median_weekly_net": float(weekly.net_pnl.median()),
        "mean_weekly_total_friction": float(weekly.total_friction.mean()),
        "total_slippage_cost": float(trades.slippage_cost.sum()),
        "total_transaction_costs": float(trades.transaction_costs.sum()),
        "median_weekly_net": float(weekly.net_pnl.median()),
        "positive_week_rate": float(weekly.positive.mean()),
        "total_net": float(trades.net_pnl.sum()),
        "worst_day": float(trades.net_pnl.min()),
        "worst_week": float(weekly.net_pnl.min()),
        "max_drawdown_daily": float((trades.net_pnl.cumsum() - trades.net_pnl.cumsum().cummax()).min()),
        "execution_coverage": float(len(trades) / max(len(sessions), 1)),
        "missing_trade_days": int(len(missing)),
        "weekly_target": WEEKLY_TARGET,
        "target_mean_pass": bool(weekly.net_pnl.mean() >= WEEKLY_TARGET),
        "target_median_pass": bool(weekly.net_pnl.median() >= WEEKLY_TARGET),
        "target_positive_week_pass": bool(weekly.positive.mean() >= 0.70),
    }
    trades.to_csv(out / "trades.csv", index=False)
    weekly.to_csv(out / "weekly.csv", index=False)
    pd.DataFrame(missing).to_csv(out / "missing_days.csv", index=False)
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--slippage", type=float, required=True)
    args = ap.parse_args()
    print(json.dumps(run(args.data, args.out, args.slippage), indent=2))
