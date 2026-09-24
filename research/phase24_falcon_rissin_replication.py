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
START_DATE = date(2024, 10, 1)
END_DATE = date(2026, 8, 4)


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
    return [
        Variant(e, p, f, a, s)
        for e in ENTRY_TIMES
        for p in TARGET_PREMIUMS
        for f in FAR_MODES
        for a in ADJUST_TIMES
        for s in STOP_MULTIPLES
    ]


def lot_size(expiry):
    d = pd.Timestamp(expiry).date()
    if d < date(2024, 11, 21):
        return 25
    if d < date(2026, 1, 6):
        return 75
    return 65


def parquet_expr(paths: list[Path]) -> str:
    if not paths:
        raise FileNotFoundError("no Rissin NIFTY parquet files")
    vals = []
    for path in paths:
        vals.append("'" + str(path).replace("'", "''") + "'")
    return "[" + ",".join(vals) + "]"


def source_files(root: Path) -> list[Path]:
    base = root / "upstox_intraday" / "NIFTY"
    files = []
    for year in (2024, 2025, 2026):
        path = base / f"NIFTY_{year}.parquet"
        if path.exists():
            files.append(path)
    if len(files) != 3:
        raise FileNotFoundError(f"expected NIFTY 2024-2026 files under {base}")
    return files


def read_dates_and_expiries(con, files: list[Path]):
    expr = parquet_expr(files)
    q = f"""
      SELECT DISTINCT
        CAST(date AS DATE) AS trade_date,
        TRY_CAST(expiry AS DATE) AS expiry_date
      FROM read_parquet({expr}, union_by_name=true)
      WHERE UPPER(CAST(underlying AS VARCHAR))='NIFTY'
        AND CAST(date AS DATE) BETWEEN DATE '{START_DATE}' AND DATE '{END_DATE}'
        AND TRY_CAST(expiry AS DATE) IS NOT NULL
    """
    return con.execute(q).df()


def build_schedule(sessions, expiries, expiry_date):
    # Historical Thursday expiry: Friday entry -> Monday adjustment -> Wednesday exit.
    # Current Tuesday expiry: Wednesday entry -> Thursday adjustment -> Monday exit.
    # This uses entry = expiry - 4 sessions; adjustment = expiry - 3 sessions; exit = expiry - 1 session.
    # Explicit current wording: Wednesday entry -> Thursday adjustment -> Monday exit.
    prior = [d for d in sessions if d < expiry_date]
    if len(prior) < 4:
        return None
    entry = prior[-4]
    adjustment = prior[-3]
    exit = prior[-1]
    later = sorted([d for d in expiries if d > expiry_date])
    if not later:
        return None
    return {
        "entry_date": entry,
        "near_expiry": expiry_date,
        "far_expiry": later[0],
        "adjust_date": adjustment,
        "exit_date": exit,
    }


def executable_schedules(con, files):
    meta = read_dates_and_expiries(con, files)
    sessions = sorted(pd.to_datetime(meta.trade_date.dropna()).dt.date.unique())
    expiries = sorted(pd.to_datetime(meta.expiry_date.dropna()).dt.date.unique())
    schedules = []
    seen = set()
    for expiry_date in expiries:
        if expiry_date < START_DATE or expiry_date > END_DATE:
            continue
        s = build_schedule(sessions, expiries, expiry_date)
        if not s or s["entry_date"] < START_DATE or s["entry_date"] > END_DATE:
            continue
        key = (s["entry_date"], s["near_expiry"], s["far_expiry"], s["adjust_date"], s["exit_date"])
        if key not in seen:
            schedules.append(s)
            seen.add(key)
    return schedules, sessions, expiries


def coverage_report(root: Path):
    files = source_files(root)
    con = duckdb.connect()
    con.execute("SET TimeZone='Asia/Kolkata'")
    schedules, sessions, expiries = executable_schedules(con, files)
    meta = read_dates_and_expiries(con, files)
    con.close()
    observed_min = min(sessions) if sessions else None
    observed_max = max(sessions) if sessions else None
    report = {
        "files": [str(x) for x in files],
        "observed_min_date": str(observed_min) if observed_min else None,
        "observed_max_date": str(observed_max) if observed_max else None,
        "distinct_trading_dates": len(sessions),
        "distinct_expiry_dates": len(expiries),
        "executable_expiry_relative_entry_dates": len(schedules),
        "rows": int(len(meta)),
        "coverage_ok": bool(
            observed_min is not None and observed_min <= START_DATE
            and observed_max is not None and observed_max >= END_DATE
            and len(sessions) >= 400
            and len(expiries) >= 80
            and len(schedules) >= 80
        ),
    }
    return report


def connect(root: Path):
    con = duckdb.connect()
    con.execute("SET TimeZone='Asia/Kolkata'")
    return con, source_files(root)


def load_entry_chain(con, files, trade_date, start_ts, end_ts, expiry_dates):
    expr = parquet_expr(files)
    exps = ",".join("DATE '" + str(x) + "'" for x in expiry_dates)
    q = f"""
      SELECT
        CAST(timestamp AS TIMESTAMP) AS ts,
        TRY_CAST(expiry AS DATE) AS expiry,
        CAST(strike AS DOUBLE) AS strike,
        UPPER(CAST(option_type AS VARCHAR)) AS option_type,
        CAST(open AS DOUBLE) AS open_px,
        CAST(close AS DOUBLE) AS close_px
      FROM read_parquet({expr}, union_by_name=true)
      WHERE UPPER(CAST(underlying AS VARCHAR))='NIFTY'
        AND CAST(date AS DATE)=DATE '{trade_date}'
        AND TRY_CAST(expiry AS DATE) IN ({exps})
        AND CAST(timestamp AS TIMESTAMP) BETWEEN TIMESTAMP '{start_ts}' AND TIMESTAMP '{end_ts}'
        AND close > 0
      ORDER BY ts, expiry, strike, option_type
    """
    x = con.execute(q).df()
    if x.empty:
        return x
    x["ts"] = pd.to_datetime(x["ts"]).dt.floor("min")
    x["expiry"] = pd.to_datetime(x["expiry"]).dt.date
    return x


def load_series(con, files, expiry, strike, side, start_ts, end_ts):
    expr = parquet_expr(files)
    q = f"""
      SELECT
        CAST(timestamp AS TIMESTAMP) AS ts,
        CAST(open AS DOUBLE) AS open_px,
        CAST(close AS DOUBLE) AS close_px
      FROM read_parquet({expr}, union_by_name=true)
      WHERE UPPER(CAST(underlying AS VARCHAR))='NIFTY'
        AND TRY_CAST(expiry AS DATE)=DATE '{expiry}'
        AND CAST(strike AS DOUBLE)={float(strike)}
        AND UPPER(CAST(option_type AS VARCHAR))='{side}'
        AND CAST(timestamp AS TIMESTAMP) BETWEEN TIMESTAMP '{start_ts}' AND TIMESTAMP '{end_ts}'
        AND close > 0
      ORDER BY ts
    """
    x = con.execute(q).df()
    if x.empty:
        return pd.DataFrame(columns=["ts", "open_px", "close_px"])
    x["ts"] = pd.to_datetime(x["ts"]).dt.floor("min")
    return x.drop_duplicates("ts").sort_values("ts")


def strike_universe(con, files, trade_date, expiry):
    expr = parquet_expr(files)
    q = f"""
      SELECT DISTINCT
        CAST(strike AS DOUBLE) AS strike,
        UPPER(CAST(option_type AS VARCHAR)) AS option_type
      FROM read_parquet({expr}, union_by_name=true)
      WHERE UPPER(CAST(underlying AS VARCHAR))='NIFTY'
        AND CAST(date AS DATE)=DATE '{trade_date}'
        AND TRY_CAST(expiry AS DATE)=DATE '{expiry}'
    """
    return con.execute(q).df()


def open_at(df, side, strike, ts):
    x = df[(df.option_type == side) & (df.strike == float(strike)) & (df.ts == pd.Timestamp(ts))]
    if x.empty or pd.isna(x.iloc[0].open_px) or x.iloc[0].open_px <= 0:
        return None
    return float(x.iloc[0].open_px)


def select_target(chain, side, target, ref_strike=None, far_otm=False):
    x = chain[chain.option_type == side].copy()
    if ref_strike is not None:
        if far_otm:
            if side == "CE":
                x = x[x.strike >= float(ref_strike)]
            else:
                x = x[x.strike <= float(ref_strike)]
        else:
            x = x[x.strike == float(ref_strike)]
    x = x[x.open_px.notna() & (x.open_px > 0)]
    if x.empty:
        return None
    x["dist"] = (x.close_px - float(target)).abs()
    return x.sort_values(["dist", "strike"]).iloc[0]


def choose_wings(strikes, short_ce, short_pe):
    ce = np.sort(np.asarray(strikes["CE"], dtype=float))
    pe = np.sort(np.asarray(strikes["PE"], dtype=float))
    ce_w = ce[ce > float(short_ce)]
    pe_w = pe[pe < float(short_pe)]
    if len(ce_w) == 0 or len(pe_w) == 0:
        return None, None
    return float(ce_w[0]), float(pe_w[-1])


def mark_panel(series_map, tolerance_minutes=1):
    base = None
    for name, s in series_map.items():
        z = s[["ts", "close_px"]].rename(columns={"close_px": name}).sort_values("ts")
        if base is None:
            base = z
        else:
            base = pd.merge_asof(
                base.sort_values("ts"),
                z,
                on="ts",
                direction="backward",
                tolerance=pd.Timedelta(minutes=tolerance_minutes),
            )
    if base is None:
        return pd.DataFrame()
    return base.dropna().sort_values("ts")


def next_open(series, after_ts):
    z = series[series.ts >= pd.Timestamp(after_ts)]
    return None if z.empty else z.iloc[0]


def cost(legs, lot, slippage, entry_date=None, exit_date=None):
    turnover = sum((leg["entry"] + leg["exit"]) * leg["qty"] * lot for leg in legs)
    sell_entry = sum(leg["entry"] * leg["qty"] * lot for leg in legs if leg["sign"] < 0)
    sell_exit = sum(leg["exit"] * leg["qty"] * lot for leg in legs if leg["sign"] > 0)
    buy_entry = sum(leg["entry"] * leg["qty"] * lot for leg in legs if leg["sign"] > 0)
    buy_exit = sum(leg["exit"] * leg["qty"] * lot for leg in legs if leg["sign"] < 0)
    brokerage = 40.0 * len(legs)
    exchange_rate = 0.0003503 if (entry_date is None or pd.Timestamp(entry_date).date() < date(2026, 3, 1)) else 0.000355299
    exchange = turnover * exchange_rate
    sebi = turnover * 0.000001
    entry_stt_rate = 0.001 if entry_date is None or pd.Timestamp(entry_date).date() < date(2026, 4, 1) else 0.0015
    exit_stt_rate = 0.001 if exit_date is None or pd.Timestamp(exit_date).date() < date(2026, 4, 1) else 0.0015
    stt = sell_entry * entry_stt_rate + sell_exit * exit_stt_rate
    stamp = (buy_entry + buy_exit) * 0.00003
    gst = 0.18 * (brokerage + exchange + sebi)
    slip = 2.0 * slippage * sum(leg["qty"] * lot for leg in legs)
    return brokerage + exchange + sebi + stt + stamp + gst + slip


def settle(legs, lot, slippage, entry_date=None, exit_date=None):
    gross = sum(leg["sign"] * (leg["exit"] - leg["entry"]) * leg["qty"] * lot for leg in legs)
    return gross - cost(legs, lot, slippage, entry_date=entry_date, exit_date=exit_date)


def build_setup(con, files, schedule, entry_time, target, far_mode):
    entry_date = schedule["entry_date"]
    near_exp = schedule["near_expiry"]
    far_exp = schedule["far_expiry"]
    t = pd.Timestamp(f"{entry_date} {entry_time}")
    fill_t = t + pd.Timedelta(minutes=1)
    chain = load_entry_chain(con, files, entry_date, t, fill_t, [near_exp, far_exp])
    if chain.empty:
        return None
    near_close = chain[(chain.expiry == near_exp) & (chain.ts == t)]
    near_fill = chain[(chain.expiry == near_exp) & (chain.ts == fill_t)]
    far_close = chain[(chain.expiry == far_exp) & (chain.ts == t)]
    far_fill = chain[(chain.expiry == far_exp) & (chain.ts == fill_t)]
    if near_close.empty or near_fill.empty or far_close.empty or far_fill.empty:
        return None

    sce = select_target(near_close, "CE", target)
    spe = select_target(near_close, "PE", target)
    if sce is None or spe is None:
        return None
    if far_mode == "SAME_STRIKE":
        fce = select_target(far_close, "CE", target, ref_strike=sce.strike)
        fpe = select_target(far_close, "PE", target, ref_strike=spe.strike)
    else:
        fce = select_target(far_close, "CE", target, ref_strike=sce.strike, far_otm=True)
        fpe = select_target(far_close, "PE", target, ref_strike=spe.strike, far_otm=True)
    if fce is None or fpe is None:
        return None
    sc_e = open_at(near_fill, "CE", sce.strike, fill_t)
    sp_e = open_at(near_fill, "PE", spe.strike, fill_t)
    fc_e = open_at(far_fill, "CE", fce.strike, fill_t)
    fp_e = open_at(far_fill, "PE", fpe.strike, fill_t)
    if None in (sc_e, sp_e, fc_e, fp_e):
        return None
    initial_credit = 5.0 * (sc_e + sp_e) - 3.0 * (fc_e + fp_e)
    if not np.isfinite(initial_credit) or initial_credit <= 0:
        return None
    return {
        "trade_date": entry_date,
        "entry_ts": t,
        "entry_fill_ts": fill_t,
        "adjust_date": schedule["adjust_date"],
        "exit_date": schedule["exit_date"],
        "near_expiry": near_exp,
        "far_expiry": far_exp,
        "short_ce_strike": float(sce.strike),
        "short_pe_strike": float(spe.strike),
        "far_ce_strike": float(fce.strike),
        "far_pe_strike": float(fpe.strike),
        "short_ce_entry": sc_e,
        "short_pe_entry": sp_e,
        "far_ce_entry": fc_e,
        "far_pe_entry": fp_e,
        "initial_credit": float(initial_credit),
        "target_premium": float(target),
        "far_mode": far_mode,
    }


def simulate_setup(con, files, setup, variant, slippage):
    entry_date = setup["trade_date"]
    lot = lot_size(setup["near_expiry"])
    start = setup["entry_fill_ts"]
    adjust_date = setup["adjust_date"]
    exit_date = setup["exit_date"]
    end = pd.Timestamp(f"{exit_date} 15:15:00")
    cache = setup.setdefault("_cache", {})

    if "initial" not in cache:
        cache["initial"] = {
            "short_ce": load_series(con, files, setup["near_expiry"], setup["short_ce_strike"], "CE", start, end),
            "short_pe": load_series(con, files, setup["near_expiry"], setup["short_pe_strike"], "PE", start, end),
            "far_ce": load_series(con, files, setup["far_expiry"], setup["far_ce_strike"], "CE", start, end),
            "far_pe": load_series(con, files, setup["far_expiry"], setup["far_pe_strike"], "PE", start, end),
        }
    initial = cache["initial"]
    if any(v.empty for v in initial.values()):
        return None

    if "wings" not in cache:
        strikes_df = strike_universe(con, files, entry_date, setup["near_expiry"])
        ce = strikes_df.loc[strikes_df.option_type == "CE", "strike"].tolist()
        pe = strikes_df.loc[strikes_df.option_type == "PE", "strike"].tolist()
        wing_ce, wing_pe = choose_wings({"CE": ce, "PE": pe}, setup["short_ce_strike"], setup["short_pe_strike"])
        cache["wings"] = (wing_ce, wing_pe)
    wing_ce, wing_pe = cache["wings"]
    if wing_ce is None or wing_pe is None:
        return None

    if "pre_panel" not in cache:
        cache["pre_panel"] = mark_panel(initial, tolerance_minutes=1)
    combined = cache["pre_panel"]
    pre_stop_ts = None
    for row in combined.itertuples(index=False):
        if row.ts < start or row.ts >= pd.Timestamp(f"{adjust_date} {variant.adjust_time}"):
            continue
        pnl_points = setup["initial_credit"] - 5 * row.short_ce - 5 * row.short_pe + 3 * row.far_ce + 3 * row.far_pe
        if pnl_points <= -variant.stop_multiple * setup["initial_credit"]:
            pre_stop_ts = row.ts
            break

    base_legs = [
        {"name":"short_ce", "entry":setup["short_ce_entry"], "exit":None, "sign":-1, "qty":5},
        {"name":"short_pe", "entry":setup["short_pe_entry"], "exit":None, "sign":-1, "qty":5},
        {"name":"far_ce", "entry":setup["far_ce_entry"], "exit":None, "sign":1, "qty":3},
        {"name":"far_pe", "entry":setup["far_pe_entry"], "exit":None, "sign":1, "qty":3},
    ]

    if pre_stop_ts is not None:
        for leg in base_legs:
            row = next_open(initial[leg["name"]], pre_stop_ts + pd.Timedelta(minutes=1))
            if row is None:
                return None
            leg["exit"] = float(row.open_px)
        exit_ts = pre_stop_ts + pd.Timedelta(minutes=1)
        return {
            "reason":"STOP_PRE_ADJUST",
            "exit_ts":exit_ts,
            "net_pnl":settle(base_legs, lot, slippage, entry_date=entry_date, exit_date=exit_ts.date()),
            "active_legs":4,
        }

    adjust_signal = pd.Timestamp(f"{adjust_date} {variant.adjust_time}")
    adjust_exec = adjust_signal + pd.Timedelta(minutes=1)
    key = (variant.adjust_time, wing_ce, wing_pe)
    adjustments = cache.setdefault("adjustments", {})
    if key not in adjustments:
        wing_series_ce = load_series(con, files, setup["near_expiry"], wing_ce, "CE", adjust_exec, end)
        wing_series_pe = load_series(con, files, setup["near_expiry"], wing_pe, "PE", adjust_exec, end)
        if wing_series_ce.empty or wing_series_pe.empty:
            return None
        ce_row = next_open(wing_series_ce, adjust_exec)
        pe_row = next_open(wing_series_pe, adjust_exec)
        if ce_row is None or pe_row is None:
            return None
        post = mark_panel({
            "short_ce":initial["short_ce"],
            "short_pe":initial["short_pe"],
            "far_ce":initial["far_ce"],
            "far_pe":initial["far_pe"],
            "wing_ce":wing_series_ce,
            "wing_pe":wing_series_pe,
        }, tolerance_minutes=1)
        adjustments[key] = {
            "wing_series_ce":wing_series_ce,
            "wing_series_pe":wing_series_pe,
            "wing_ce_entry":float(ce_row.open_px),
            "wing_pe_entry":float(pe_row.open_px),
            "post":post[post.ts >= adjust_exec].copy(),
        }
    adj = adjustments[key]
    wing_series_ce = adj["wing_series_ce"]
    wing_series_pe = adj["wing_series_pe"]
    wing_ce_entry = adj["wing_ce_entry"]
    wing_pe_entry = adj["wing_pe_entry"]

    legs = base_legs + [
        {"name":"wing_ce", "entry":wing_ce_entry, "exit":None, "sign":1, "qty":5},
        {"name":"wing_pe", "entry":wing_pe_entry, "exit":None, "sign":1, "qty":5},
    ]
    stop_ts = None
    for row in adj["post"].itertuples(index=False):
        pnl_points = (
            setup["initial_credit"] - 5 * row.short_ce - 5 * row.short_pe
            + 3 * row.far_ce + 3 * row.far_pe
            + 5 * row.wing_ce + 5 * row.wing_pe
            - 5 * wing_ce_entry - 5 * wing_pe_entry
        )
        if pnl_points <= -variant.stop_multiple * setup["initial_credit"]:
            stop_ts = row.ts
            break

    exit_signal = stop_ts if stop_ts is not None else pd.Timestamp(f"{exit_date} 15:15:00")
    exit_from = exit_signal + pd.Timedelta(minutes=1)
    for leg in legs:
        if leg["name"] == "wing_ce":
            s = wing_series_ce
        elif leg["name"] == "wing_pe":
            s = wing_series_pe
        else:
            s = initial[leg["name"]]
        row = next_open(s, exit_from)
        if row is None:
            z = s[s.ts <= exit_signal].tail(1)
            if z.empty:
                return None
            leg["exit"] = float(z.iloc[0].close_px)
        else:
            leg["exit"] = float(row.open_px)

    return {
        "reason":"STOP_POST_ADJUST" if stop_ts is not None else "PRE_EXPIRY_EXIT",
        "exit_ts":exit_signal,
        "net_pnl":settle(legs, lot, slippage, entry_date=entry_date, exit_date=exit_signal.date()),
        "active_legs":6,
    }


def summarize(trades, out, slippage, n_setups):
    out.mkdir(parents=True, exist_ok=True)
    if trades.empty:
        summary = {"variants":270, "setups":n_setups, "trades":0, "positive_variants":0, "target_qualified":0, "best":None, "slippage":slippage}
        (out / "phase24b_summary.json").write_text(json.dumps(summary, indent=2, default=str))
        return summary
    trades.to_csv(out / "phase24b_trades.csv", index=False)
    daily = trades.groupby(["variant_id", "trade_date"], as_index=False).net_pnl.sum()
    rows = []
    for variant_id, group in daily.groupby("variant_id"):
        vals = group.net_pnl.astype(float)
        wins = float((vals > 0).mean())
        gross_win = float(vals[vals > 0].sum())
        gross_loss = float(-vals[vals < 0].sum())
        pf = gross_win / gross_loss if gross_loss > 0 else float("inf")
        curve = vals.cumsum()
        dd = curve - curve.cummax()
        rows.append({
            "variant_id":variant_id,
            "active_days":int(len(vals)),
            "trades":int((trades.variant_id == variant_id).sum()),
            "mean_active_day_net":float(vals.mean()),
            "median_active_day_net":float(vals.median()),
            "win_rate":wins,
            "profit_factor":pf,
            "max_drawdown":float(dd.min()),
        })
    board = pd.DataFrame(rows).sort_values("mean_active_day_net", ascending=False)
    board["target_qualified"] = board.mean_active_day_net >= 1000.0
    board.to_csv(out / "phase24b_leaderboard.csv", index=False)
    by_year = trades.assign(year=pd.to_datetime(trades.trade_date).dt.year).groupby(["variant_id","year"],as_index=False).net_pnl.sum()
    by_year.to_csv(out / "phase24b_yearly_net.csv", index=False)
    best = board.iloc[0].to_dict() if not board.empty else None
    summary = {
        "variants":270,
        "setups":n_setups,
        "trades":int(len(trades)),
        "positive_variants":int((board.mean_active_day_net > 0).sum()),
        "target_qualified":int(board.target_qualified.sum()),
        "best":best,
        "slippage":slippage,
    }
    (out / "phase24b_summary.json").write_text(json.dumps(summary, indent=2, default=str))
    return summary


def run(data: Path, out: Path, slippage: float):
    report = coverage_report(data)
    print(json.dumps({"coverage":report}, indent=2, default=str))
    if not report["coverage_ok"]:
        raise RuntimeError("Rissin coverage preflight failed; no P&L stage allowed")
    con, files = connect(data)
    schedules, _, _ = executable_schedules(con, files)
    variants = variant_grid()
    setups = []
    for sched in schedules:
        for entry_time in ENTRY_TIMES:
            for target in TARGET_PREMIUMS:
                for far_mode in FAR_MODES:
                    setup = build_setup(con, files, sched, entry_time, target, far_mode)
                    if setup is not None:
                        setup["schedule_key"] = (sched["entry_date"], sched["near_expiry"], sched["far_expiry"], entry_time, target, far_mode)
                        setups.append(setup)
    rows = []
    errors = []
    by_setup = {}
    for setup in setups:
        key = setup["schedule_key"]
        by_setup.setdefault(key, []).append(setup)
    for setup in setups:
        entry_time = pd.Timestamp(setup["entry_ts"]).strftime("%H:%M:%S")
        for variant in variants:
            if variant.entry_time != entry_time:
                continue
            if variant.target_premium != setup["target_premium"] or variant.far_mode != setup["far_mode"]:
                continue
            try:
                result = simulate_setup(con, files, setup, variant, slippage)
            except Exception as exc:
                errors.append({"trade_date":str(setup["trade_date"]), "variant_id":variant.variant_id, "error":repr(exc)})
                result = None
            if result is not None:
                rows.append({
                    "variant_id":variant.variant_id,
                    "trade_date":setup["trade_date"],
                    "entry_ts":setup["entry_ts"],
                    "near_expiry":setup["near_expiry"],
                    "far_expiry":setup["far_expiry"],
                    "short_ce_strike":setup["short_ce_strike"],
                    "short_pe_strike":setup["short_pe_strike"],
                    "far_ce_strike":setup["far_ce_strike"],
                    "far_pe_strike":setup["far_pe_strike"],
                    **result,
                })
    con.close()
    out.mkdir(parents=True, exist_ok=True)
    if errors:
        (out / "phase24b_sim_errors.json").write_text(json.dumps(errors[:200], indent=2, default=str))
    trades = pd.DataFrame(rows)
    return summarize(trades, out, slippage, len(setups))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=Path("reports/base"))
    ap.add_argument("--slippage", type=float, default=0.20)
    ap.add_argument("--coverage-only", action="store_true")
    args = ap.parse_args()
    report = coverage_report(args.data)
    print(json.dumps(report, indent=2, default=str))
    if args.coverage_only:
        if not report["coverage_ok"]:
            raise SystemExit(2)
    else:
        print(json.dumps(run(args.data, args.out, args.slippage), indent=2, default=str))