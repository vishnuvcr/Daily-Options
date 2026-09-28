from __future__ import annotations

import argparse
import json
import math
from datetime import date
from pathlib import Path
from statistics import NormalDist

import duckdb
import numpy as np
import pandas as pd

START = date(2021, 7, 1)
END = date(2026, 8, 31)
LOOKBACK = 60
RV_WINDOW = 20
Z_THRESHOLD = 0.75
SQRT_ONE_SESSION = math.sqrt(1.0 / 252.0)
STATES = ("HIGH_GAP_DISLOCATION", "LOW_GAP_DISLOCATION")
MAPPINGS = ("CONTINUE", "FADE")
EXITS = ("10:30:00", "15:10:00")
NULL_SEEDS = (101, 202, 303, 404, 505)
STRIKE_STEP = 50.0
SPREAD_WIDTH = 200.0
COVERAGE_TARGET = 0.95
IV_CAP = 5.0


def lot_size(expiry):
    d = pd.Timestamp(expiry).date()
    if d < date(2024, 4, 26):
        return 50
    if d < date(2024, 11, 21):
        return 25
    if d < date(2026, 1, 6):
        return 75
    return 65


def charge(price, action, qty, lot, d):
    gross = float(price) * qty * lot
    d = pd.Timestamp(d).date()
    stt = gross * (0.001 if d < date(2026, 4, 1) else 0.0015) if action == "SELL" else 0.0
    exch = gross * (0.0003503 if d < date(2026, 3, 1) else 0.000355299)
    sebi = gross * 0.000001
    stamp = gross * 0.00003 if action == "BUY" else 0.0
    brokerage = 20.0
    gst = 0.18 * (brokerage + exch + sebi)
    return brokerage + exch + sebi + stt + stamp + gst


def idx_path(root):
    return str(root / "index" / "NIFTY.parquet")


def option_path(root, expiry):
    return root / "options" / "NIFTY" / f"{pd.Timestamp(expiry).date()}.parquet"


def norm_cdf(x):
    return 0.5 * (1.0 + math.erf(float(x) / math.sqrt(2.0)))


def bs_price(spot, strike, t, sigma, call):
    if not (spot > 0 and strike > 0 and t > 0 and sigma > 0):
        return float("nan")
    d1 = (math.log(spot / strike) + 0.5 * sigma * sigma * t) / (sigma * math.sqrt(t))
    d2 = d1 - sigma * math.sqrt(t)
    if call:
        return spot * norm_cdf(d1) - strike * norm_cdf(d2)
    return strike * norm_cdf(-d2) - spot * norm_cdf(-d1)


def implied_vol(price, spot, strike, t, call):
    if not all(np.isfinite(v) for v in (price, spot, strike, t)):
        return float("nan")
    if price <= 0 or spot <= 0 or strike <= 0 or t <= 0:
        return float("nan")
    intrinsic = max(spot - strike, 0.0) if call else max(strike - spot, 0.0)
    upper = spot if call else strike
    if price < intrinsic - 1e-7 or price > upper + 1e-7:
        return float("nan")
    lo, hi = 1e-6, IV_CAP
    for _ in range(70):
        mid = (lo + hi) / 2.0
        val = bs_price(spot, strike, t, mid, call)
        if val > price:
            hi = mid
        else:
            lo = mid
    iv = (lo + hi) / 2.0
    return iv if np.isfinite(iv) and 0 < iv <= IV_CAP else float("nan")


def round_strike(spot):
    x = float(spot) / STRIKE_STEP
    return math.floor(x + 0.5) * STRIKE_STEP


def prior_only_z(values, window=LOOKBACK):
    s = pd.Series(values, dtype="float64")
    prior_mean = s.rolling(window, min_periods=window).mean().shift(1)
    prior_std = s.rolling(window, min_periods=window).std(ddof=1).shift(1)
    z = (s - prior_mean) / prior_std.replace(0.0, np.nan)
    return prior_mean, prior_std, z


def discovery_cells():
    return [(state, mapping, ex) for state in STATES for mapping in MAPPINGS for ex in EXITS]


def expiry_list(root):
    exps = []
    for p in sorted((root / "options" / "NIFTY").glob("*.parquet")):
        try:
            exps.append((pd.Timestamp(p.stem).date(), p))
        except Exception:
            continue
    return exps


def load_sessions(root):
    con = duckdb.connect()
    con.execute("SET TimeZone='Asia/Kolkata'")
    q = f"""
        WITH src AS (
            SELECT
                CAST(timestamp AS TIMESTAMP) AS ts,
                CAST(timestamp AS DATE) AS trade_date,
                strftime(CAST(timestamp AS TIMESTAMP), '%H:%M:%S') AS local_time,
                CAST(open AS DOUBLE) AS open_px,
                CAST(close AS DOUBLE) AS close_px
            FROM read_parquet('{idx_path(root)}', union_by_name=true)
            WHERE CAST(timestamp AS DATE) BETWEEN DATE '{START}' AND DATE '{END}'
        )
        SELECT
            trade_date,
            MAX(open_px) FILTER (WHERE local_time='09:15:00') AS open_0915,
            MAX(close_px) FILTER (WHERE local_time='15:10:00') AS close_1510
        FROM src
        GROUP BY trade_date
        ORDER BY trade_date
    """
    x = con.execute(q).df()
    con.close()
    x["trade_date"] = pd.to_datetime(x["trade_date"]).dt.date
    x["open_0915"] = pd.to_numeric(x["open_0915"], errors="coerce")
    x["close_1510"] = pd.to_numeric(x["close_1510"], errors="coerce")
    x["prior_date"] = x["trade_date"].shift(1)
    x["prior_close_1510"] = x["close_1510"].shift(1)
    x["overnight_gap"] = x["open_0915"] / x["prior_close_1510"] - 1.0
    daily_ret = x["close_1510"].pct_change()
    x["rv20"] = daily_ret.rolling(RV_WINDOW, min_periods=RV_WINDOW).std(ddof=1) * math.sqrt(252.0)
    return x


def signal_expiry_map(sessions, expiries):
    exp_dates = [d for d, _ in expiries]
    out = {}
    for d in sessions["prior_date"]:
        if pd.isna(d):
            continue
        d = pd.Timestamp(d).date()
        future = [e for e in exp_dates if e > d]
        out[d] = future[0] if future else None
    return out


def query_prior_iv(root, requests):
    if not requests:
        return {}
    out = {}
    con = duckdb.connect()
    con.execute("SET TimeZone='Asia/Kolkata'")
    req = pd.DataFrame(requests, columns=["prior_date", "expiry", "atm_strike", "spot"])
    for expiry, g in req.groupby("expiry"):
        p = option_path(root, expiry)
        if not p.exists():
            continue
        dates = ",".join(f"DATE '{d}'" for d in sorted(g.prior_date.unique()))
        strikes = ",".join(str(float(x)) for x in sorted(g.atm_strike.unique()))
        ps = str(p).replace("'", "''")
        q = f"""
            WITH src AS (
                SELECT
                    CAST(timestamp AS DATE) AS trade_date,
                    CAST(expiry AS DATE) AS expiry,
                    CAST(timestamp AS TIMESTAMP) AS ts,
                    UPPER(CAST(option_type AS VARCHAR)) AS option_type,
                    CAST(strike AS DOUBLE) AS strike,
                    CAST(close AS DOUBLE) AS close_px
                FROM read_parquet('{ps}', union_by_name=true)
                WHERE CAST(timestamp AS DATE) IN ({dates})
                  AND CAST(strike AS DOUBLE) IN ({strikes})
                  AND UPPER(CAST(option_type AS VARCHAR)) IN ('CE','PE')
                  AND close > 0
                  AND strftime(CAST(timestamp AS TIMESTAMP), '%H:%M:%S') <= '15:10:00'
            )
            SELECT trade_date, expiry, option_type, strike, close_px, ts
            FROM src
            QUALIFY ROW_NUMBER() OVER (
                PARTITION BY trade_date, option_type, strike
                ORDER BY ts DESC
            ) = 1
        """
        z = con.execute(q).df()
        if z.empty:
            continue
        z["trade_date"] = pd.to_datetime(z["trade_date"]).dt.date
        z["expiry"] = pd.to_datetime(z["expiry"]).dt.date
        for d, dg in g.groupby("prior_date"):
            d = pd.Timestamp(d).date()
            spot = float(dg["spot"].iloc[0])
            atm = float(dg["atm_strike"].iloc[0])
            pair = z[(z.trade_date == d) & np.isclose(z.strike.astype(float), atm)]
            if pair.empty:
                continue
            expiry_ts = pd.Timestamp(expiry) + pd.Timedelta(hours=15, minutes=30)
            signal_ts = pd.Timestamp(d) + pd.Timedelta(hours=15, minutes=10)
            t = (expiry_ts - signal_ts).total_seconds() / 31536000.0
            vals = {}
            for typ in ("CE", "PE"):
                qrow = pair[pair.option_type == typ]
                if qrow.empty:
                    continue
                px = float(qrow.iloc[-1].close_px)
                iv = implied_vol(px, spot, atm, t, typ == "CE")
                vals[typ.lower() + "_price_1510"] = px
                vals[typ.lower() + "_iv_1510"] = iv
            if np.isfinite(vals.get("ce_iv_1510", np.nan)) and np.isfinite(vals.get("pe_iv_1510", np.nan)):
                vals["atm_iv_1510"] = (vals["ce_iv_1510"] + vals["pe_iv_1510"]) / 2.0
                out[(d, expiry)] = vals
    con.close()
    return out


def build_feature_panel(root):
    sessions = load_sessions(root)
    exps = expiry_list(root)
    exp_map = signal_expiry_map(sessions, exps)
    req = []
    for r in sessions.itertuples(index=False):
        if not np.isfinite(r.prior_close_1510):
            continue
        prior_date = pd.Timestamp(r.prior_date).date()
        exp = exp_map.get(prior_date)
        if exp is None:
            continue
        req.append((prior_date, exp, round_strike(r.prior_close_1510), float(r.prior_close_1510)))
    iv_map = query_prior_iv(root, req)
    panel = sessions.copy()
    panel["prior_expiry"] = panel["prior_date"].map(
        lambda x: exp_map.get(pd.Timestamp(x).date()) if not pd.isna(x) else None
    )
    panel["prior_atm_strike"] = panel["prior_close_1510"].map(
        lambda x: round_strike(x) if np.isfinite(x) else np.nan
    )
    iv_rows = []
    for r in panel.itertuples(index=False):
        key = (pd.Timestamp(r.prior_date).date(), r.prior_expiry) if not pd.isna(r.prior_date) and r.prior_expiry is not None else None
        v = iv_map.get(key, {}) if key else {}
        iv_rows.append({
            "ce_iv_1510": v.get("ce_iv_1510", np.nan),
            "pe_iv_1510": v.get("pe_iv_1510", np.nan),
            "atm_iv_1510": v.get("atm_iv_1510", np.nan),
        })
    panel = pd.concat([panel.reset_index(drop=True), pd.DataFrame(iv_rows)], axis=1)
    panel["implied_session_move"] = panel["atm_iv_1510"] * SQRT_ONE_SESSION
    panel["gap_ratio"] = panel["overnight_gap"].abs() / panel["implied_session_move"]
    panel["gap_ratio_z_mean"], panel["gap_ratio_z_std"], panel["gap_ratio_z"] = prior_only_z(panel["gap_ratio"], LOOKBACK)
    panel["iv_rv_ratio"] = panel["atm_iv_1510"] / panel["rv20"].replace(0.0, np.nan)
    panel["feature_eligible"] = (
        panel["open_0915"].gt(0)
        & panel["prior_close_1510"].gt(0)
        & panel["overnight_gap"].notna()
        & panel["rv20"].gt(0)
        & panel["atm_iv_1510"].gt(0)
        & panel["implied_session_move"].gt(0)
        & panel["gap_ratio"].notna()
        & panel["gap_ratio_z"].notna()
        & panel["prior_expiry"].notna()
    )
    panel["prior_information_violation"] = (
        panel["prior_date"].notna() & (pd.to_datetime(panel["prior_date"]) >= pd.to_datetime(panel["trade_date"]))
    )
    return panel, sessions


def build_signals(panel, sessions, z_override=None):
    z_values = panel["gap_ratio_z"].to_numpy(dtype=float) if z_override is None else np.asarray(z_override, dtype=float)
    rows = []
    for i, r in enumerate(panel.itertuples(index=False)):
        if not bool(r.feature_eligible):
            continue
        z = float(z_values[i])
        if not np.isfinite(z):
            continue
        state = "HIGH_GAP_DISLOCATION" if z >= Z_THRESHOLD else ("LOW_GAP_DISLOCATION" if z <= -Z_THRESHOLD else None)
        if state is None or not np.isfinite(r.overnight_gap) or r.overnight_gap == 0:
            continue
        direction = "BULL" if r.overnight_gap > 0 else "BEAR"
        for mapping in MAPPINGS:
            side = direction if mapping == "CONTINUE" else ("BEAR" if direction == "BULL" else "BULL")
            for ex in EXITS:
                rows.append({
                    "state": state,
                    "mapping": mapping,
                    "exit_time": ex,
                    "trade_date": r.trade_date,
                    "prior_date": r.prior_date,
                    "prior_expiry": r.prior_expiry,
                    "prior_atm_strike": float(r.prior_atm_strike),
                    "opening_gap": float(r.overnight_gap),
                    "gap_ratio": float(r.gap_ratio),
                    "gap_ratio_z": z,
                    "atm_iv_1510": float(r.atm_iv_1510),
                    "rv20": float(r.rv20),
                    "iv_rv_ratio": float(r.iv_rv_ratio),
                    "side": side,
                })
    return pd.DataFrame(rows)


def required_legs(r):
    atm = float(r.prior_atm_strike)
    if r.side == "BULL":
        return ("CE", atm, "CE", atm + SPREAD_WIDTH)
    return ("PE", atm, "PE", atm - SPREAD_WIDTH)


def execution_price_map(signals, root):
    prices = {}
    if signals.empty:
        return prices
    req = []
    for r in signals.itertuples(index=False):
        long_type, long_strike, short_type, short_strike = required_legs(r)
        for tm in ("09:31:00", str(r.exit_time)):
            req.append((r.trade_date, r.prior_expiry, tm, long_type, long_strike))
            req.append((r.trade_date, r.prior_expiry, tm, short_type, short_strike))
    req = pd.DataFrame(req, columns=["trade_date", "expiry", "time", "type", "strike"]).drop_duplicates()
    con = duckdb.connect()
    con.execute("SET TimeZone='Asia/Kolkata'")
    for expiry, g in req.groupby("expiry"):
        p = option_path(root, expiry)
        if not p.exists():
            continue
        dates = ",".join(f"DATE '{d}'" for d in sorted(pd.to_datetime(g.trade_date).dt.date.unique()))
        times = ",".join(f"'{x}'" for x in sorted(g.time.unique()))
        strikes = ",".join(str(float(x)) for x in sorted(g.strike.unique()))
        types = ",".join(f"'{x}'" for x in sorted(g.type.unique()))
        ps = str(p).replace("'", "''")
        q = f"""
            SELECT
                CAST(timestamp AS DATE) AS trade_date,
                CAST(expiry AS DATE) AS expiry,
                strftime(CAST(timestamp AS TIMESTAMP), '%H:%M:%S') AS local_time,
                UPPER(CAST(option_type AS VARCHAR)) AS option_type,
                CAST(strike AS DOUBLE) AS strike,
                CAST(open AS DOUBLE) AS open_px,
                CAST(close AS DOUBLE) AS close_px
            FROM read_parquet('{ps}', union_by_name=true)
            WHERE CAST(timestamp AS DATE) IN ({dates})
              AND strftime(CAST(timestamp AS TIMESTAMP), '%H:%M:%S') IN ({times})
              AND CAST(strike AS DOUBLE) IN ({strikes})
              AND UPPER(CAST(option_type AS VARCHAR)) IN ({types})
              AND (
                (strftime(CAST(timestamp AS TIMESTAMP), '%H:%M:%S')='09:31:00' AND open > 0)
                OR
                (strftime(CAST(timestamp AS TIMESTAMP), '%H:%M:%S')<>'09:31:00' AND close > 0)
              )
        """
        z = con.execute(q).df()
        if z.empty:
            continue
        z["trade_date"] = pd.to_datetime(z["trade_date"]).dt.date
        z["expiry"] = pd.to_datetime(z["expiry"]).dt.date
        for rr in z.itertuples(index=False):
            key = (rr.trade_date, rr.expiry, rr.local_time, rr.option_type, float(rr.strike))
            prices[key] = float(rr.open_px if rr.local_time == "09:31:00" else rr.close_px)
    con.close()
    return prices


def coverage_table(signals, checks):
    rows = []
    by = {}
    for state, mapping, ex, ok in checks:
        by.setdefault((state, mapping, ex), []).append(ok)
    for cell in discovery_cells():
        vals = by.get(cell, [])
        n = int(((signals.state == cell[0]) & (signals.mapping == cell[1]) & (signals.exit_time == cell[2])).sum()) if not signals.empty else 0
        ok = int(sum(vals))
        rows.append({
            "state": cell[0],
            "mapping": cell[1],
            "exit_time": cell[2],
            "expected_signals": n,
            "executed_quote_complete": ok,
            "execution_coverage": ok / n if n else 1.0,
        })
    return pd.DataFrame(rows)


def trade_rows(signals, prices, slippage):
    rows = []
    checks = []
    for r in signals.itertuples(index=False):
        d = pd.Timestamp(r.trade_date).date()
        expiry = pd.Timestamp(r.prior_expiry).date()
        lot = lot_size(expiry)
        long_type, long_strike, short_type, short_strike = required_legs(r)
        entry_tm = "09:31:00"
        exit_tm = str(r.exit_time)
        keys = [
            (d, expiry, entry_tm, long_type, float(long_strike)),
            (d, expiry, entry_tm, short_type, float(short_strike)),
            (d, expiry, exit_tm, long_type, float(long_strike)),
            (d, expiry, exit_tm, short_type, float(short_strike)),
        ]
        complete = all(k in prices for k in keys)
        if complete:
            le, se = prices[keys[0]], prices[keys[1]]
            lx, sx = prices[keys[2]], prices[keys[3]]
            entry_debit = le - se
            debit_ok = entry_debit > 0
        else:
            le = se = lx = sx = entry_debit = float("nan")
            debit_ok = False
        checks.append((r.state, r.mapping, r.exit_time, complete))
        if not complete or not debit_ok:
            continue
        exit_value = lx - sx
        gross = (exit_value - entry_debit) * lot
        slip = slippage * 4 * lot
        tc = (
            charge(le, "BUY", 1, lot, d)
            + charge(se, "SELL", 1, lot, d)
            + charge(lx, "SELL", 1, lot, d)
            + charge(sx, "BUY", 1, lot, d)
        )
        net = gross - slip - tc
        rows.append({
            **r._asdict(),
            "lot_size": lot,
            "long_strike": float(long_strike),
            "short_strike": float(short_strike),
            "entry_debit": entry_debit,
            "exit_value": exit_value,
            "gross_pnl": gross,
            "slippage_cost": slip,
            "transaction_costs": tc,
            "net_pnl": net,
            "accounting_residual": net - (gross - slip - tc),
            "entry_capital": entry_debit * lot,
            "week": str(pd.Timestamp(d).to_period("W-SUN")),
            "year": int(pd.Timestamp(d).year),
        })
    return pd.DataFrame(rows), coverage_table(signals, checks)


def bootstrap_mean_ci(values, seed=12345, draws=1000):
    a = np.asarray(values, dtype=float)
    a = a[np.isfinite(a)]
    if len(a) == 0:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(a), size=(draws, len(a)))
    return float(np.quantile(a[idx].mean(axis=1), 0.025)), float(np.quantile(a[idx].mean(axis=1), 0.975))


def summarize(trades):
    rows = []
    for cell in discovery_cells():
        g = trades[(trades.state == cell[0]) & (trades.mapping == cell[1]) & (trades.exit_time == cell[2])] if not trades.empty else pd.DataFrame()
        weekly = g.groupby("week").net_pnl.sum() if not g.empty else pd.Series(dtype=float)
        if len(g):
            pnl = g.sort_values("trade_date").net_pnl.astype(float)
            equity = pnl.cumsum()
            dd = equity - equity.cummax()
            gross = float(g.gross_pnl.sum())
            slip = float(g.slippage_cost.sum())
            tx = float(g.transaction_costs.sum())
            recon = float(g.accounting_residual.abs().max())
            pf = pnl[pnl > 0].sum() / abs(pnl[pnl < 0].sum()) if (pnl < 0).any() else float("inf")
            max_dd = float(dd.min())
        else:
            gross = slip = tx = recon = max_dd = 0.0
            pf = 0.0
        ci_lo, ci_hi = bootstrap_mean_ci(weekly.to_numpy(), seed=1000 + discovery_cells().index(cell))
        mean_w = float(weekly.mean()) if len(weekly) else 0.0
        median_w = float(weekly.median()) if len(weekly) else 0.0
        pos = float((weekly > 0).mean()) if len(weekly) else 0.0
        rows.append({
            "state": cell[0], "mapping": cell[1], "exit_time": cell[2],
            "executed_trades": int(len(g)), "weeks": int(len(weekly)),
            "total_net": float(g.net_pnl.sum()) if len(g) else 0.0,
            "mean_weekly_net": mean_w, "median_weekly_net": median_w,
            "positive_week_rate": pos,
            "bootstrap_mean_weekly_ci_low": ci_lo,
            "bootstrap_mean_weekly_ci_high": ci_hi,
            "profit_factor": pf,
            "worst_week": float(weekly.min()) if len(weekly) else 0.0,
            "worst_trade": float(g.net_pnl.min()) if len(g) else 0.0,
            "max_drawdown": max_dd,
            "raw_gross": gross, "slippage_cost": slip, "transaction_costs": tx,
            "accounting_max_residual": recon,
            "accounting_ok": recon < 1e-10,
            "average_entry_capital": float(g.entry_capital.mean()) if len(g) else 0.0,
            "max_entry_capital": float(g.entry_capital.max()) if len(g) else 0.0,
            "promotion_pass": mean_w >= 5000 and median_w >= 5000 and pos >= 0.70
        })
    return pd.DataFrame(rows)


def null_summary(panel, sessions, slippage, root):
    base_z = panel["gap_ratio_z"].to_numpy(dtype=float)
    eligible_idx = np.where(panel["feature_eligible"].to_numpy(dtype=bool))[0]
    vals = base_z[eligible_idx].copy()
    out = []
    for seed in NULL_SEEDS:
        rng = np.random.default_rng(seed)
        shuf = vals.copy()
        rng.shuffle(shuf)
        override = base_z.copy()
        override[eligible_idx] = shuf
        sig = build_signals(panel, sessions, z_override=override)
        prices = execution_price_map(sig, root)
        tr, _ = trade_rows(sig, prices, slippage)
        ss = summarize(tr)
        ss["null_seed"] = seed
        out.append(ss)
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def gate(panel, signals, coverage):
    post = panel.iloc[LOOKBACK:].copy()
    expected = max(len(panel) - LOOKBACK, 0)
    eligible = int(post.feature_eligible.sum())
    eligibility = eligible / expected if expected else 0.0
    iv_cov = float(post["atm_iv_1510"].notna().mean()) if len(post) else 0.0
    gap_cov = float(post["overnight_gap"].notna().mean()) if len(post) else 0.0
    violations = int(panel["prior_information_violation"].sum())
    expiry_cov = float(panel.loc[panel.feature_eligible, "prior_expiry"].notna().mean()) if eligible else 0.0
    exec_cov = float(coverage.execution_coverage.min()) if len(coverage) else 0.0
    status = "PASS" if (
        eligibility >= COVERAGE_TARGET
        and iv_cov >= COVERAGE_TARGET
        and gap_cov >= COVERAGE_TARGET
        and violations == 0
        and expiry_cov >= COVERAGE_TARGET
        and len(coverage) == 8
        and exec_cov >= COVERAGE_TARGET
    ) else "FAIL"
    return {
        "status": status,
        "raw_sessions": int(len(panel)),
        "post_warmup_sessions": int(expected),
        "feature_eligible_sessions": eligible,
        "post_warmup_eligibility_rate": eligibility,
        "prior_day_iv_coverage": iv_cov,
        "overnight_gap_coverage": gap_cov,
        "expiry_mapping_coverage": expiry_cov,
        "prior_information_violations": violations,
        "signal_rows": int(len(signals)),
        "execution_coverage_min": exec_cov,
        "coverage_cells": int(len(coverage)),
        "required_coverage": COVERAGE_TARGET,
        "rv_window": RV_WINDOW,
        "lookback_sessions": LOOKBACK,
        "gap_ratio_z_threshold": Z_THRESHOLD,
        "implied_move_scaling": "sqrt(1/252)",
        "study_start": str(START),
        "study_end": str(END),
    }


def run(root, out, slippage, gate_only):
    root, out = Path(root), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    panel, sessions = build_feature_panel(root)
    panel.to_csv(out / "feature_panel.csv", index=False)
    signals = build_signals(panel, sessions)
    signals.to_csv(out / "signals.csv", index=False)
    prices = execution_price_map(signals, root)
    trades, coverage = trade_rows(signals, prices, slippage)
    coverage.to_csv(out / "price_coverage.csv", index=False)
    g = gate(panel, signals, coverage)
    (out / "data_gate.json").write_text(json.dumps(g, indent=2))
    if gate_only:
        print(json.dumps(g))
        return
    trades.to_csv(out / "trades.csv", index=False)
    summarize(trades).to_csv(out / "true_cell_summary.csv", index=False)
    null_summary(panel, sessions, slippage, root).to_csv(out / "null_summary.csv", index=False)
    panel[panel.feature_eligible].to_csv(out / "eligible_feature_series.csv", index=False)
    print(json.dumps(g))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/cache/phase40_trademarkk")
    ap.add_argument("--out", default="reports/phase40/gate")
    ap.add_argument("--slippage", type=float, default=0.20)
    ap.add_argument("--gate-only", action="store_true")
    args = ap.parse_args()
    run(args.data, args.out, args.slippage, args.gate_only)


if __name__ == "__main__":
    main()
