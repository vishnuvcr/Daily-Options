from __future__ import annotations

import argparse
import itertools
import json
import math
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd


START = "2025-09-01"
END = "2026-08-31"

ENTRY_DAYS = ("MON", "TUE", "WED", "THU", "FRI")
ENTRY_TIMES = ("09:20", "10:00", "11:00")
EXPIRY_CHOICES = ("nearest_weekly", "second_nearest_weekly")
STRIKE_METHODS = ("delta020", "sigma1", "sigma2")
TRIGGERS = ("touch", "ninety_pct")
ACTIONS = ("add_short", "protective_next_strike")
RISKS = ("no_stop", "stop_2x_credit")

SLIP_BASE = 0.20
SLIP_STRESS = 0.40


def lot_size(expiry) -> int:
    return 75 if pd.Timestamp(expiry).date() <= pd.Timestamp("2025-12-30").date() else 65


def weekly_expiries(expiries) -> list:
    xs = sorted(set(pd.Timestamp(e).date() for e in expiries))
    by_month = {}
    for e in xs:
        by_month.setdefault((e.year, e.month), []).append(e)
    monthly = {max(v) for v in by_month.values()}
    return [e for e in xs if e not in monthly]


def load_spot(root: Path) -> pd.DataFrame:
    frames = []
    for p in sorted(root.glob("*.csv")):
        z = pd.read_csv(p)
        ts = pd.to_datetime(z["Timestamp"], errors="coerce")
        if getattr(ts.dt, "tz", None) is None:
            ts = ts.dt.tz_localize("Asia/Kolkata")
        else:
            ts = ts.dt.tz_convert("Asia/Kolkata")
        z["Timestamp"] = ts
        for c in ("Open", "High", "Low", "Close"):
            z[c] = pd.to_numeric(z[c], errors="coerce")
        frames.append(z[["Timestamp", "Open", "High", "Low", "Close"]])
    if not frames:
        raise RuntimeError("NIFTY spot cache is empty")
    z = (
        pd.concat(frames, ignore_index=True)
        .dropna()
        .drop_duplicates("Timestamp")
        .sort_values("Timestamp")
    )
    return z[
        (z.Timestamp.dt.date >= pd.Timestamp(START).date())
        & (z.Timestamp.dt.date <= pd.Timestamp(END).date())
    ].reset_index(drop=True)


def load_vix(path: Path) -> pd.DataFrame:
    z = pd.read_csv(path)
    z["date"] = pd.to_datetime(z["date"], errors="coerce").dt.date
    z["close"] = pd.to_numeric(z["close"], errors="coerce")
    z = z.dropna(subset=["date", "close"]).drop_duplicates("date").sort_values("date")
    if z.empty:
        raise RuntimeError("VIX cache is empty")
    return z[(z.date >= pd.Timestamp(START).date()) & (z.date <= pd.Timestamp(END).date())].reset_index(drop=True)


def prior_vix_close(vix: pd.DataFrame, d) -> float | None:
    x = vix[vix.date < d]
    return None if x.empty else float(x.iloc[-1].close)


def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def bs_call_delta(spot: float, strike: float, sigma: float, t_years: float) -> float:
    if sigma <= 0 or t_years <= 0:
        return 1.0 if spot > strike else 0.0
    d1 = (math.log(max(spot, 1e-9) / max(strike, 1e-9)) + 0.5 * sigma * sigma * t_years) / (
        sigma * math.sqrt(t_years)
    )
    return norm_cdf(d1)


def bs_put_abs_delta(spot: float, strike: float, sigma: float, t_years: float) -> float:
    if sigma <= 0 or t_years <= 0:
        return 1.0 if spot < strike else 0.0
    d1 = (math.log(max(spot, 1e-9) / max(strike, 1e-9)) + 0.5 * sigma * sigma * t_years) / (
        sigma * math.sqrt(t_years)
    )
    return norm_cdf(-d1)


def expected_strikes(spot: float, strikes: np.ndarray, sigma: float, t_years: float, method: str) -> tuple[float, float]:
    ks = np.asarray(strikes, dtype=float)
    if not len(ks):
        raise RuntimeError("No listed strikes")

    if method == "delta020":
        c = np.array([abs(bs_call_delta(spot, k, sigma, t_years) - 0.20) for k in ks])
        p = np.array([abs(bs_put_abs_delta(spot, k, sigma, t_years) - 0.20) for k in ks])
        call = float(ks[int(np.argmin(c))])
        put = float(ks[int(np.argmin(p))])
        if put >= call:
            below = ks[ks < spot]
            above = ks[ks > spot]
            if len(below):
                put = float(below[-1])
            if len(above):
                call = float(above[0])
        return put, call

    multiplier = 1.0 if method == "sigma1" else 2.0
    move = spot * sigma * math.sqrt(max(t_years, 1e-9)) * multiplier
    below = ks[ks <= spot - move]
    above = ks[ks >= spot + move]
    put = float(below[-1]) if len(below) else float(ks[0])
    call = float(above[0]) if len(above) else float(ks[-1])
    if put >= call:
        mid = int(np.argmin(np.abs(ks - spot)))
        put = float(ks[max(0, mid - 1)])
        call = float(ks[min(len(ks) - 1, mid + 1)])
    return put, call


def load_option_rows(data_root: Path, contracts: pd.DataFrame) -> pd.DataFrame:
    files = sorted(data_root.glob("NIFTY_*.parquet"))
    if not files:
        raise RuntimeError("NIFTY option cache is empty")
    con = duckdb.connect()
    relation = "read_parquet(" + json.dumps([str(x) for x in files]) + ", union_by_name=true)"
    con.register("contracts", contracts)
    q = f"""
        SELECT
          CAST(q.date AS DATE) AS date,
          q.timestamp AS ts,
          CAST(q.expiry AS DATE) AS expiry,
          CAST(q.strike AS DOUBLE) AS strike,
          UPPER(CAST(q.option_type AS VARCHAR)) AS option_type,
          CAST(q.open AS DOUBLE) AS open_px,
          CAST(q.close AS DOUBLE) AS close_px
        FROM {relation} q
        JOIN contracts k
          ON CAST(q.expiry AS DATE) = k.expiry
         AND CAST(q.strike AS DOUBLE) = k.strike
         AND UPPER(CAST(q.option_type AS VARCHAR)) = k.option_type
         AND CAST(q.date AS DATE) >= k.start_date
         AND CAST(q.date AS DATE) <= k.end_date
        WHERE q.granularity = '1min'
          AND q.open > 0
          AND q.close > 0
        ORDER BY expiry, strike, option_type, ts
    """
    z = con.execute(q).df()
    if z.empty:
        return z
    z["expiry"] = pd.to_datetime(z["expiry"]).dt.date
    z["ts"] = pd.to_datetime(z["ts"])
    if z["ts"].dt.tz is None:
        z["ts"] = z["ts"].dt.tz_localize("Asia/Kolkata")
    else:
        z["ts"] = z["ts"].dt.tz_convert("Asia/Kolkata")
    return z.drop_duplicates(["expiry", "strike", "option_type", "ts"]).sort_values(
        ["expiry", "strike", "option_type", "ts"]
    )


def first_quote(series: pd.DataFrame | None, when, exact: bool = False):
    if series is None or series.empty:
        return None
    ts = series["ts"].to_numpy(dtype="datetime64[ns]")
    t = pd.Timestamp(when).tz_convert("Asia/Kolkata").to_datetime64() if pd.Timestamp(when).tzinfo else pd.Timestamp(when).tz_localize("Asia/Kolkata").to_datetime64()
    idx = np.searchsorted(ts, t, side="left")
    if idx >= len(series):
        return None
    if exact and ts[idx] != t:
        return None
    return series.iloc[int(idx)]


def series_map(opt: pd.DataFrame) -> dict[tuple, pd.DataFrame]:
    return {
        (e, float(s), ot): g.reset_index(drop=True)
        for (e, s, ot), g in opt.groupby(["expiry", "strike", "option_type"], sort=False)
    }


def cost(orders: list[dict], slip: float) -> float:
    brokerage = 20.0 * len(orders)
    ex = sebi = stt = stamp = 0.0
    for o in orders:
        d = pd.Timestamp(o["date"]).date()
        px = float(o["price"])
        qty = int(o["qty"])
        turnover = px * qty
        ex += turnover * (0.0003503 if d < pd.Timestamp("2026-03-01").date() else 0.0003553)
        sebi += turnover * 0.000001
        if o["side"] < 0:
            stt += turnover * (0.001 if d < pd.Timestamp("2026-04-01").date() else 0.0015)
        else:
            stamp += turnover * 0.00003
    return brokerage + ex + sebi + stt + stamp + 0.18 * (brokerage + ex + sebi)


def fill_price(raw: float, side: int, slip: float) -> float:
    return raw + slip if side > 0 else raw - slip


def key_week(d) -> str:
    iso = pd.Timestamp(d).isocalendar()
    return f"{int(iso.year)}-W{int(iso.week):02d}"


def capital_proxy(spot: float, put: float, call: float, credit_points: float, lot: int, adjusted: bool) -> float:
    worst_leg_points = max(abs(spot - put), abs(call - spot))
    base = credit_points * lot + worst_leg_points * lot * 0.20
    return float(base * (1.25 if adjusted else 1.0))


def make_events(spot: pd.DataFrame, vix: pd.DataFrame, expiries: list, entry_day: str, entry_time: str, expiry_choice: str, strike_method: str, strikes_by_expiry: dict) -> pd.DataFrame:
    weekday_map = {"MON": 0, "TUE": 1, "WED": 2, "THU": 3, "FRI": 4}
    target_wd = weekday_map[entry_day]
    rows = []
    day_spot = spot[spot.Timestamp.dt.weekday == target_wd].copy()
    for d, g in day_spot.groupby(day_spot.Timestamp.dt.date):
        if pd.Timestamp(d).date() < pd.Timestamp(START).date() or pd.Timestamp(d).date() > pd.Timestamp(END).date():
            continue
        entry_ts = pd.Timestamp(f"{d} {entry_time}", tz="Asia/Kolkata")
        q = g[g.Timestamp >= entry_ts]
        if q.empty:
            continue
        spot_px = float(q.iloc[0]["Close"])
        vix_close = prior_vix_close(vix, d)
        if vix_close is None:
            continue
        future = [e for e in expiries if e > d]
        if len(future) < 2:
            continue
        expiry = future[0] if expiry_choice == "nearest_weekly" else future[1]
        t_years = max((pd.Timestamp(f"{expiry} 15:30", tz="Asia/Kolkata") - entry_ts).total_seconds(), 60.0) / (365.0 * 24 * 3600)
        ks = strikes_by_expiry.get(expiry, np.array([]))
        if not len(ks):
            continue
        put_k, call_k = expected_strikes(spot_px, ks, vix_close / 100.0, t_years, strike_method)
        rows.append({
            "entry_date": d,
            "entry_ts": entry_ts,
            "entry_day": entry_day,
            "entry_time": entry_time,
            "expiry_choice": expiry_choice,
            "strike_method": strike_method,
            "expiry": expiry,
            "spot": spot_px,
            "vix_close": vix_close,
            "put_strike": put_k,
            "call_strike": call_k,
            "week": key_week(d),
        })
    return pd.DataFrame(rows)


def eval_event(event: dict, smap: dict, spot_ts: pd.Series, spot_df: pd.DataFrame, slip: float) -> dict:
    expiry = event["expiry"]
    put_k = float(event["put_strike"])
    call_k = float(event["call_strike"])
    entry_ts = event["entry_ts"]
    lot = lot_size(expiry)
    p_series = smap.get((expiry, put_k, "PE"))
    c_series = smap.get((expiry, call_k, "CE"))
    if p_series is None or c_series is None:
        return {"status": "entry_missing", "eligible": False}

    pe = first_quote(p_series, entry_ts)
    ce = first_quote(c_series, entry_ts)
    if pe is None or ce is None:
        return {"status": "entry_missing", "eligible": False}

    entry_credit = float(pe.open_px) + float(ce.open_px)
    if entry_credit <= 0:
        return {"status": "nonpositive_credit", "eligible": False}

    exit_ts = pd.Timestamp(f"{expiry} 15:25", tz="Asia/Kolkata")
    path_spot = spot_df[(spot_df.Timestamp >= entry_ts) & (spot_df.Timestamp <= exit_ts)][["Timestamp", "Close"]].copy()
    if path_spot.empty:
        return {"status": "spot_path_missing", "eligible": False}

    up_thresholds = {
        "touch": call_k,
        "ninety_pct": event["spot"] + 0.90 * (call_k - event["spot"]),
    }
    dn_thresholds = {
        "touch": put_k,
        "ninety_pct": event["spot"] - 0.90 * (event["spot"] - put_k),
    }

    base_context = {
        "entry_credit": entry_credit,
        "entry_pe": pe,
        "entry_ce": ce,
        "lot": lot,
        "exit_ts": exit_ts,
        "p_series": p_series,
        "c_series": c_series,
        "path_spot": path_spot,
        "up_hedge_strike": None,
        "dn_hedge_strike": None,
    }

    event_results = []
    for trigger in TRIGGERS:
        up_hit = path_spot[path_spot.Close >= up_thresholds[trigger]]
        dn_hit = path_spot[path_spot.Close <= dn_thresholds[trigger]]
        candidates = []
        if not up_hit.empty:
            candidates.append(("UP", up_hit.iloc[0].Timestamp))
        if not dn_hit.empty:
            candidates.append(("DOWN", dn_hit.iloc[0].Timestamp))
        trigger_side, trigger_ts = min(candidates, key=lambda x: x[1]) if candidates else (None, None)

        adj_ts = None
        adj_series = None
        adj_quote = None
        hedge_strike = None

        if trigger_ts is not None:
            obs_ts = trigger_ts + pd.Timedelta(minutes=1)
            if trigger_side == "UP":
                adj_series = c_series
                if ACTIONS:
                    all_call_strikes = sorted({k[1] for k in smap if k[0] == expiry and k[2] == "CE"})
                    higher = [k for k in all_call_strikes if k > call_k]
                    hedge_strike = higher[0] if higher else None
            else:
                adj_series = p_series
                all_put_strikes = sorted({k[1] for k in smap if k[0] == expiry and k[2] == "PE"})
                lower = [k for k in all_put_strikes if k < put_k]
                hedge_strike = lower[-1] if lower else None
            adj_quote = first_quote(adj_series, obs_ts)
            adj_ts = adj_quote.ts if adj_quote is not None else None

        if trigger_ts is not None and adj_quote is None:
            continue

        for action, risk in itertools.product(ACTIONS, RISKS):
            adjusted = bool(adj_quote is not None)
            if action == "protective_next_strike" and hedge_strike is not None and trigger_ts is not None:
                hedge_type = "CE" if trigger_side == "UP" else "PE"
                hedge_series = smap.get((expiry, float(hedge_strike), hedge_type))
                hedge_quote = first_quote(hedge_series, trigger_ts + pd.Timedelta(minutes=1)) if hedge_series is not None else None
            else:
                hedge_type = None
                hedge_series = None
                hedge_quote = None

            # Build synchronized mark path. Initial short legs are marked from entry.
            z = path_spot[["Timestamp"]].copy()
            pc = p_series[["ts", "close_px"]].rename(columns={"ts": "Timestamp", "close_px": "put_px"})
            cc = c_series[["ts", "close_px"]].rename(columns={"ts": "Timestamp", "close_px": "call_px"})
            z = pd.merge_asof(z.sort_values("Timestamp"), pc.sort_values("Timestamp"), on="Timestamp", direction="backward")
            z = pd.merge_asof(z.sort_values("Timestamp"), cc.sort_values("Timestamp"), on="Timestamp", direction="backward")
            if hedge_series is not None:
                hc = hedge_series[["ts", "close_px"]].rename(columns={"ts": "Timestamp", "close_px": "hedge_px"})
                z = pd.merge_asof(z.sort_values("Timestamp"), hc.sort_values("Timestamp"), on="Timestamp", direction="backward")
            z = z.dropna(subset=["put_px", "call_px"])
            if z.empty:
                continue

            if adjusted:
                mask_after = z.Timestamp >= adj_ts
            else:
                mask_after = pd.Series(False, index=z.index)

            pnl_points = entry_credit - z["put_px"].astype(float) - z["call_px"].astype(float)
            if adjusted and action == "add_short":
                adj_price = float(adj_quote.open_px)
                adj_mark = z["call_px"] if trigger_side == "UP" else z["put_px"]
                pnl_points = pnl_points + (adj_price - adj_mark.astype(float)).where(mask_after, 0.0)
            elif adjusted and action == "protective_next_strike":
                if hedge_quote is None:
                    continue
                hprice = float(hedge_quote.open_px)
                hmark = z.get("hedge_px")
                if hmark is None:
                    continue
                pnl_points = pnl_points + (-hprice + hmark.astype(float)).where(mask_after, 0.0)

            stop_idx = None
            if risk == "stop_2x_credit":
                stop_level = -2.0 * entry_credit
                bad = np.flatnonzero(pnl_points.to_numpy(dtype=float) <= stop_level)
                if len(bad):
                    stop_idx = int(bad[0])

            if stop_idx is None:
                xt = exit_ts
                reason = "TIME_EXIT"
            else:
                xt = z.iloc[stop_idx].Timestamp + pd.Timedelta(minutes=1)
                reason = "STOP"

            p_exit = first_quote(p_series, xt)
            c_exit = first_quote(c_series, xt)
            if p_exit is None or c_exit is None:
                continue

            orders = [
                {"date": event["entry_date"], "side": -1, "price": fill_price(float(pe.open_px), -1, slip), "qty": lot},
                {"date": event["entry_date"], "side": -1, "price": fill_price(float(ce.open_px), -1, slip), "qty": lot},
            ]
            positions = [
                ("PE", put_k, lot, -1),
                ("CE", call_k, lot, -1),
            ]
            if adjusted and adj_ts <= xt:
                if action == "add_short":
                    orders.append({
                        "date": pd.Timestamp(adj_ts).date(), "side": -1,
                        "price": fill_price(float(adj_quote.open_px), -1, slip), "qty": lot,
                    })
                    if trigger_side == "UP":
                        positions.append(("CE", call_k, lot, -1))
                    else:
                        positions.append(("PE", put_k, lot, -1))
                elif action == "protective_next_strike":
                    if hedge_quote is None:
                        continue
                    orders.append({
                        "date": pd.Timestamp(hedge_quote.ts).date(), "side": 1,
                        "price": fill_price(float(hedge_quote.open_px), 1, slip), "qty": lot,
                    })
                    positions.append((hedge_type, float(hedge_strike), lot, 1))

            close_map = {}
            for ot, sk, qty, direction in positions:
                k = (ot, float(sk), direction)
                close_map[k] = close_map.get(k, 0) + qty

            for (ot, sk, direction), qty in close_map.items():
                ser = smap.get((expiry, sk, ot))
                q = first_quote(ser, xt)
                if q is None:
                    close_map = None
                    break
                close_side = 1 if direction == -1 else -1
                orders.append({
                    "date": pd.Timestamp(q.ts).date(),
                    "side": close_side,
                    "price": fill_price(float(q.open_px), close_side, slip),
                    "qty": int(qty),
                })
            if close_map is None:
                continue

            gross = sum((-1 if o["side"] > 0 else 1) * float(o["price"]) * int(o["qty"]) for o in orders)
            net = gross - cost(orders, slip)
            cap = capital_proxy(event["spot"], put_k, call_k, entry_credit, lot, adjusted and adj_ts <= xt)

            event_results.append({
                "trigger": trigger,
                "action": action,
                "risk": risk,
                "status": "ok",
                "eligible": True,
                "week": event["week"],
                "net_pnl": net,
                "gross_pnl": gross,
                "cost": net * 0 + (gross - net),
                "capital_proxy": cap,
                "adjusted": bool(adjusted and adj_ts <= xt),
                "reason": reason,
                "entry_credit": entry_credit,
            })

    return event_results


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, required=True)
    ap.add_argument("--spot-root", type=Path, required=True)
    ap.add_argument("--vix-file", type=Path, required=True)
    ap.add_argument("--out-root", type=Path, required=True)
    ap.add_argument("--slippage", type=float, default=SLIP_BASE)
    ap.add_argument("--def-start", type=int, default=0)
    ap.add_argument("--def-count", type=int, default=8)
    ap.add_argument("--start", default=START)
    ap.add_argument("--end", default=END)
    args = ap.parse_args()

    global START, END
    START, END = args.start, args.end

    out = args.out_root
    out.mkdir(parents=True, exist_ok=True)

    spot = load_spot(args.spot_root)
    vix = load_vix(args.vix_file)

    con = duckdb.connect()
    files = sorted(args.data_root.glob("NIFTY_*.parquet"))
    if not files:
        raise RuntimeError("NIFTY option cache is missing")
    relation = "read_parquet(" + json.dumps([str(x) for x in files]) + ", union_by_name=true)"
    expiry_rows = con.execute(
        f"SELECT DISTINCT CAST(expiry AS DATE) AS expiry FROM {relation} WHERE granularity='1min' ORDER BY expiry"
    ).fetchall()
    expiries = weekly_expiries([x[0] for x in expiry_rows])
    if not expiries:
        raise RuntimeError("No weekly expiries found")

    # Cache the listed strike set for each weekly expiry.
    e_sql = ",".join(["?"] * len(expiries))
    strike_df = con.execute(
        f"SELECT DISTINCT CAST(expiry AS DATE) expiry, CAST(strike AS DOUBLE) strike "
        f"FROM {relation} WHERE granularity='1min' AND CAST(expiry AS DATE) IN ({e_sql}) "
        f"ORDER BY expiry, strike",
        expiries,
    ).df()
    strike_df["expiry"] = pd.to_datetime(strike_df["expiry"], errors="coerce").dt.date
    strikes_by_expiry = {
        e: np.sort(g.strike.to_numpy(dtype=float))
        for e, g in strike_df.groupby("expiry")
    }

    base_specs = list(itertools.product(ENTRY_DAYS, ENTRY_TIMES, EXPIRY_CHOICES, STRIKE_METHODS))
    shard_specs = base_specs[args.def_start : args.def_start + args.def_count]
    if not shard_specs:
        raise RuntimeError("Empty shard definition range")

    # Build all event definitions for this shard before loading option quotes.
    event_frames = []
    for day, tm, ec, sm in shard_specs:
        z = make_events(spot, vix, expiries, day, tm, ec, sm, strikes_by_expiry)
        if not z.empty:
            event_frames.append(z)
    if not event_frames:
        raise RuntimeError("No executable event definitions in shard")
    events = pd.concat(event_frames, ignore_index=True)

    # Required quote contracts.
    contracts = []
    for r in events.itertuples():
        contracts.extend([
            {"expiry": r.expiry, "strike": float(r.put_strike), "option_type": "PE", "start_date": r.entry_date, "end_date": r.expiry},
            {"expiry": r.expiry, "strike": float(r.call_strike), "option_type": "CE", "start_date": r.entry_date, "end_date": r.expiry},
        ])
        # Add adjacent hedge strikes where available.
        pks = strikes_by_expiry.get(r.expiry, np.array([]))
        put_lower = pks[pks < r.put_strike]
        call_higher = pks[pks > r.call_strike]
        if len(put_lower):
            contracts.append({"expiry": r.expiry, "strike": float(put_lower[-1]), "option_type": "PE", "start_date": r.entry_date, "end_date": r.expiry})
        if len(call_higher):
            contracts.append({"expiry": r.expiry, "strike": float(call_higher[0]), "option_type": "CE", "start_date": r.entry_date, "end_date": r.expiry})

    contracts = pd.DataFrame(contracts).drop_duplicates()
    opt = load_option_rows(args.data_root, contracts)
    if opt.empty:
        raise RuntimeError("Required option quote set is empty")
    smap = series_map(opt)

    week_seen = {}
    cells = {}
    for r in events.itertuples():
        base_key = (r.entry_day, r.entry_time, r.expiry_choice, r.strike_method)
        week_seen.setdefault(base_key, set()).add(r.week)
        results = eval_event(r._asdict(), smap, spot.set_index("Timestamp")["Close"], spot, args.slippage)
        if isinstance(results, dict):
            results = [results]
        for res in results:
            if not res.get("eligible"):
                continue
            vk = (res["trigger"], res["action"], res["risk"])
            k = base_key + vk
            st = cells.setdefault(k, {"weeks": {}, "trades": 0, "gross": 0.0, "net": 0.0, "cost": 0.0, "cap": []})
            if res.get("eligible"):
                st["trades"] += 1
                st["weeks"][r.week] = st["weeks"].get(r.week, 0.0) + float(res["net_pnl"])
                st["gross"] += float(res["gross_pnl"])
                st["net"] += float(res["net_pnl"])
                st["cost"] += float(res["cost"])
                st["cap"].append(float(res["capital_proxy"]))

    rows = []
    full_keys = list(itertools.product(shard_specs, TRIGGERS, ACTIONS, RISKS))
    # Above creates tuples like ((day,time,expiry,method),trigger,action,risk).
    for base_key, trig, action, risk in full_keys:
        key = tuple(base_key) + (trig, action, risk)
        st = cells.get(key, {"weeks": {}, "trades": 0, "gross": 0.0, "net": 0.0, "cost": 0.0, "cap": []})
        active = pd.Series(st["weeks"], dtype=float).sort_index()
        completed = int(len(active))
        mean_week = float(active.mean()) if completed else 0.0
        median_week = float(active.median()) if completed else 0.0
        pos_rate = float((active > 0).mean()) if completed else 0.0
        gross_pos = float(active[active > 0].sum()) if completed else 0.0
        gross_neg = float(-active[active < 0].sum()) if completed else 0.0
        eq = active.cumsum()
        dd = eq - eq.cummax()
        expected_weeks = len(week_seen.get(base_key, set()))
        rows.append({
            "entry_day": key[0],
            "entry_time": key[1],
            "expiry_choice": key[2],
            "strike_method": key[3],
            "trigger": key[4],
            "action": key[5],
            "risk": key[6],
            "trades": int(st["trades"]),
            "weeks_completed": completed,
            "eligible_weeks": expected_weeks,
            "mean_weekly_net": mean_week,
            "median_weekly_net": median_week,
            "profitable_week_rate": pos_rate,
            "profit_factor": float(gross_pos / gross_neg) if gross_neg else math.inf,
            "max_drawdown": float(dd.min()) if completed else 0.0,
            "weekly_q05": float(active.quantile(0.05)) if completed else 0.0,
            "weekly_es05": float(active[active <= active.quantile(0.05)].mean()) if completed and (active <= active.quantile(0.05)).any() else 0.0,
            "execution_coverage": float(completed / expected_weeks) if expected_weeks else 0.0,
            "avg_capital_proxy": float(np.mean(st["cap"])) if st["cap"] else 0.0,
            "peak_capital_proxy": float(np.max(st["cap"])) if st["cap"] else 0.0,
            "gross_pnl": float(st["gross"]),
            "costs": float(st["cost"]),
            "net_pnl": float(st["net"]),
            "cost_share": float(st["cost"] / abs(st["gross"])) if st["gross"] else 0.0,
            "gate": bool(
                mean_week >= 5000
                and median_week >= 5000
                and pos_rate >= 0.70
                and completed >= 20
                and (completed / expected_weeks if expected_weeks else 0.0) >= 0.80
            ),
        })

    lb = pd.DataFrame(rows).sort_values(["gate", "mean_weekly_net"], ascending=[False, False])
    lb.to_csv(out / "leaderboard.csv", index=False)
    diagnostics = {
        "base_definitions_registered": len(base_specs),
        "base_definitions_in_shard": len(shard_specs),
        "event_rows": int(len(events)),
        "option_rows_loaded": int(len(opt)),
        "option_series": int(len(smap)),
        "vix_rows": int(len(vix)),
        "study_window": [START, END],
        "slippage": args.slippage,
        "pnl_authorized": True,
    }
    (out / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2, default=str))
    summary = {
        "registered_cells_total": len(base_specs) * len(TRIGGERS) * len(ACTIONS) * len(RISKS),
        "tested_cells_in_shard": int(len(lb)),
        "passed_gate_in_shard": int(lb["gate"].sum()),
        "best_cell": lb.iloc[0].to_dict() if len(lb) else {},
        "slippage": args.slippage,
        "study_window": [START, END],
        "pnl_authorized": True,
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
