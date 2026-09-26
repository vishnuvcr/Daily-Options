
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

ENTRY_TIMES = ("09:30:00", "10:00:00", "11:00:00", "13:00:00", "14:00:00")
TARGET_PREMIUMS = (20.0, 25.0, 30.0)
FAR_MODES = ("DIAGONAL_PREMIUM", "SAME_STRIKE")
ADJUST_TIMES = ("09:30:00", "10:00:00", "11:00:00")
STOP_MULTIPLES = (0.50, 1.00, 1.50)

START_DATE = pd.Timestamp("2025-09-01").date()
END_CAP = pd.Timestamp("2026-08-31").date()
WEEKLY_TARGET = 5000.0
POSITIVE_WEEK_RATE_TARGET = 0.70
EXECUTION_COVERAGE_TARGET = 0.80


@dataclass(frozen=True)
class Variant:
    entry_time: str
    target_premium: float
    far_mode: str
    adjust_time: str
    stop_multiple: float

    @property
    def variant_id(self) -> str:
        return (
            f"{self.entry_time}|p{self.target_premium:g}|{self.far_mode}|"
            f"adj{self.adjust_time}|stop{self.stop_multiple:g}"
        )


def variant_grid():
    return [Variant(e, p, f, a, s)
            for e in ENTRY_TIMES for p in TARGET_PREMIUMS
            for f in FAR_MODES for a in ADJUST_TIMES for s in STOP_MULTIPLES]


def lot_size(expiry):
    d = pd.Timestamp(expiry).date()
    if d < pd.Timestamp("2021-07-01").date():
        return 75
    if d < pd.Timestamp("2024-04-26").date():
        return 50
    if d < pd.Timestamp("2024-11-21").date():
        return 25
    if d < pd.Timestamp("2026-01-06").date():
        return 75
    return 65


def glob_expr(root: Path) -> str:
    return str(root / "NIFTY_*.parquet")


def load_calendar(con, root: Path):
    path = glob_expr(root)
    sessions = con.execute(
        f"""
        SELECT DISTINCT CAST(date AS DATE) AS trade_date
        FROM read_parquet('{path}')
        WHERE upper(underlying)='NIFTY'
          AND granularity='1min'
          AND CAST(date AS DATE) BETWEEN DATE '{START_DATE}' AND DATE '{END_CAP}'
        ORDER BY trade_date
        """
    ).df()
    expiries = con.execute(
        f"""
        SELECT DISTINCT CAST(expiry AS DATE) AS expiry_date
        FROM read_parquet('{path}')
        WHERE upper(underlying)='NIFTY'
          AND granularity='1min'
          AND CAST(expiry AS DATE) >= DATE '{START_DATE}'
          AND CAST(expiry AS DATE) <= DATE '{END_CAP}' + INTERVAL 31 DAY
        ORDER BY expiry_date
        """
    ).df()
    sessions["trade_date"] = pd.to_datetime(sessions["trade_date"]).dt.date
    expiries["expiry_date"] = pd.to_datetime(expiries["expiry_date"]).dt.date
    return sessions["trade_date"].tolist(), expiries["expiry_date"].tolist()


def expiry_setups(sessions, expiries):
    # Build setups by the same calendar invariant used by the independently
    # audited Phase-25 Falcon implementation: an entry date is valid only when
    # it is exactly the fourth prior trading session to the near expiry.
    # This avoids constructing candidate calendars from expiry rows that may
    # not be present on the actual entry-date chain.
    session_list = sorted(set(sessions))
    usable = sorted(e for e in set(expiries) if START_DATE <= e <= END_CAP)
    out = []
    for entry_date in session_list:
        if not (START_DATE <= entry_date <= END_CAP):
            continue
        future_exp = [e for e in usable if e >= entry_date]
        if len(future_exp) < 2:
            continue
        near_exp, far_exp = future_exp[0], future_exp[1]
        prior = [d for d in session_list if d < near_exp]
        if len(prior) < 4 or prior[-4] != entry_date:
            continue
        adjust_date, exit_date = prior[-3], prior[-1]
        out.append(
            {
                "near_expiry": near_exp,
                "far_expiry": far_exp,
                "entry_date": entry_date,
                "adjust_date": adjust_date,
                "exit_date": exit_date,
            }
        )
    return out


def load_snapshot(con, root, entry_date, near_expiry, far_expiry, ts, fill_ts):
    path = glob_expr(root)
    q = f"""
    SELECT CAST(timestamp AS TIMESTAMP) AS ts,
           CAST(expiry AS DATE) AS expiry,
           CAST(strike AS DOUBLE) AS strike,
           upper(option_type) AS option_type,
           CAST(open AS DOUBLE) AS open_px,
           CAST(close AS DOUBLE) AS close_px
    FROM read_parquet('{path}')
    WHERE upper(underlying)='NIFTY'
      AND granularity='1min'
      AND CAST(date AS DATE)=DATE '{entry_date}'
      AND CAST(expiry AS DATE) IN (DATE '{near_expiry}', DATE '{far_expiry}')
      AND CAST(timestamp AS TIMESTAMP) BETWEEN TIMESTAMP '{ts}' AND TIMESTAMP '{fill_ts}'
      AND open > 0 AND close > 0
    ORDER BY expiry, option_type, strike, ts
    """
    return con.execute(q).df()


def select_target(chain, expiry, side, target, ref_strike=None, far_otm=False):
    x = chain[(chain.expiry == pd.Timestamp(expiry).date()) & (chain.option_type == side)].copy()
    if ref_strike is not None:
        if far_otm:
            x = x[x.strike >= float(ref_strike)] if side == "CE" else x[x.strike <= float(ref_strike)]
        else:
            x = x[x.strike == float(ref_strike)]
    if x.empty:
        return None
    x["dist"] = (x.close_px - float(target)).abs()
    return x.sort_values(["dist", "strike"]).iloc[0]


def open_at(df, side, strike, ts):
    x = df[(df.option_type == side) & (df.strike == float(strike)) & (df.ts == pd.Timestamp(ts))]
    if x.empty or pd.isna(x.iloc[0].open_px) or x.iloc[0].open_px <= 0:
        return None
    return float(x.iloc[0].open_px)


def load_series(con, root, trade_start, trade_end, expiry, strike, side):
    path = glob_expr(root)
    q = f"""
    SELECT CAST(timestamp AS TIMESTAMP) AS ts,
           CAST(open AS DOUBLE) AS open_px,
           CAST(close AS DOUBLE) AS close_px
    FROM read_parquet('{path}')
    WHERE upper(underlying)='NIFTY'
      AND granularity='1min'
      AND CAST(expiry AS DATE)=DATE '{expiry}'
      AND CAST(strike AS DOUBLE)={float(strike)}
      AND upper(option_type)='{side}'
      AND CAST(timestamp AS TIMESTAMP) BETWEEN TIMESTAMP '{trade_start} 09:00:00'
          AND TIMESTAMP '{trade_end} 15:15:00'
      AND close > 0
    ORDER BY ts
    """
    x = con.execute(q).df()
    if x.empty:
        return pd.DataFrame(columns=["ts", "open_px", "close_px"])
    x["ts"] = pd.to_datetime(x["ts"]).dt.floor("min")
    return x.drop_duplicates("ts").sort_values("ts")


def next_open(s, after_ts):
    z = s[s.ts >= pd.Timestamp(after_ts)]
    return None if z.empty else z.iloc[0]


def mark_panel(series_map, tolerance_minutes=1):
    base = None
    for name, s in series_map.items():
        z = s[["ts", "close_px"]].rename(columns={"close_px": name}).sort_values("ts")
        base = z if base is None else pd.merge_asof(
            base.sort_values("ts"), z, on="ts",
            direction="backward",
            tolerance=pd.Timedelta(minutes=tolerance_minutes),
        )
    return pd.DataFrame() if base is None else base.dropna().sort_values("ts")


def cost(legs, lot, slippage, brokerage_per_order, entry_date=None, exit_date=None):
    turnover = sum((leg["entry"] + leg["exit"]) * leg["qty"] * lot for leg in legs)
    sell_entry = sum(leg["entry"] * leg["qty"] * lot for leg in legs if leg["sign"] < 0)
    sell_exit = sum(leg["exit"] * leg["qty"] * lot for leg in legs if leg["sign"] > 0)
    buy_entry = sum(leg["entry"] * leg["qty"] * lot for leg in legs if leg["sign"] > 0)
    buy_exit = sum(leg["exit"] * leg["qty"] * lot for leg in legs if leg["sign"] < 0)
    brokerage = 2.0 * brokerage_per_order * len(legs)
    exchange_rate = 0.0003503 if (entry_date is None or pd.Timestamp(entry_date).date() < date(2026, 3, 1)) else 0.000355299
    exchange = turnover * exchange_rate
    sebi = turnover * 0.000001
    entry_stt = 0.001 if entry_date is None or pd.Timestamp(entry_date).date() < date(2026, 4, 1) else 0.0015
    exit_stt = 0.001 if exit_date is None or pd.Timestamp(exit_date).date() < date(2026, 4, 1) else 0.0015
    stt = sell_entry * entry_stt + sell_exit * exit_stt
    stamp = (buy_entry + buy_exit) * 0.00003
    gst = 0.18 * (brokerage + exchange + sebi)
    slip = 2.0 * slippage * sum(leg["qty"] * lot for leg in legs)
    return brokerage + exchange + sebi + stt + stamp + gst + slip


def settle(legs, lot, slippage, brokerage_per_order, entry_date=None, exit_date=None):
    gross = sum(leg["sign"] * (leg["exit"] - leg["entry"]) * leg["qty"] * lot for leg in legs)
    return gross - cost(legs, lot, slippage, brokerage_per_order, entry_date, exit_date)


def build_setup(con, root, cal, entry_time, target, far_mode):
    entry_date, adjust_date, exit_date = cal["entry_date"], cal["adjust_date"], cal["exit_date"]
    near_exp, far_exp = cal["near_expiry"], cal["far_expiry"]
    signal_ts = pd.Timestamp(f"{entry_date} {entry_time}")
    fill_ts = signal_ts + pd.Timedelta(minutes=1)
    snap = load_snapshot(con, root, entry_date, near_exp, far_exp, signal_ts, fill_ts)
    if snap.empty:
        return None

    near_signal = snap[snap.ts == signal_ts]
    near_fill = snap[snap.ts == fill_ts]
    far_signal = snap[snap.ts == signal_ts]
    far_fill = snap[snap.ts == fill_ts]
    sce = select_target(near_signal, near_exp, "CE", target)
    spe = select_target(near_signal, near_exp, "PE", target)
    if sce is None or spe is None:
        return None

    if far_mode == "SAME_STRIKE":
        fce = select_target(far_signal, far_exp, "CE", target, ref_strike=sce.strike)
        fpe = select_target(far_signal, far_exp, "PE", target, ref_strike=spe.strike)
    else:
        fce = select_target(far_signal, far_exp, "CE", target, ref_strike=sce.strike, far_otm=True)
        fpe = select_target(far_signal, far_exp, "PE", target, ref_strike=spe.strike, far_otm=True)
    if any(x is None for x in (fce, fpe)):
        return None

    sc, sp = open_at(near_fill, "CE", sce.strike, fill_ts), open_at(near_fill, "PE", spe.strike, fill_ts)
    fc, fp = open_at(far_fill, "CE", fce.strike, fill_ts), open_at(far_fill, "PE", fpe.strike, fill_ts)
    if any(x is None for x in (sc, sp, fc, fp)):
        return None
    credit = 5.0 * (sc + sp) - 3.0 * (fc + fp)
    if not np.isfinite(credit) or credit <= 0:
        return None

    return {
        "entry_date": entry_date, "adjust_date": adjust_date, "exit_date": exit_date,
        "entry_ts": signal_ts, "entry_fill_ts": fill_ts,
        "near_expiry": near_exp, "far_expiry": far_exp,
        "near_strikes": {"ce": float(sce.strike), "pe": float(spe.strike)},
        "far_strikes": {"ce": float(fce.strike), "pe": float(fpe.strike)},
        "entry_prices": {"sce": sc, "spe": sp, "fce": fc, "fpe": fp},
        "initial_credit": float(credit), "far_mode": far_mode,
        "target_premium": float(target), "entry_time": entry_time, "_cache": {},
    }


def simulate_setup(con, root, setup, variant, slippage, brokerage_per_order, series_cache, strike_cache):
    c = setup["_cache"]
    lot = lot_size(setup["near_expiry"])

    def cached_series(trade_start, trade_end, expiry, strike, side):
        key = (str(trade_start), str(trade_end), str(expiry), float(strike), side)
        if key not in series_cache:
            series_cache[key] = load_series(con, root, trade_start, trade_end, expiry, strike, side)
        return series_cache[key]
    start = setup["entry_fill_ts"]
    end = pd.Timestamp(f"{setup['exit_date']} 15:15:00")
    adjust_signal = pd.Timestamp(f"{setup['adjust_date']} {variant.adjust_time}")
    adjust_exec = adjust_signal + pd.Timedelta(minutes=1)

    if "initial" not in c:
        c["initial"] = {
            "sce": cached_series(setup["entry_date"], setup["exit_date"], setup["near_expiry"], setup["near_strikes"]["ce"], "CE"),
            "spe": cached_series(setup["entry_date"], setup["exit_date"], setup["near_expiry"], setup["near_strikes"]["pe"], "PE"),
            "fce": cached_series(setup["entry_date"], setup["exit_date"], setup["far_expiry"], setup["far_strikes"]["ce"], "CE"),
            "fpe": cached_series(setup["entry_date"], setup["exit_date"], setup["far_expiry"], setup["far_strikes"]["pe"], "PE"),
        }
    initial = c["initial"]
    if any(s.empty for s in initial.values()):
        return None

    if "pre_panel" not in c:
        c["pre_panel"] = mark_panel(initial, 1)

    pre_stop = next(
        (row.ts for row in c["pre_panel"].itertuples(index=False)
         if start <= row.ts < adjust_signal
         and setup["initial_credit"] - 5*row.sce - 5*row.spe + 3*row.fce + 3*row.fpe
             <= -variant.stop_multiple * setup["initial_credit"]),
        None,
    )

    base_legs = [
        {"entry": setup["entry_prices"]["sce"], "exit": None, "sign": -1, "qty": 5},
        {"entry": setup["entry_prices"]["spe"], "exit": None, "sign": -1, "qty": 5},
        {"entry": setup["entry_prices"]["fce"], "exit": None, "sign": 1, "qty": 3},
        {"entry": setup["entry_prices"]["fpe"], "exit": None, "sign": 1, "qty": 3},
    ]

    if pre_stop is not None:
        exit_ts = pre_stop + pd.Timedelta(minutes=1)
        for leg, key in zip(base_legs, ("sce", "spe", "fce", "fpe")):
            row = next_open(initial[key], exit_ts)
            if row is None:
                return None
            leg["exit"] = float(row.open_px)
        return {
            "reason": "STOP_PRE_ADJUST", "exit_ts": exit_ts,
            "net_pnl": settle(base_legs, lot, slippage, brokerage_per_order, setup["entry_date"], exit_ts.date()),
            "active_legs": 4,
        }

    adjustments = c.setdefault("adjustments", {})
    wing_key = variant.adjust_time
    if wing_key not in adjustments:
        path = glob_expr(root)
        strike_df = con.execute(
            f"""
            SELECT DISTINCT CAST(strike AS DOUBLE) strike, upper(option_type) option_type
            FROM read_parquet('{path}')
            WHERE upper(underlying)='NIFTY'
              AND granularity='1min'
              AND CAST(date AS DATE)=DATE '{setup["adjust_date"]}'
              AND CAST(expiry AS DATE)=DATE '{setup["near_expiry"]}'
            """
        ).df()
        ce_all = np.sort(strike_df.loc[strike_df.option_type=="CE","strike"].unique())
        pe_all = np.sort(strike_df.loc[strike_df.option_type=="PE","strike"].unique())
        ce_w = ce_all[ce_all > setup["near_strikes"]["ce"]]
        pe_w = pe_all[pe_all < setup["near_strikes"]["pe"]]
        if len(ce_w) == 0 or len(pe_w) == 0:
            return None
        wing_ce, wing_pe = float(ce_w[0]), float(pe_w[-1])

        wce = cached_series(setup["adjust_date"], setup["exit_date"], setup["near_expiry"], wing_ce, "CE")
        wpe = cached_series(setup["adjust_date"], setup["exit_date"], setup["near_expiry"], wing_pe, "PE")
        if wce.empty or wpe.empty:
            return None
        wce_row, wpe_row = next_open(wce, adjust_exec), next_open(wpe, adjust_exec)
        if wce_row is None or wpe_row is None:
            return None
        post = mark_panel({"sce": initial["sce"], "spe": initial["spe"], "fce": initial["fce"], "fpe": initial["fpe"],
                           "wce": wce, "wpe": wpe}, 1)
        adjustments[wing_key] = {
            "wce": wce, "wpe": wpe,
            "wce_entry": float(wce_row.open_px), "wpe_entry": float(wpe_row.open_px),
            "post": post[post.ts >= adjust_exec].copy(),
        }

    adj = adjustments[wing_key]
    legs = base_legs + [
        {"entry": adj["wce_entry"], "exit": None, "sign": 1, "qty": 5},
        {"entry": adj["wpe_entry"], "exit": None, "sign": 1, "qty": 5},
    ]

    post_stop = next(
        (row.ts for row in adj["post"].itertuples(index=False)
         if setup["initial_credit"] - 5*row.sce - 5*row.spe + 3*row.fce + 3*row.fpe
              + 5*row.wce + 5*row.wpe
              - 5*adj["wce_entry"] - 5*adj["wpe_entry"]
             <= -variant.stop_multiple * setup["initial_credit"]),
        None,
    )

    exit_signal = post_stop if post_stop is not None else end
    exit_from = exit_signal + pd.Timedelta(minutes=1)
    for leg, s in zip(legs, (initial["sce"], initial["spe"], initial["fce"], initial["fpe"], adj["wce"], adj["wpe"])):
        row = next_open(s, exit_from)
        if row is None:
            z = s[s.ts <= exit_signal].tail(1)
            if z.empty:
                return None
            leg["exit"] = float(z.iloc[0].close_px)
        else:
            leg["exit"] = float(row.open_px)

    return {
        "reason": "STOP_POST_ADJUST" if post_stop is not None else "PRE_EXPIRY_EXIT",
        "exit_ts": exit_signal,
        "net_pnl": settle(legs, lot, slippage, brokerage_per_order, setup["entry_date"], exit_signal.date()),
        "active_legs": 6,
    }


def max_drawdown(values):
    if len(values) == 0:
        return 0.0
    c = np.cumsum(values)
    return float(np.min(c - np.maximum.accumulate(c)))


def run(data: Path, out: Path, slippage: float, brokerage_per_order: float):
    out.mkdir(parents=True, exist_ok=True)
    variants = variant_grid()
    con = duckdb.connect()
    con.execute("SET TimeZone='Asia/Kolkata'")
    sessions, expiries = load_calendar(con, data)
    cals = expiry_setups(sessions, expiries)

    setups = []
    for cal in cals:
        for entry_time in ENTRY_TIMES:
            for target in TARGET_PREMIUMS:
                for far_mode in FAR_MODES:
                    s = build_setup(con, data, cal, entry_time, target, far_mode)
                    if s is not None:
                        setups.append(s)

    series_cache, strike_cache = {}, {}
    by_key = {}
    for v in variants:
        by_key.setdefault((v.entry_time, v.target_premium, v.far_mode), []).append(v)

    rows, errors = [], []
    for setup in setups:
        for v in by_key[(setup["entry_time"], setup["target_premium"], setup["far_mode"])]:
            try:
                result = simulate_setup(con, data, setup, v, slippage, brokerage_per_order, series_cache, strike_cache)
            except Exception as exc:
                errors.append({"entry_date": str(setup["entry_date"]), "variant_id": v.variant_id, "error": repr(exc)})
                result = None
            if result is not None:
                rows.append({"variant_id": v.variant_id, "entry_date": setup["entry_date"],
                             "adjust_date": setup["adjust_date"], "exit_date": setup["exit_date"],
                             "near_expiry": setup["near_expiry"], "far_expiry": setup["far_expiry"],
                             "entry_ts": setup["entry_ts"], **result})

    if errors:
        (out / "phase24_rissin_sim_errors.json").write_text(json.dumps(errors[:500], indent=2, default=str))

    trades = pd.DataFrame(rows)
    coverage = {
        "source": "rissin/nse-options-intraday",
        "revision": "resolved at workflow runtime and persisted in data manifest",
        "window_start": str(START_DATE),
        "window_cap": str(END_CAP),
        "calendar_expiries": len(cals),
        "candidate_setups": len(setups),
        "unique_entry_dates": 0 if trades.empty else int(pd.Series(trades["entry_date"]).nunique()),
        "unique_calendar_weeks": 0 if trades.empty else int(pd.Series(trades["week"]).nunique()) if "week" in trades else 0,
    }
    (out / "phase24_rissin_coverage.json").write_text(json.dumps(coverage, indent=2, default=str))

    if trades.empty:
        summary = {"variants": len(variants), "setups": len(setups), "trades": 0,
                   "positive_variants": 0, "target_qualified": 0, "best": None,
                   "slippage": slippage, "coverage": coverage}
        (out / "phase24_rissin_summary.json").write_text(json.dumps(summary, indent=2, default=str))
        con.close()
        return summary

    trades["entry_date"] = pd.to_datetime(trades["entry_date"]).dt.date
    trades.to_csv(out / "phase24_rissin_trades.csv", index=False)
    daily = trades.groupby(["variant_id", "entry_date"], as_index=False).net_pnl.sum()

    leaderboard = trades.groupby("variant_id").agg(
        trades=("net_pnl", "size"),
        total_net=("net_pnl", "sum"),
        mean_trade=("net_pnl", "mean"),
        win_rate=("net_pnl", lambda x: float((x > 0).mean())),
    ).reset_index()
    stats = daily.groupby("variant_id").net_pnl.agg(["mean", "median"]).reset_index()
    stats = stats.rename(columns={"mean": "mean_active_day_net", "median": "median_active_day_net"})
    leaderboard = leaderboard.merge(stats, on="variant_id")

    pf_map, dd_map, day_map = {}, {}, {}
    for vid, g in daily.groupby("variant_id"):
        x = g.sort_values("entry_date").net_pnl.to_numpy(dtype=float)
        gain = float(x[x > 0].sum()) if np.any(x > 0) else 0.0
        loss = float(-x[x < 0].sum()) if np.any(x < 0) else 0.0
        pf_map[vid] = gain / loss if loss > 0 else (float("inf") if gain > 0 else 0.0)
        dd_map[vid] = max_drawdown(x)
        day_map[vid] = len(x)

    leaderboard["profit_factor"] = leaderboard.variant_id.map(pf_map)
    leaderboard["max_drawdown"] = leaderboard.variant_id.map(dd_map)
    leaderboard["active_days"] = leaderboard.variant_id.map(day_map).astype(int)
    # Weekly target is evaluated on completed trading weeks, not active days.
    trades["week"] = pd.to_datetime(trades["entry_date"]).dt.to_period("W-MON").astype(str)
    weekly = trades.groupby(["variant_id","week"], as_index=False).net_pnl.sum()
    weekly_stats = weekly.groupby("variant_id").net_pnl.agg(["mean","median"]).reset_index()
    weekly_stats = weekly_stats.rename(columns={"mean":"mean_weekly_net","median":"median_weekly_net"})
    weekly_stats["positive_week_rate"] = weekly.groupby("variant_id").net_pnl.apply(lambda x: float((x>0).mean())).values
    weekly_stats["completed_weeks"] = weekly.groupby("variant_id").size().values
    leaderboard = leaderboard.merge(weekly_stats,on="variant_id",how="left")
    leaderboard["execution_coverage"] = leaderboard["completed_weeks"] / max(len(cals), 1)
    leaderboard["target_qualified"] = (
        (leaderboard["mean_weekly_net"] >= WEEKLY_TARGET) &
        (leaderboard["median_weekly_net"] >= WEEKLY_TARGET) &
        (leaderboard["positive_week_rate"] >= POSITIVE_WEEK_RATE_TARGET) &
        (leaderboard["completed_weeks"] >= 20) &
        (leaderboard["execution_coverage"] >= EXECUTION_COVERAGE_TARGET)
    )
    leaderboard = leaderboard.sort_values(["mean_active_day_net", "profit_factor"], ascending=False)
    leaderboard.to_csv(out / "phase24_rissin_leaderboard.csv", index=False)

    best = leaderboard.iloc[0].to_dict() if not leaderboard.empty else None
    summary = {
        "variants": len(variants),
        "setups": len(setups),
        "trades": int(len(trades)),
        "positive_variants": int((leaderboard.mean_active_day_net > 0).sum()),
        "target_qualified": int(leaderboard.target_qualified.sum()),
        "weekly_target": WEEKLY_TARGET,
        "positive_week_rate_target": POSITIVE_WEEK_RATE_TARGET,
        "execution_coverage_target": EXECUTION_COVERAGE_TARGET,
        "unique_entry_dates": int(pd.Series(trades["entry_date"]).nunique()),
        "best": best,
        "slippage": slippage,
        "brokerage_per_order": brokerage_per_order,
        "coverage": coverage,
    }
    (out / "phase24_rissin_summary.json").write_text(json.dumps(summary, indent=2, default=str))
    con.close()
    return summary


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--slippage", type=float, default=0.20)
    ap.add_argument("--brokerage", type=float, default=10.0)
    args = ap.parse_args()
    print(json.dumps(run(args.data, args.out, args.slippage, args.brokerage), indent=2, default=str))
