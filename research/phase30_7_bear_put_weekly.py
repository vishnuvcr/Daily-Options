#!/usr/bin/env python3
from __future__ import annotations

import bisect
import json
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

# Inputs are pinned by workflow.
OPTION_ROOT = Path("data/cache/phase30_2_rissin")
SPOT_ROOT = Path("data/cache/phase30_5_nifty_spot")
OUT_ROOT = Path("reports/phase30_7_bear_put")
START_DATE = date(2025, 9, 1)
END_DATE = date(2026, 8, 31)
LOT_CUTOFF = date(2026, 1, 6)
BROKERAGE = 10.0
BASE_SLIP = 0.20
STRESS_SLIP = 0.40
GAP_THRESHOLDS = (200.0, 300.0)
STRIKE_CONFIGS = ("ATM_W50", "OTM1_W50", "ATM_W100", "OTM1_W100")
STUDY_WEEK_TARGET = 20


@dataclass(frozen=True)
class SignalDef:
    lookback: int
    touch: float
    trigger: str
    threshold: float

    @property
    def id(self) -> str:
        return (
            f"lb{self.lookback}|tol{self.touch:.3f}|"
            f"{self.trigger}|thr{self.threshold:.3f}"
        )


def lot_size(expiry: date) -> int:
    return 75 if expiry < LOT_CUTOFF else 65


def option_glob() -> str:
    return str(OPTION_ROOT / "NIFTY_*.parquet")


def normalize_spot_timestamp(ts: pd.Series) -> pd.Series:
    out = pd.to_datetime(ts, errors="coerce")
    if getattr(out.dt, "tz", None) is None:
        return out.dt.tz_localize("Asia/Kolkata")
    return out.dt.tz_convert("Asia/Kolkata")


def load_spot() -> pd.DataFrame:
    frames = []
    for p in sorted(SPOT_ROOT.glob("*.csv")):
        x = pd.read_csv(p)
        x["Timestamp"] = normalize_spot_timestamp(x["Timestamp"])
        for c in ("Open", "High", "Low", "Close"):
            x[c] = pd.to_numeric(x[c], errors="coerce")
        x = x.dropna(subset=["Timestamp", "Open", "High", "Low", "Close"])
        x = x[(x.Timestamp.dt.date >= START_DATE) & (x.Timestamp.dt.date <= END_DATE)]
        frames.append(x[["Timestamp", "Open", "High", "Low", "Close"]])
    if not frames:
        raise RuntimeError("NO_SPOT_FILES")
    z = pd.concat(frames, ignore_index=True).sort_values("Timestamp")
    z = z.drop_duplicates("Timestamp").reset_index(drop=True)
    z["date"] = z.Timestamp.dt.date
    return z


def scan_day(day_df: pd.DataFrame, definition: SignalDef):
    x = day_df.sort_values("Timestamp").reset_index(drop=True)
    lb = definition.lookback
    if len(x) <= lb:
        return None
    highs = x["High"].to_numpy(float)
    opens = x["Open"].to_numpy(float)
    closes = x["Close"].to_numpy(float)
    windows = np.lib.stride_tricks.sliding_window_view(highs, lb)[:-1]
    resistance = windows.max(axis=1)
    touch_count = (windows >= resistance[:, None] * (1 - definition.touch)).sum(axis=1)
    candidate = np.flatnonzero(touch_count >= 2)
    if candidate.size == 0:
        return None
    if definition.trigger == "crack":
        cond = closes[lb:] <= resistance * (1 - definition.threshold)
    else:
        cond = opens[lb:] <= resistance * (1 - definition.threshold)
    hits = candidate[cond[candidate]]
    if hits.size == 0:
        return None
    k = int(hits[0])
    i = k + lb
    row = x.iloc[i]
    return {
        "date": str(day_df["date"].iloc[0]),
        "signal_ts": row.Timestamp.isoformat(),
        "resistance": float(resistance[k]),
        "spot_open": float(row.Open),
        "spot_close": float(row.Close),
    }


def build_all_signal_definitions():
    defs = []
    for lb in (30, 60, 120):
        for touch in (0.001, 0.002, 0.004):
            for trigger, vals in (("crack", (0.001, 0.002, 0.004)),
                                  ("gapdown", (0.002, 0.005, 0.010))):
                for threshold in vals:
                    defs.append(SignalDef(lb, touch, trigger, threshold))
    return defs


def generate_signals(spot: pd.DataFrame):
    by_day = {d: g.copy() for d, g in spot.groupby("date", sort=True)}
    out = {}
    for definition in build_all_signal_definitions():
        sigs = []
        for day, g in by_day.items():
            hit = scan_day(g, definition)
            if hit is not None:
                sigs.append(hit)
        weeks = sorted({pd.Timestamp(s["date"]).isocalendar()[:2] for s in sigs})
        if len(weeks) >= STUDY_WEEK_TARGET:
            out[definition.id] = (definition, sigs)
    return out


def load_expiries(con):
    q = f"""
    SELECT DISTINCT CAST(expiry AS DATE) AS expiry
    FROM read_parquet('{option_glob()}')
    WHERE upper(underlying)='NIFTY'
      AND granularity='1min'
      AND CAST(expiry AS DATE) BETWEEN DATE '{START_DATE}' AND DATE '{END_DATE}'
    ORDER BY expiry
    """
    x = con.execute(q).df()
    return [pd.Timestamp(v).date() for v in x["expiry"].tolist()]


def load_expiry_slice(con, expiry: date, start_date: date, end_date: date):
    q = f"""
    SELECT CAST(timestamp AS VARCHAR) AS ts_raw,
           CAST(expiry AS DATE) AS expiry,
           CAST(strike AS DOUBLE) AS strike,
           upper(option_type) AS option_type,
           CAST(open AS DOUBLE) AS open_px,
           CAST(close AS DOUBLE) AS close_px
    FROM read_parquet('{option_glob()}')
    WHERE upper(underlying)='NIFTY'
      AND granularity='1min'
      AND CAST(expiry AS DATE)=DATE '{expiry}'
      AND CAST(date AS DATE) BETWEEN DATE '{start_date}' AND DATE '{end_date}'
      AND CAST(timestamp AS TIMESTAMP)
            BETWEEN TIMESTAMP '{start_date} 09:00:00'
            AND TIMESTAMP '{end_date} 15:15:00'
      AND open > 0 AND close > 0
    ORDER BY option_type, strike, ts_raw
    """
    x = con.execute(q).df()
    if x.empty:
        return pd.DataFrame(columns=["ts", "expiry", "strike", "option_type", "open_px", "close_px"])
    raw = x["ts_raw"].astype(str).str.strip()
    aware = raw.str.contains(r"(?:[+-]d{2}:?d{2}|Z)$", regex=True, na=False)
    ts = pd.Series(pd.NaT, index=x.index, dtype="datetime64[ns]")
    if aware.any():
        p = pd.to_datetime(raw[aware], errors="coerce", utc=True)
        ts.loc[aware] = p.dt.tz_convert("Asia/Kolkata").dt.tz_localize(None)
    naive = ~aware
    if naive.any():
        p = pd.to_datetime(raw[naive], errors="coerce")
        ts.loc[naive] = p.dt.tz_localize("Asia/Kolkata").dt.tz_localize(None)
    x["ts"] = ts.dt.floor("min")
    x = x.drop(columns=["ts_raw"]).dropna(subset=["ts"])
    return x.drop_duplicates(["ts", "strike", "option_type"]).sort_values(["option_type", "strike", "ts"])


def exact_open(frame: pd.DataFrame, strike: float, side: str, ts: pd.Timestamp):
    x = frame[(frame.option_type == side) &
              (frame.strike == float(strike)) &
              (frame.ts == ts)]
    if x.empty:
        return None
    return float(x.iloc[0].open_px)


def exact_close(frame: pd.DataFrame, strike: float, side: str, ts: pd.Timestamp):
    x = frame[(frame.option_type == side) &
              (frame.strike == float(strike)) &
              (frame.ts == ts)]
    if x.empty:
        return None
    return float(x.iloc[0].close_px)


def nearest_open_after(frame: pd.DataFrame, strike: float, side: str, ts: pd.Timestamp):
    x = frame[(frame.option_type == side) &
              (frame.strike == float(strike)) &
              (frame.ts >= ts)].sort_values("ts")
    if x.empty:
        return None
    return x.iloc[0]


def nearest_spot_on_or_after(day_df: pd.DataFrame, ts: pd.Timestamp):
    x = day_df[day_df.Timestamp >= ts]
    return None if x.empty else x.iloc[0]


def round_to_50(x: float) -> float:
    return float(np.floor(x / 50.0 + 0.5) * 50.0)


def strike_pair(spot_price: float, config: str):
    atm = round_to_50(spot_price)
    long = atm if config.startswith("ATM") else atm - 50.0
    width = 50.0 if config.endswith("W50") else 100.0
    short = long - width
    return long, short


def transaction_cost(legs, lot, slippage, entry_date: date, exit_date: date):
    turnover = sum((x["entry"] + x["exit"]) * x["qty"] * lot for x in legs)
    sell_entry = sum(x["entry"] * x["qty"] * lot for x in legs if x["sign"] < 0)
    sell_exit = sum(x["exit"] * x["qty"] * lot for x in legs if x["sign"] > 0)
    buy_entry = sum(x["entry"] * x["qty"] * lot for x in legs if x["sign"] > 0)
    buy_exit = sum(x["exit"] * x["qty"] * lot for x in legs if x["sign"] < 0)

    brokerage = 2.0 * BROKERAGE * len(legs)
    exchange_rate = 0.0003503 if entry_date < date(2026, 3, 1) else 0.000355299
    exchange = turnover * exchange_rate
    sebi = turnover * 0.000001
    entry_stt = 0.001 if entry_date < date(2026, 4, 1) else 0.0015
    exit_stt = 0.001 if exit_date < date(2026, 4, 1) else 0.0015
    stt = sell_entry * entry_stt + sell_exit * exit_stt
    stamp = (buy_entry + buy_exit) * 0.00003
    gst = 0.18 * (brokerage + exchange + sebi)
    slip = 2.0 * slippage * sum(x["qty"] * lot for x in legs)
    return brokerage + exchange + sebi + stt + stamp + gst + slip


def settle(legs, lot, slippage, entry_date, exit_date):
    gross = sum(x["sign"] * (x["exit"] - x["entry"]) * x["qty"] * lot for x in legs)
    return gross - transaction_cost(legs, lot, slippage, entry_date, exit_date)


def conservative_zero_index_loss(legs, lot, entry_date, expiry_date, slippage):
    exit_entries = []
    for x in legs:
        k = x["strike"]
        payoff = max(k, 0.0) if x["option_type"] == "PE" else 0.0
        exit_entries.append({
            "entry": x["entry"],
            "exit": payoff,
            "sign": x["sign"],
            "qty": x["qty"],
        })
    gross = sum(x["sign"] * (x["exit"] - x["entry"]) * x["qty"] * lot for x in exit_entries)
    costs = transaction_cost(exit_entries, lot, slippage, entry_date, expiry_date)
    return max(0.0, -(gross - costs))


def simulate_position(
    frame: pd.DataFrame,
    spot_by_day: dict,
    signal: dict,
    expiry: date,
    config: str,
    gap_threshold: float,
    slippage: float,
):
    signal_day = date.fromisoformat(signal["date"])
    signal_ts = pd.Timestamp(signal["signal_ts"]).tz_localize(None)
    entry_ts = signal_ts + pd.Timedelta(minutes=1)

    long_strike, short_strike = strike_pair(signal["spot_close"], config)
    long_px = exact_open(frame, long_strike, "PE", entry_ts)
    short_px = exact_open(frame, short_strike, "PE", entry_ts)
    if long_px is None or short_px is None:
        return {"status": "incomplete", "reason": "ENTRY_MISSING"}
    initial_debit = long_px - short_px
    if not np.isfinite(initial_debit) or initial_debit <= 0:
        return {"status": "incomplete", "reason": "NONPOSITIVE_DEBIT"}
    lot = lot_size(expiry)
    next_days = sorted(d for d in spot_by_day if d > signal_day)
    adjust_day = next_days[0] if next_days else None

    base_legs = [
        {"entry": long_px, "exit": None, "sign": +1, "qty": 1, "strike": long_strike, "option_type": "PE"},
        {"entry": short_px, "exit": None, "sign": -1, "qty": 1, "strike": short_strike, "option_type": "PE"},
    ]
    adjusted = False
    reversal = False

    if adjust_day is not None and adjust_day <= expiry:
        prior_spot = spot_by_day[signal_day]
        next_spot = spot_by_day[adjust_day]
        prev_close = float(prior_spot.iloc[-1]["Close"])
        next_open_row = next_spot.iloc[0]
        next_open = float(next_open_row.Open)
        if next_open - prev_close >= gap_threshold and next_open > signal["resistance"]:
            check_ts = next_open_row.Timestamp + pd.Timedelta(minutes=60)
            check_row = nearest_spot_on_or_after(next_spot, check_ts)
            if check_row is not None and float(check_row.Close) > signal["resistance"]:
                adjust_exec = check_row.Timestamp.tz_convert("Asia/Kolkata").tz_localize(None) + pd.Timedelta(minutes=1)
                extra_px = exact_open(frame, short_strike, "PE", adjust_exec)
                if extra_px is not None:
                    adjusted = True
                    extra = {
                        "entry": extra_px, "exit": None, "sign": -1, "qty": 1,
                        "strike": short_strike, "option_type": "PE",
                    }
                    after = next_spot[next_spot.Timestamp >= (check_row.Timestamp + pd.Timedelta(minutes=1))]
                    under = after[after.Close < signal["resistance"]]
                    if not under.empty:
                        reversal = True
                        rev_ts = under.iloc[0].Timestamp.tz_convert("Asia/Kolkata").tz_localize(None) + pd.Timedelta(minutes=1)
                        rev_row = nearest_open_after(frame, short_strike, "PE", rev_ts)
                        if rev_row is not None:
                            extra["exit"] = float(rev_row.open_px)
                        else:
                            return {"status": "incomplete", "reason": "ADJUSTMENT_REVERSAL_EXIT_MISSING"}
                    if extra["exit"] is None:
                        final_ts = pd.Timestamp(f"{expiry} 15:15:00")
                        extra_close = exact_close(frame, short_strike, "PE", final_ts)
                        if extra_close is None:
                            return {"status": "incomplete", "reason": "EXPIRY_EXIT_MISSING_EXTRA"}
                        extra["exit"] = extra_close
                    base_legs.append(extra)

    final_ts = pd.Timestamp(f"{expiry} 15:15:00")
    long_exit = exact_close(frame, long_strike, "PE", final_ts)
    short_exit = exact_close(frame, short_strike, "PE", final_ts)
    if long_exit is None or short_exit is None:
        return {"status": "incomplete", "reason": "EXPIRY_EXIT_MISSING"}
    base_legs[0]["exit"] = long_exit
    base_legs[1]["exit"] = short_exit

    net = settle(base_legs, lot, slippage, signal_day, expiry)
    cap = initial_debit * lot
    risk0 = conservative_zero_index_loss(base_legs, lot, signal_day, expiry, slippage)

    return {
        "status": "complete",
        "net_pnl": float(net),
        "initial_capital": float(cap),
        "capital_at_zero_risk": float(risk0),
        "adjusted": adjusted,
        "reversal": reversal,
        "signal_date": str(signal_day),
        "expiry": str(expiry),
        "config": config,
        "gap_threshold": gap_threshold,
        "resistance": signal["resistance"],
        "signal_ts": signal["signal_ts"],
    }


def summarize(rows, errors, scenario, attempted_by_variant):
    if not rows:
        return {
            "scenario": scenario,
            "trades": 0,
            "positive_variants": 0,
            "qualified_variants": 0,
            "rows": [],
            "errors": errors,
        }
    df = pd.DataFrame(rows)
    df["week"] = pd.to_datetime(df["expiry"]).dt.isocalendar().week.astype(int)
    df["year"] = pd.to_datetime(df["expiry"]).dt.isocalendar().year.astype(int)

    summaries = []
    for vid, g in df.groupby("variant_id"):
        weekly = g.groupby(["year", "week"])["net_pnl"].sum()
        completed = int(len(weekly))
        profitable = float((weekly > 0).mean()) if completed else 0.0
        mean_week = float(weekly.mean()) if completed else 0.0
        median_week = float(weekly.median()) if completed else 0.0
        pf_pos = float(weekly[weekly > 0].sum()) if (weekly > 0).any() else 0.0
        pf_neg = float(-weekly[weekly < 0].sum()) if (weekly < 0).any() else 0.0
        pf = pf_pos / pf_neg if pf_neg else (float("inf") if pf_pos else 0.0)
        c = weekly.cumsum()
        dd = float((c - c.cummax()).min()) if len(c) else 0.0
        summaries.append({
            "variant_id": vid,
            "trades": int(len(g)),
            "completed_weeks": completed,
            "total_net": float(g.net_pnl.sum()),
            "mean_weekly_net": mean_week,
            "median_weekly_net": median_week,
            "profitable_week_rate": profitable,
            "profit_factor": pf,
            "max_drawdown": dd,
            "mean_initial_capital": float(g.initial_capital.mean()),
            "max_initial_capital": float(g.initial_capital.max()),
            "mean_conservative_zero_index_loss": float(g.capital_at_zero_risk.mean()),
            "adjustment_rate": float(g.adjusted.mean()),
            "reversal_rate_after_adjustment": float(g.loc[g.adjusted, "reversal"].mean()) if g.adjusted.any() else 0.0,
            "execution_coverage": float(len(g) / max(1, attempted_by_variant.get(vid, len(g)))),
        })
    summaries = sorted(summaries, key=lambda x: (x["mean_weekly_net"], x["median_weekly_net"]), reverse=True)
    qualified = [
        x for x in summaries
        if x["mean_weekly_net"] >= 5000
        and x["median_weekly_net"] >= 5000
        and x["profitable_week_rate"] >= 0.70
        and x["completed_weeks"] >= 20
        and x["execution_coverage"] >= 0.80
    ]
    return {
        "scenario": scenario,
        "trades": int(len(df)),
        "positive_variants": int(sum(x["mean_weekly_net"] > 0 for x in summaries)),
        "qualified_variants": int(len(qualified)),
        "best_measured": summaries[0] if summaries else None,
        "qualified": qualified,
        "all_variants": summaries,
        "errors": errors,
    }


def run_scenario(con, spot, signals, expiries, slippage, scenario):
    spot_by_day = {d: g.sort_values("Timestamp").copy() for d, g in spot.groupby("date", sort=True)}
    expiry_list = sorted(expiries)
    # Each signal is assigned to exactly one nearest weekly expiry on/after
    # its signal date. If a definition produces multiple signals for that
    # expiry, retain only its first signal. This prevents the same event from
    # being replicated across future expiries.
    positions_by_key = {}
    for did, (definition, sigs) in signals.items():
        for signal in sigs:
            signal_day = date.fromisoformat(signal["date"])
            idx = bisect.bisect_left(expiry_list, signal_day)
            if idx >= len(expiry_list):
                continue
            expiry = expiry_list[idx]
            key = (did, expiry)
            old = positions_by_key.get(key)
            if old is None or signal["signal_ts"] < old[2]["signal_ts"]:
                positions_by_key[key] = (did, definition, signal, expiry)
    positions = sorted(positions_by_key.values(), key=lambda x: (x[3], x[0], x[2]["signal_ts"]))

    rows, errors = [], []
    attempted_by_variant = {}
    grouped = {}
    for item in positions:
        grouped.setdefault(item[3], []).append(item)

    for expiry, items in sorted(grouped.items()):
        min_date = min(date.fromisoformat(x[2]["date"]) for x in items)
        frame = load_expiry_slice(con, expiry, min_date, expiry)
        if frame.empty:
            for did, _, signal, _ in items:
                for config in STRIKE_CONFIGS:
                    for gap in GAP_THRESHOLDS:
                        vid = f"{did}|{config}|gap{gap:g}"
                        attempted_by_variant[vid] = attempted_by_variant.get(vid, 0) + 1
                        errors.append({"variant": vid, "status": "incomplete", "reason": "EMPTY_EXPIRY_FRAME"})
            continue
        for did, definition, signal, exp in items:
            for config in STRIKE_CONFIGS:
                for gap in GAP_THRESHOLDS:
                    vid = f"{did}|{config}|gap{gap:g}"
                    attempted_by_variant[vid] = attempted_by_variant.get(vid, 0) + 1
                    try:
                        res = simulate_position(frame, spot_by_day, signal, exp, config, gap, slippage)
                    except Exception as exc:
                        errors.append({"variant": vid, "signal_date": signal["date"], "error": repr(exc)})
                        continue
                    if res["status"] == "complete":
                        rows.append({"variant_id": vid, **res})
                    else:
                        errors.append({"variant": vid, "signal_date": signal["date"], "error": res["reason"]})
        del frame

    summary = summarize(rows, errors, scenario, attempted_by_variant)
    summary["eligible_signal_definitions"] = len(signals)
    summary["attempted_positions"] = int(sum(attempted_by_variant.values()))
    return summary


def main():
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    spot = load_spot()
    signals = generate_signals(spot)
    con = duckdb.connect()
    con.execute("SET TimeZone='Asia/Kolkata'")
    expiries = load_expiries(con)
    base = run_scenario(con, spot, signals, expiries, BASE_SLIP, "BASE")
    stress = run_scenario(con, spot, signals, expiries, STRESS_SLIP, "STRESS")
    report = {
        "study_window": [str(START_DATE), str(END_DATE)],
        "eligible_signal_definitions": len(signals),
        "cell_count_per_scenario": len(signals) * len(STRIKE_CONFIGS) * len(GAP_THRESHOLDS),
        "strike_configs": STRIKE_CONFIGS,
        "gap_thresholds": GAP_THRESHOLDS,
        "base": base,
        "stress": stress,
        "backtest_authorized": True,
    }
    out = OUT_ROOT / "phase30_7_bear_put_result.json"
    out.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({
        "eligible_definitions": len(signals),
        "cells": report["cell_count_per_scenario"],
        "base_qualified": base["qualified_variants"],
        "stress_qualified": stress["qualified_variants"],
        "base_trades": base["trades"],
        "stress_trades": stress["trades"],
    }, indent=2))


if __name__ == "__main__":
    main()
