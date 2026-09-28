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
WARMUP = 60
Z_THRESHOLD = 0.75
STATES = ("HIGH_DISLOCATION", "LOW_DISLOCATION")
MAPPINGS = ("CONTINUE", "FADE")
EXITS = ("10:30:00", "15:10:00")
NULL_SEEDS = (101, 202, 303, 404, 505)
STRIKE_STEP = 50.0
SPREAD_WIDTH = 200.0
SQRT_SESSION = math.sqrt(15.0 / 390.0)
COVERAGE_TARGET = 0.95
IV_CAP = 5.0
ND = NormalDist()


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


def implied_15m_move_pct(atm_iv):
    return float(atm_iv) * SQRT_SESSION


def prior_only_z(values, window=WARMUP):
    s = pd.Series(values, dtype="float64")
    mean_out = np.full(len(s), np.nan)
    std_out = np.full(len(s), np.nan)
    z_out = np.full(len(s), np.nan)
    history = []
    for i, value in enumerate(s.to_numpy(dtype=float)):
        if len(history) >= window and np.isfinite(value):
            prior = np.asarray(history[-window:], dtype=float)
            mean = float(prior.mean())
            std = float(prior.std(ddof=1))
            mean_out[i] = mean
            std_out[i] = std
            if std > 0:
                z_out[i] = (float(value) - mean) / std
        if np.isfinite(value):
            history.append(float(value))
    return (
        pd.Series(mean_out, index=s.index),
        pd.Series(std_out, index=s.index),
        pd.Series(z_out, index=s.index),
    )


def discovery_cells():
    return [(state, mapping, ex) for state in STATES for mapping in MAPPINGS for ex in EXITS]


def load_index(root):
    con = duckdb.connect()
    con.execute("SET TimeZone='Asia/Kolkata'")
    q = f"""
        WITH src AS (
            SELECT
                CAST(trading_day AS DATE) AS trade_date,
                CAST(timestamp AS TIMESTAMP) AS ts,
                strftime(CAST(timestamp AS TIMESTAMP), '%H:%M:%S') AS local_time,
                CAST(open AS DOUBLE) AS open_px,
                CAST(close AS DOUBLE) AS close_px
            FROM read_parquet('{idx_path(root)}', union_by_name=true)
            WHERE CAST(trading_day AS DATE) BETWEEN DATE '{START}' AND DATE '{END}'
        )
        SELECT
            trade_date,
            MAX(open_px) FILTER (WHERE local_time='09:15:00') AS open_0915,
            MAX(close_px) FILTER (WHERE local_time='09:29:00') AS close_0929,
            MAX(close_px) FILTER (WHERE local_time='09:30:00') AS spot_0930
        FROM src
        GROUP BY trade_date
        ORDER BY trade_date
    """
    x = con.execute(q).df()
    con.close()
    x["trade_date"] = pd.to_datetime(x["trade_date"]).dt.date
    for c in ("open_0915", "close_0929", "spot_0930"):
        x[c] = pd.to_numeric(x[c], errors="coerce")
    x["opening_return"] = (x["close_0929"] - x["open_0915"]) / x["open_0915"]
    x["opening_abs_return"] = x["opening_return"].abs()
    return x


def expiry_list(root):
    rows = []
    for p in sorted((root / "options" / "NIFTY").glob("*.parquet")):
        try:
            rows.append((pd.Timestamp(p.stem).date(), p))
        except Exception:
            continue
    return rows


def signal_expiry_map(sessions, exps):
    exp_dates = [d for d, _ in exps]
    mapping = {}
    for d in sessions["trade_date"]:
        future = [e for e in exp_dates if e > d]
        mapping[d] = future[0] if future else None
    return mapping


def query_0930_iv(root, requests):
    if not requests:
        return {}
    out = {}
    con = duckdb.connect()
    con.execute("SET TimeZone='Asia/Kolkata'")
    req = pd.DataFrame(requests, columns=["trade_date", "expiry", "atm_strike", "spot"])
    for expiry, g in req.groupby("expiry"):
        p = option_path(root, expiry)
        if not p.exists():
            continue
        dates = ",".join(f"DATE '{d}'" for d in sorted(g.trade_date.unique()))
        strikes = ",".join(str(float(x)) for x in sorted(g.atm_strike.unique()))
        ps = str(p).replace("'", "''")
        q = f"""
            WITH src AS (
                SELECT
                    CAST(timestamp AS DATE) AS trade_date,
                    CAST(expiry AS DATE) AS expiry,
                    CAST(timestamp AS TIMESTAMP) AS ts,
                    strftime(CAST(timestamp AS TIMESTAMP), '%H:%M:%S') AS local_time,
                    UPPER(CAST(option_type AS VARCHAR)) AS option_type,
                    CAST(strike AS DOUBLE) AS strike,
                    CAST(close AS DOUBLE) AS close_px
                FROM read_parquet('{ps}', union_by_name=true)
                WHERE CAST(timestamp AS DATE) IN ({dates})
                  AND CAST(strike AS DOUBLE) IN ({strikes})
                  AND UPPER(CAST(option_type AS VARCHAR)) IN ('CE','PE')
                  AND close > 0
                  AND strftime(CAST(timestamp AS TIMESTAMP), '%H:%M:%S') <= '09:30:00'
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
        for d, dg in g.groupby("trade_date"):
            spot = float(dg["spot"].iloc[0])
            atm = float(dg["atm_strike"].iloc[0])
            pair = z[(z.trade_date == d) & np.isclose(z.strike.astype(float), atm)]
            if pair.empty:
                continue
            vals = {}
            expiry_ts = pd.Timestamp(expiry) + pd.Timedelta(hours=15, minutes=30)
            signal_ts = pd.Timestamp(d) + pd.Timedelta(hours=9, minutes=30)
            t = (expiry_ts - signal_ts).total_seconds() / 31536000.0
            for typ in ("CE", "PE"):
                qrow = pair[pair.option_type == typ]
                if qrow.empty:
                    continue
                px = float(qrow.iloc[-1].close_px)
                vals[typ.lower() + "_price_0930"] = px
                vals[typ.lower() + "_iv_0930"] = implied_vol(px, spot, atm, t, typ == "CE")
            if np.isfinite(vals.get("ce_iv_0930", np.nan)) and np.isfinite(vals.get("pe_iv_0930", np.nan)):
                vals["atm_iv_0930"] = (vals["ce_iv_0930"] + vals["pe_iv_0930"]) / 2.0
                out[(d, expiry)] = vals
    con.close()
    return out


def build_feature_panel(root):
    sessions = load_index(root)
    exps = expiry_list(root)
    exp_map = signal_expiry_map(sessions, exps)
    req = []
    for r in sessions.itertuples(index=False):
        if not np.isfinite(r.spot_0930) or r.spot_0930 <= 0:
            continue
        exp = exp_map.get(r.trade_date)
        if exp is None:
            continue
        req.append((r.trade_date, exp, round_strike(r.spot_0930), float(r.spot_0930)))
    iv_map = query_0930_iv(root, req)
    panel = sessions.copy()
    panel["front_expiry"] = panel["trade_date"].map(exp_map)
    panel["atm_strike"] = panel["spot_0930"].map(lambda x: round_strike(x) if np.isfinite(x) else np.nan)
    iv_rows = []
    for r in panel.itertuples(index=False):
        key = (r.trade_date, r.front_expiry)
        v = iv_map.get(key, {})
        iv_rows.append({
            "ce_price_0930": v.get("ce_price_0930", np.nan),
            "pe_price_0930": v.get("pe_price_0930", np.nan),
            "ce_iv_0930": v.get("ce_iv_0930", np.nan),
            "pe_iv_0930": v.get("pe_iv_0930", np.nan),
            "atm_iv_0930": v.get("atm_iv_0930", np.nan),
        })
    panel = pd.concat([panel.reset_index(drop=True), pd.DataFrame(iv_rows)], axis=1)
    panel["implied_15m_move_pct"] = panel["atm_iv_0930"].map(
        lambda x: implied_15m_move_pct(x) if np.isfinite(x) else np.nan
    )
    panel["move_ratio"] = panel["opening_abs_return"] / panel["implied_15m_move_pct"]
    panel["prior_mean"], panel["prior_std"], panel["move_ratio_z"] = prior_only_z(panel["move_ratio"], WARMUP)
    panel["feature_eligible"] = (
        panel["open_0915"].gt(0)
        & panel["close_0929"].gt(0)
        & panel["spot_0930"].gt(0)
        & panel["opening_return"].notna()
        & panel["atm_iv_0930"].notna()
        & panel["implied_15m_move_pct"].gt(0)
        & panel["move_ratio"].notna()
        & panel["move_ratio_z"].notna()
        & panel["front_expiry"].notna()
    )
    panel["prior_date"] = panel["trade_date"].shift(1)
    panel["prior_information_violation"] = (
        panel["prior_date"].notna() & (panel["prior_date"] >= panel["trade_date"])
    )
    return panel, sessions


def build_signals(panel, sessions, z_override=None):
    d = sessions["trade_date"].tolist()
    next_day = {d[i]: d[i + 1] for i in range(len(d) - 1)}
    rows = []
    z_values = panel["move_ratio_z"].to_numpy() if z_override is None else np.asarray(z_override)
    for i, r in enumerate(panel.itertuples(index=False)):
        if not bool(r.feature_eligible):
            continue
        z = float(z_values[i])
        if not np.isfinite(z):
            continue
        state = "HIGH_DISLOCATION" if z >= Z_THRESHOLD else ("LOW_DISLOCATION" if z <= -Z_THRESHOLD else None)
        if state is None or not np.isfinite(r.opening_return) or r.opening_return == 0:
            continue
        direction = "BULL" if r.opening_return > 0 else "BEAR"
        td = next_day.get(r.trade_date)
        if td is None or r.front_expiry is None:
            continue
        for mapping in MAPPINGS:
            side = direction
            if mapping == "FADE":
                side = "BEAR" if direction == "BULL" else "BULL"
            for ex in EXITS:
                rows.append({
                    "state": state,
                    "mapping": mapping,
                    "exit_time": ex,
                    "signal_date": r.trade_date,
                    "trade_date": td,
                    "expiry": r.front_expiry,
                    "atm_strike": float(r.atm_strike),
                    "opening_return": float(r.opening_return),
                    "move_ratio": float(r.move_ratio),
                    "move_ratio_z": z,
                    "side": side,
                })
    return pd.DataFrame(rows)


def required_legs(r):
    atm = float(r.atm_strike)
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
            req.append((r.trade_date, r.expiry, tm, long_type, long_strike))
            req.append((r.trade_date, r.expiry, tm, short_type, short_strike))
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
                CAST(trading_day AS DATE) AS trade_date,
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


def debit_table(signals, checks):
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
            "positive_debit": ok,
            "positive_debit_rate": ok / n if n else 0.0,
        })
    return pd.DataFrame(rows)


def trade_rows(signals, prices, slippage):
    rows = []
    checks = []
    debit_checks = []
    for r in signals.itertuples(index=False):
        d = pd.Timestamp(r.trade_date).date()
        expiry = pd.Timestamp(r.expiry).date()
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
            long_entry = prices[keys[0]]
            short_entry = prices[keys[1]]
            long_exit = prices[keys[2]]
            short_exit = prices[keys[3]]
            entry_debit = long_entry - short_entry
            debit_ok = entry_debit > 0
        else:
            long_entry = short_entry = long_exit = short_exit = float("nan")
            entry_debit = float("nan")
            debit_ok = False
        checks.append((r.state, r.mapping, r.exit_time, complete))
        debit_checks.append((r.state, r.mapping, r.exit_time, complete and debit_ok))
        if not complete or not debit_ok:
            continue
        exit_value = long_exit - short_exit
        gross = (exit_value - entry_debit) * lot
        slip = slippage * 4 * lot
        tc = (
            charge(long_entry, "BUY", 1, lot, d)
            + charge(short_entry, "SELL", 1, lot, d)
            + charge(long_exit, "SELL", 1, lot, d)
            + charge(short_exit, "BUY", 1, lot, d)
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
    cov = coverage_table(signals, checks)
    debit = debit_table(signals, debit_checks)
    return pd.DataFrame(rows), cov, debit


def bootstrap_mean_ci(values, seed=12345, draws=1000):
    a = np.asarray(values, dtype=float)
    a = a[np.isfinite(a)]
    if len(a) == 0:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(a), size=(draws, len(a)))
    means = a[idx].mean(axis=1)
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def summarize(trades):
    rows = []
    for cell in discovery_cells():
        if trades.empty:
            g = pd.DataFrame()
        else:
            g = trades[(trades.state == cell[0]) & (trades.mapping == cell[1]) & (trades.exit_time == cell[2])]
        weekly = g.groupby("week").net_pnl.sum() if not g.empty else pd.Series(dtype=float)
        if len(g):
            pnl = g.sort_values(["trade_date", "exit_time"]).net_pnl.astype(float)
            equity = pnl.cumsum()
            dd = equity - equity.cummax()
            pf = pnl[pnl > 0].sum() / abs(pnl[pnl < 0].sum()) if (pnl < 0).any() else float("inf")
            max_dd = float(dd.min())
            worst_trade = float(pnl.min())
            gross = float(g.gross_pnl.sum())
            slippage = float(g.slippage_cost.sum())
            tx = float(g.transaction_costs.sum())
            recon = float(g.accounting_residual.abs().max())
            avg_cap = float(g.entry_capital.mean())
            max_cap = float(g.entry_capital.max())
        else:
            pf = 0.0
            max_dd = worst_trade = gross = slippage = tx = 0.0
            recon = 0.0
            avg_cap = max_cap = 0.0
        ci_lo, ci_hi = bootstrap_mean_ci(weekly.to_numpy(), seed=1000 + discovery_cells().index(cell))
        mean_week = float(weekly.mean()) if len(weekly) else 0.0
        median_week = float(weekly.median()) if len(weekly) else 0.0
        pos_rate = float((weekly > 0).mean()) if len(weekly) else 0.0
        promotion = (
            mean_week >= 5000
            and median_week >= 5000
            and pos_rate >= 0.70
        )
        rows.append({
            "state": cell[0],
            "mapping": cell[1],
            "exit_time": cell[2],
            "executed_trades": int(len(g)),
            "weeks": int(len(weekly)),
            "total_net": float(g.net_pnl.sum()) if len(g) else 0.0,
            "mean_weekly_net": mean_week,
            "median_weekly_net": median_week,
            "positive_week_rate": pos_rate,
            "bootstrap_mean_weekly_ci_low": ci_lo,
            "bootstrap_mean_weekly_ci_high": ci_hi,
            "profit_factor": pf,
            "worst_trade": worst_trade,
            "worst_week": float(weekly.min()) if len(weekly) else 0.0,
            "max_drawdown": max_dd,
            "raw_gross": gross,
            "slippage_cost": slippage,
            "transaction_costs": tx,
            "accounting_max_residual": recon,
            "accounting_ok": recon < 1e-10,
            "average_entry_capital": avg_cap,
            "max_entry_capital": max_cap,
            "promotion_pass": promotion,
        })
    return pd.DataFrame(rows)


def null_summary(panel, sessions, slippage, root):
    out = []
    base_z = panel["move_ratio_z"].to_numpy(dtype=float)
    eligible_idx = np.where(panel["feature_eligible"].to_numpy(dtype=bool))[0]
    eligible_vals = base_z[eligible_idx].copy()
    for seed in NULL_SEEDS:
        rng = np.random.default_rng(seed)
        shuffled = eligible_vals.copy()
        rng.shuffle(shuffled)
        override = base_z.copy()
        override[eligible_idx] = shuffled
        sig = build_signals(panel, sessions, z_override=override)
        prices = execution_price_map(sig, root)
        tr, _, _ = trade_rows(sig, prices, slippage)
        s = summarize(tr)
        s["null_seed"] = seed
        out.append(s)
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def gate(panel, sessions, signals, coverage):
    post_warm = panel.iloc[WARMUP:].copy()
    expected = max(len(panel) - WARMUP, 0)
    eligible = int(post_warm.feature_eligible.sum())
    eligibility_rate = eligible / expected if expected else 0.0
    iv_inputs = float(
        (post_warm[["spot_0930", "atm_strike", "front_expiry", "ce_iv_0930", "pe_iv_0930"]].notna().all(axis=1)).mean()
    ) if len(post_warm) else 0.0
    violations = int(panel["prior_information_violation"].sum())
    expiry_cov = float(panel.loc[panel.feature_eligible, "front_expiry"].notna().mean()) if eligible else 0.0
    exec_cov = float(coverage.execution_coverage.min()) if len(coverage) else 0.0
    status = (
        "PASS"
        if eligibility_rate >= COVERAGE_TARGET
        and iv_inputs >= COVERAGE_TARGET
        and violations == 0
        and expiry_cov >= COVERAGE_TARGET
        and len(coverage) == 8
        and exec_cov >= COVERAGE_TARGET
        else "FAIL"
    )
    return {
        "status": status,
        "raw_sessions": int(len(panel)),
        "post_warmup_sessions": int(expected),
        "feature_eligible_sessions": eligible,
        "post_warmup_eligibility_rate": eligibility_rate,
        "iv_input_coverage": iv_inputs,
        "expiry_mapping_coverage": expiry_cov,
        "prior_information_violations": violations,
        "signal_rows": int(len(signals)),
        "execution_coverage_min": exec_cov,
        "coverage_cells": int(len(coverage)),
        "required_coverage": COVERAGE_TARGET,
        "lookback_sessions": WARMUP,
        "move_ratio_z_threshold": Z_THRESHOLD,
        "implied_move_scaling": "sqrt(15/390)",
        "study_start": str(START),
        "study_end": str(END),
    }


def run(root, out, slippage, gate_only):
    root = Path(root)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    panel, sessions = build_feature_panel(root)
    panel.to_csv(out / "feature_panel.csv", index=False)
    panel.to_csv(out / "source_signal_panel.csv", index=False)
    signals = build_signals(panel, sessions)
    signals.to_csv(out / "signals.csv", index=False)
    prices = execution_price_map(signals, root)
    trades, coverage, debit = trade_rows(signals, prices, slippage)
    coverage.to_csv(out / "price_coverage.csv", index=False)
    debit.to_csv(out / "debit_admissibility.csv", index=False)
    g = gate(panel, sessions, signals, coverage)
    (out / "data_gate.json").write_text(json.dumps(g, indent=2))
    if gate_only:
        print(json.dumps(g))
        return
    trades.to_csv(out / "trades.csv", index=False)
    summary = summarize(trades)
    summary.to_csv(out / "true_cell_summary.csv", index=False)
    nulls = null_summary(panel, sessions, slippage, root)
    nulls.to_csv(out / "null_summary.csv", index=False)
    eligible = panel[panel.feature_eligible].copy()
    pd.DataFrame({
        "trade_date": eligible.trade_date.astype(str),
        "year": pd.to_datetime(eligible.trade_date).dt.year,
        "move_ratio": eligible.move_ratio,
        "move_ratio_z": eligible.move_ratio_z,
        "opening_return": eligible.opening_return,
        "atm_iv_0930": eligible.atm_iv_0930,
    }).to_csv(out / "eligible_feature_series.csv", index=False)
    print(json.dumps(g))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/cache/phase39_trademarkk")
    ap.add_argument("--out", default="reports/phase39/gate")
    ap.add_argument("--slippage", type=float, default=0.20)
    ap.add_argument("--gate-only", action="store_true")
    args = ap.parse_args()
    run(args.data, args.out, args.slippage, args.gate_only)


if __name__ == "__main__":
    main()
