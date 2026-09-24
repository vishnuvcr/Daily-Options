
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

ENTRY_TIMES = ("09:30:00", "10:00:00", "11:00:00", "13:00:00", "14:00:00")
TARGET_PREMIUMS = (20.0, 25.0, 30.0)
FAR_MODES = ("DIAGONAL_PREMIUM", "SAME_STRIKE")
ADJUST_TIMES = ("09:30:00", "10:00:00", "11:00:00")
STOP_MULTIPLES = (0.50, 1.00, 1.50)
START_DATE = "2021-07-01"
END_DATE = "2026-08-04"


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
    if d < pd.Timestamp("2021-07-01").date():
        return 75
    if d < pd.Timestamp("2024-04-26").date():
        return 50
    if d < pd.Timestamp("2024-11-21").date():
        return 25
    if d < pd.Timestamp("2026-01-06").date():
        return 75
    return 65


def expiry_files(root: Path):
    out = []
    for p in sorted((root / "options" / "NIFTY").glob("*.parquet")):
        try:
            out.append((pd.Timestamp(p.stem).date(), p))
        except Exception:
            continue
    if not out:
        raise FileNotFoundError(f"no exact-expiry files in {root/'options'/'NIFTY'}")
    return out


def next_two_expiries(files, trade_date):
    td = pd.Timestamp(trade_date).date()
    fut = [(d, p) for d, p in files if d >= td]
    return (fut[0], fut[1]) if len(fut) >= 2 else None


def open_at(df, side, strike, ts):
    x = df[
        (df.option_type == side)
        & (df.strike == float(strike))
        & (df.ts == pd.Timestamp(ts))
    ]
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


def load_chain_minute(con, path, trade_date, start_ts, end_ts=None):
    end_clause = (
        f"AND CAST(timestamp AS TIMESTAMP) <= TIMESTAMP '{end_ts}'"
        if end_ts is not None else ""
    )
    q = f"""
      SELECT CAST(timestamp AS TIMESTAMP) ts,
             CAST(strike AS DOUBLE) strike,
             UPPER(CAST(option_type AS VARCHAR)) option_type,
             CAST(open AS DOUBLE) open_px,
             CAST(close AS DOUBLE) close_px
      FROM read_parquet('{path}')
      WHERE CAST(trading_day AS DATE)=DATE '{trade_date}'
        AND CAST(timestamp AS TIMESTAMP) >= TIMESTAMP '{start_ts}'
        {end_clause}
        AND close > 0
      ORDER BY ts, strike, option_type
    """
    return con.execute(q).df()


def load_candidate_spot(root):
    p = root / "index" / "NIFTY.parquet"
    con = duckdb.connect()
    con.execute("SET TimeZone='Asia/Kolkata'")
    q = f"""
      WITH d AS (
        SELECT DISTINCT
          CAST(trading_day AS DATE) AS trade_date
        FROM read_parquet('{p}')
        WHERE CAST(trading_day AS DATE) BETWEEN DATE '{START_DATE}' AND DATE '{END_DATE}'
      ),
      r AS (
        SELECT trade_date,
               ROW_NUMBER() OVER (ORDER BY trade_date) AS session_no
        FROM d
      )
      SELECT trade_date,
             session_no
      FROM r
      ORDER BY trade_date
    """
    sessions = con.execute(q).df()
    if sessions.empty:
        con.close()
        return sessions
    sessions["trade_date"] = pd.to_datetime(sessions["trade_date"]).dt.date
    con.close()
    return sessions


def build_setup(con, root, entry_row, target, far_mode, files):
    entry_date = pd.Timestamp(entry_row.trade_date).date()
    chosen = next_two_expiries(files, entry_date)
    if not chosen:
        return None
    (near_exp, near_path), (far_exp, far_path) = chosen

    # Preserve the source strategy's time-to-expiry geometry across the NSE
    # expiry-day change:
    #   old Thursday regime: Friday entry -> Monday adjustment -> Wednesday exit
    #   current Tuesday regime: Wednesday entry -> Friday adjustment -> Monday exit
    # In trading-session offsets this is:
    #   entry = expiry - 4 sessions
    #   adjustment = expiry - 2 sessions
    #   exit = expiry - 1 session
    session_q = f"""
      SELECT DISTINCT CAST(trading_day AS DATE) AS trade_date
      FROM read_parquet('{root / "index" / "NIFTY.parquet"}')
      WHERE CAST(trading_day AS DATE) <= DATE '{near_exp}'
        AND CAST(trading_day AS DATE) >= DATE '{START_DATE}'
      ORDER BY trade_date
    """
    session_df = con.execute(session_q).df()
    session_dates = [pd.Timestamp(x).date() for x in session_df["trade_date"].tolist()]
    expiry_date = pd.Timestamp(near_exp).date()
    prior = [d for d in session_dates if d < expiry_date]
    if len(prior) < 4:
        return None
    entry_expected = prior[-4]
    adjust_date = prior[-2]
    exit_date = prior[-1]
    if entry_expected != entry_date:
        return None

    candidate_times = entry_row
    t = pd.Timestamp(f"{entry_date} {candidate_times.entry_time}")
    fill_t = t + pd.Timedelta(minutes=1)

    near = load_chain_minute(con, near_path, entry_date, t, fill_t)
    far = load_chain_minute(con, far_path, entry_date, t, fill_t)
    if near.empty or far.empty:
        return None

    near_close = near[near.ts == t]
    near_fill = near[near.ts == fill_t]
    far_close = far[far.ts == t]
    far_fill = far[far.ts == fill_t]
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
        "adjust_date": adjust_date,
        "exit_date": exit_date,
        "near_expiry": near_exp,
        "far_expiry": far_exp,
        "near_path": str(near_path),
        "far_path": str(far_path),
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


def series(con, path, trade_date, strike, side, start_ts, end_ts):
    q = f"""
      SELECT CAST(timestamp AS TIMESTAMP) ts,
             CAST(open AS DOUBLE) open_px,
             CAST(close AS DOUBLE) close_px
      FROM read_parquet('{path}')
      WHERE CAST(timestamp AS TIMESTAMP) BETWEEN TIMESTAMP '{start_ts}' AND TIMESTAMP '{end_ts}'
        AND CAST(strike AS DOUBLE)={float(strike)}
        AND UPPER(CAST(option_type AS VARCHAR))='{side}'
        AND close > 0
      ORDER BY ts
    """
    x = con.execute(q).df()
    if x.empty:
        return pd.DataFrame(columns=["ts","open_px","close_px"])
    x["ts"] = pd.to_datetime(x.ts).dt.floor("min")
    return x.drop_duplicates("ts").sort_values("ts")


def next_open(s, after_ts):
    z = s[s.ts >= pd.Timestamp(after_ts)]
    return None if z.empty else z.iloc[0]


def mark_panel(series_map, tolerance_minutes=1):
    """Build a leakage-safe common mark panel using backward as-of joins only."""
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


def cost(legs, lot, slippage):
    turnover = sum((leg["entry"] + leg["exit"]) * leg["qty"] * lot for leg in legs)
    sell_entry = sum(leg["entry"] * leg["qty"] * lot for leg in legs if leg["sign"] < 0)
    sell_exit = sum(leg["exit"] * leg["qty"] * lot for leg in legs if leg["sign"] > 0)
    buy_entry = sum(leg["entry"] * leg["qty"] * lot for leg in legs if leg["sign"] > 0)
    buy_exit = sum(leg["exit"] * leg["qty"] * lot for leg in legs if leg["sign"] < 0)
    brokerage = 40.0 * len(legs)
    exchange = turnover * 0.0003503
    sebi = turnover * 0.000001
    stt = (sell_entry + sell_exit) * 0.0015
    stamp = (buy_entry + buy_exit) * 0.00003
    gst = 0.18 * (brokerage + exchange + sebi)
    slip = 2.0 * slippage * sum(leg["qty"] * lot for leg in legs)
    return brokerage + exchange + sebi + stt + stamp + gst + slip


def settle(legs, lot, slippage):
    gross = sum(
        leg["sign"] * (leg["exit"] - leg["entry"]) * leg["qty"] * lot
        for leg in legs
    )
    return gross - cost(legs, lot, slippage)


def simulate_setup(con, setup, variant, slippage):
    entry_date = setup["trade_date"]
    near = Path(setup["near_path"])
    far = Path(setup["far_path"])
    lot = lot_size(setup["near_expiry"])
    start = setup["entry_fill_ts"]
    adjust_date = setup["adjust_date"]
    exit_date = setup["exit_date"]
    end = pd.Timestamp(f"{exit_date} 15:15:00")
    initial = {
        "short_ce": series(con, near, entry_date, setup["short_ce_strike"], "CE", start, end),
        "short_pe": series(con, near, entry_date, setup["short_pe_strike"], "PE", start, end),
        "far_ce": series(con, far, entry_date, setup["far_ce_strike"], "CE", start, end),
        "far_pe": series(con, far, entry_date, setup["far_pe_strike"], "PE", start, end),
    }
    if any(v.empty for v in initial.values()):
        return None

    adjust_signal = pd.Timestamp(f"{adjust_date} {variant.adjust_time}")
    adjust_exec = adjust_signal + pd.Timedelta(minutes=1)

    # One listed strike outside the original short on the same weekly expiry.
    strike_q = f"""
      SELECT DISTINCT CAST(strike AS DOUBLE) strike, UPPER(CAST(option_type AS VARCHAR)) option_type
      FROM read_parquet('{near}')
      WHERE CAST(trading_day AS DATE)=DATE '{friday}'
    """
    strikes = con.execute(strike_q).df()
    ce = np.sort(strikes.loc[strikes.option_type=="CE","strike"].unique())
    pe = np.sort(strikes.loc[strikes.option_type=="PE","strike"].unique())
    ce_w = ce[ce > setup["short_ce_strike"]]
    pe_w = pe[pe < setup["short_pe_strike"]]
    if len(ce_w) == 0 or len(pe_w) == 0:
        return None
    wing_ce = float(ce_w[0])
    wing_pe = float(pe_w[-1])

    wing_series_ce = series(con, near, adjust_date, wing_ce, "CE", adjust_exec, end)
    wing_series_pe = series(con, near, adjust_date, wing_pe, "PE", adjust_exec, end)
    if wing_series_ce.empty or wing_series_pe.empty:
        return None

    wing_ce_row = next_open(wing_series_ce, adjust_exec)
    wing_pe_row = next_open(wing_series_pe, adjust_exec)
    if wing_ce_row is None or wing_pe_row is None:
        return None

    base_legs = [
        {"name":"short_ce","entry":setup["short_ce_entry"],"exit":None,"sign":-1,"qty":5},
        {"name":"short_pe","entry":setup["short_pe_entry"],"exit":None,"sign":-1,"qty":5},
        {"name":"far_ce","entry":setup["far_ce_entry"],"exit":None,"sign":1,"qty":3},
        {"name":"far_pe","entry":setup["far_pe_entry"],"exit":None,"sign":1,"qty":3},
    ]

    # Pre-adjustment stop, evaluated on close MTM and executed at the next available open.
    # One-minute quote series can have occasional missing bars, so use backward as-of
    # alignment with a fixed one-minute tolerance; never use a future quote.
    combined = mark_panel(initial, tolerance_minutes=1)
    pre_stop_ts = None
    for row in combined.itertuples(index=False):
        if row.ts < start or row.ts >= adjust_signal:
            continue
        pnl_points = (
            setup["initial_credit"]
            - 5*getattr(row,"short_ce")
            - 5*getattr(row,"short_pe")
            + 3*getattr(row,"far_ce")
            + 3*getattr(row,"far_pe")
        )
        if pnl_points <= -variant.stop_multiple * setup["initial_credit"]:
            pre_stop_ts = row.ts
            break

    if pre_stop_ts is not None:
        ex = {}
        for leg in base_legs:
            s = initial[leg["name"]]
            row = next_open(s, pre_stop_ts + pd.Timedelta(minutes=1))
            if row is None:
                return None
            ex[leg["name"]] = float(row.open_px)
            leg["exit"] = ex[leg["name"]]
        pnl = settle(base_legs, lot, slippage)
        return {"reason":"STOP_PRE_ADJUST","exit_ts":pre_stop_ts + pd.Timedelta(minutes=1),"net_pnl":pnl,"active_legs":4}

    wing_entries = {"wing_ce":float(wing_ce_row.open_px),"wing_pe":float(wing_pe_row.open_px)}
    legs = base_legs + [
        {"name":"wing_ce","entry":wing_entries["wing_ce"],"exit":None,"sign":1,"qty":5},
        {"name":"wing_pe","entry":wing_entries["wing_pe"],"exit":None,"sign":1,"qty":5},
    ]
    post = mark_panel({
        "short_ce": initial["short_ce"],
        "short_pe": initial["short_pe"],
        "far_ce": initial["far_ce"],
        "far_pe": initial["far_pe"],
        "wing_ce": wing_series_ce,
        "wing_pe": wing_series_pe,
    }, tolerance_minutes=1)
    post = post[post.ts >= adjust_exec].copy()
    stop_ts = None
    for row in post.itertuples(index=False):
        pnl_points = (
            setup["initial_credit"]
            - 5*row.short_ce - 5*row.short_pe
            + 3*row.far_ce + 3*row.far_pe
            + 5*row.wing_ce + 5*row.wing_pe
            - 5*wing_entries["wing_ce"] - 5*wing_entries["wing_pe"]
        )
        if pnl_points <= -variant.stop_multiple * setup["initial_credit"]:
            stop_ts = row.ts
            break

    # Exit on the last available pre-expiry session. Under today's NIFTY
    # Tuesday expiry this is Monday, avoiding 0-DTE Tuesday exposure.
    exit_signal = stop_ts if stop_ts is not None else pd.Timestamp(f"{exit_date} 15:15:00")
    exit_from = exit_signal + pd.Timedelta(minutes=1)
    for leg in legs:
        s = (
            wing_series_ce if leg["name"]=="wing_ce"
            else wing_series_pe if leg["name"]=="wing_pe"
            else initial[leg["name"]]
        )
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
        "net_pnl":settle(legs, lot, slippage),
        "active_legs":6,
    }


def run(data: Path, out: Path, slippage: float):
    out.mkdir(parents=True, exist_ok=True)
    variants = variant_grid()
    candidates = load_candidate_spot(data)
    if candidates.empty:
        raise RuntimeError("no Friday candidate rows")

    files = expiry_files(data)
    con = duckdb.connect()
    con.execute("SET TimeZone='Asia/Kolkata'")
    setups = {}
    for row in candidates.itertuples(index=False):
        for entry_time in ENTRY_TIMES:
            row_with_time = type("EntryRow", (), {
                "trade_date": row.trade_date,
                "entry_time": entry_time,
            })
            for target in TARGET_PREMIUMS:
                for far_mode in FAR_MODES:
                    s = build_setup(con, data, row_with_time, target, far_mode, files)
                    if s:
                        setups[(row.trade_date, entry_time, target, far_mode)] = s

    rows = []
    errors = []
    for setup in setups.values():
        for v in variants:
            if v.entry_time != pd.Timestamp(setup["entry_ts"]).strftime("%H:%M:%S"):
                continue
            if v.target_premium != setup["target_premium"] or v.far_mode != setup["far_mode"]:
                continue
            try:
                result = simulate_setup(con, setup, v, slippage)
            except Exception as exc:
                errors.append({"trade_date": str(setup["trade_date"]), "variant_id": v.variant_id, "error": repr(exc)})
                result = None
            if result is not None:
                rows.append({
                    "variant_id":v.variant_id,
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

    if errors:
        (out/"phase24_sim_errors.json").write_text(json.dumps(errors[:100], indent=2, default=str))
    trades = pd.DataFrame(rows)
    if trades.empty:
        summary = {"variants":len(variants),"setups":len(setups),"trades":0,
                   "target_qualified":0,"positive_variants":0,"best":None,
                   "slippage":slippage}
        (out/"phase24_summary.json").write_text(json.dumps(summary,indent=2,default=str))
        return summary

    trades.to_csv(out/"phase24_trades.csv",index=False)
    daily = trades.groupby(["variant_id","trade_date"],as_index=False).net_pnl.sum()
    board = trades.groupby("variant_id").agg(
        trades=("net_pnl","size"),
        total_net=("net_pnl","sum"),
        mean_trade=("net_pnl","mean"),
        win_rate=("net_pnl",lambda x:float((x>0).mean())),
    ).reset_index()
    stats = daily.groupby("variant_id").net_pnl.agg(["mean","median"]).reset_index()
    stats = stats.rename(columns={"mean":"mean_active_day_net","median":"median_active_day_net"})
    board = board.merge(stats,on="variant_id")
    board["target_qualified"] = board.mean_active_day_net >= 1000
    board = board.sort_values("mean_active_day_net",ascending=False)
    board.to_csv(out/"phase24_leaderboard.csv",index=False)
    best = board.iloc[0].to_dict() if not board.empty else None
    summary = {
        "variants":len(variants),
        "setups":len(setups),
        "trades":len(trades),
        "positive_variants":int((board.mean_active_day_net>0).sum()),
        "target_qualified":int(board.target_qualified.sum()),
        "best":best,
        "slippage":slippage,
    }
    (out/"phase24_summary.json").write_text(json.dumps(summary,indent=2,default=str))
    return summary


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--slippage", type=float, default=0.20)
    args = ap.parse_args()
    print(json.dumps(run(args.data,args.out,args.slippage),indent=2,default=str))
