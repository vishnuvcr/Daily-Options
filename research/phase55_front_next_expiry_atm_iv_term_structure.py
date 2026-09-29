#!/usr/bin/env python3
from __future__ import annotations

import argparse
import bisect
import json
import math
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

START = date(2021, 7, 1)
END = date(2026, 8, 31)
LOOKBACK = 60
WING = 200
STRIKE_STEP = 50
HORIZONS = {"H10_30": "10:30:00", "H15_10": "15:10:00"}
DIRECTIONS = ("CONTINUE", "FADE")
STATES = ("STEEP_TERM", "INVERTED_TERM")
NULL_SEEDS = (101, 202, 303, 404, 505)
WEEKLY_TARGET = 5000.0
POSITIVE_WEEK_TARGET = 0.70
COVERAGE_TARGET = 0.95


@dataclass(frozen=True)
class Cell:
    state: str
    mapping: str
    horizon: str

    @property
    def cell_id(self) -> str:
        return f"{self.state}|{self.mapping}|{self.horizon}"


def cells():
    return [Cell(s, m, h) for s in STATES for m in DIRECTIONS for h in HORIZONS]


def cell_key(state, mapping, horizon):
    return f"{state}|{mapping}|{horizon}"


def lot_size(expiry: date) -> int:
    if expiry < date(2024, 4, 26):
        return 50
    if expiry < date(2024, 11, 21):
        return 25
    if expiry < date(2026, 1, 6):
        return 75
    return 65


def charge(price: float, side: str, qty: int, lot: int, order_date: date) -> float:
    gross = float(price) * qty * lot
    stt_rate = 0.001 if order_date < date(2026, 4, 1) else 0.0015
    exchange_rate = 0.0003503 if order_date < date(2026, 3, 1) else 0.000355299
    brokerage = 20.0
    sebi = gross * 0.000001
    exchange = gross * exchange_rate
    stt = gross * stt_rate if side == "SELL" else 0.0
    stamp = gross * 0.00003 if side == "BUY" else 0.0
    gst = 0.18 * (brokerage + exchange + sebi)
    return brokerage + exchange + sebi + stt + stamp + gst


def price_key(trade_date, expiry, option_type, strike, clock):
    d = pd.Timestamp(trade_date).date()
    e = pd.Timestamp(expiry).date()
    return (d, e, str(option_type).upper(), float(strike), pd.Timestamp(clock).strftime("%Y-%m-%d %H:%M:%S"))


def round_strike(px: float) -> int:
    return int(math.floor(float(px) / STRIKE_STEP + 0.5) * STRIKE_STEP)



def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def bs_price(spot: float, strike: float, t: float, sigma: float, call: bool) -> float:
    if min(spot, strike, t, sigma) <= 0:
        return max(spot - strike, 0.0) if call else max(strike - spot, 0.0)
    d1 = (math.log(spot / strike) + 0.5 * sigma * sigma * t) / (sigma * math.sqrt(t))
    d2 = d1 - sigma * math.sqrt(t)
    if call:
        return spot * norm_cdf(d1) - strike * norm_cdf(d2)
    return strike * norm_cdf(-d2) - spot * norm_cdf(-d1)


def implied_vol(spot: float, strike: float, t: float, target: float, call: bool) -> float | None:
    if not all(np.isfinite([spot, strike, t, target])) or min(spot, strike, t, target) <= 0:
        return None
    intrinsic = max(spot - strike, 0.0) if call else max(strike - spot, 0.0)
    upper = spot if call else strike
    if target + 1e-8 < intrinsic or target - 1e-8 > upper:
        return None
    lo, hi = 1e-5, 5.0
    if bs_price(spot, strike, t, hi, call) < target:
        return None
    for _ in range(90):
        mid = 0.5 * (lo + hi)
        p = bs_price(spot, strike, t, mid, call)
        if p < target:
            lo = mid
        else:
            hi = mid
    iv = 0.5 * (lo + hi)
    return iv if np.isfinite(iv) and 0 < iv < 5.0 else None


def load_nifty(root: Path) -> pd.DataFrame:
    con = duckdb.connect()
    con.execute("SET TimeZone='Asia/Kolkata'")
    p = str(root / "index" / "NIFTY.parquet").replace("'", "''")
    q = f"""
    SELECT CAST(timestamp AS TIMESTAMP) ts,
           CAST(open AS DOUBLE) open_px,
           CAST(high AS DOUBLE) high_px,
           CAST(low AS DOUBLE) low_px,
           CAST(close AS DOUBLE) close_px
    FROM read_parquet('{p}')
    WHERE CAST(timestamp AS DATE) BETWEEN DATE '{START}' AND DATE '{END}'
    ORDER BY ts
    """
    x = con.execute(q).df()
    con.close()
    if x.empty:
        raise RuntimeError("NIFTY index cache is empty for the study window")
    x["ts"] = pd.to_datetime(x["ts"]).dt.floor("min")
    x = x.drop_duplicates("ts").sort_values("ts")
    x["date"] = x["ts"].dt.date
    x["time"] = x["ts"].dt.strftime("%H:%M:%S")
    return x


def build_feature_panel(nifty: pd.DataFrame) -> pd.DataFrame:
    x=nifty[nifty["time"].isin(["09:15:00","15:10:00"])].copy()
    opens=(x[x["time"]=="09:15:00"][["date","open_px"]]
           .drop_duplicates("date").rename(columns={"open_px":"open_0915"}))
    bars=(x[x["time"]=="15:10:00"][["date","close_px"]]
          .drop_duplicates("date").rename(columns={"close_px":"close_1510"}))
    panel=opens.merge(bars,on="date",how="outer").sort_values("date").reset_index(drop=True)
    prior_close=panel["close_1510"].shift(1)
    panel["prior_date"]=panel["date"].shift(1)
    panel["opening_gap"]=(panel["open_0915"]/prior_close)-1.0
    panel["feature_eligible"]=panel[["open_0915","close_1510","opening_gap","prior_date"]].notna().all(axis=1)
    panel["barrier_ok"]=panel["feature_eligible"] & (pd.to_datetime(panel["prior_date"]) < pd.to_datetime(panel["date"]))
    panel["direction"]=np.sign(panel["opening_gap"]).fillna(0).astype(int)
    panel["term_slope"]=np.nan
    panel["front_iv"]=np.nan
    panel["back_iv"]=np.nan
    panel["term_valid"]=False
    panel["term_fail_reason"]=""
    panel["state"]="INVERTED_TERM"
    return panel

def add_0930_spot(panel: pd.DataFrame, nifty: pd.DataFrame) -> pd.DataFrame:
    s = (nifty[nifty["time"] == "09:30:00"][["date", "close_px"]]
         .drop_duplicates("date").rename(columns={"close_px": "spot_0930"}))
    x = panel.drop(columns=["atm", "atm_0930"], errors="ignore").merge(s, on="date", how="left")
    x["atm"] = x["spot_0930"].map(lambda v: round_strike(v) if pd.notna(v) else np.nan)
    x["feature_eligible"] = x["feature_eligible"] & x["spot_0930"].notna() & x["atm"].notna()
    x["barrier_ok"] = x["barrier_ok"] & x["feature_eligible"]
    return x


def build_signals(panel: pd.DataFrame, null_seed: int | None = None) -> pd.DataFrame:
    x=panel.copy()
    if null_seed is not None:
        rng=np.random.default_rng(null_seed)
        vals=x["state"].to_numpy(dtype=object,copy=True)
        idx=np.flatnonzero(x["feature_eligible"].to_numpy())
        perm=vals[idx].copy(); rng.shuffle(perm); vals[idx]=perm; x["state"]=vals
    rows=[]
    for row in x.itertuples(index=False):
        if (not row.feature_eligible or not row.barrier_ok or row.state not in STATES
            or row.direction==0 or pd.isna(row.atm) or pd.isna(row.expiry)):
            continue
        for mapping in DIRECTIONS:
            side="CALL" if ((mapping=="CONTINUE" and row.direction>0) or (mapping=="FADE" and row.direction<0)) else "PUT"
            for horizon in HORIZONS:
                rows.append({"day":row.date,"state":row.state,"mapping":mapping,"horizon":horizon,
                    "opening_gap":float(row.opening_gap),"expiry":row.expiry,"atm":int(row.atm),"side":side,
                    "cell_id":cell_key(row.state,mapping,horizon),"null_seed":null_seed})
    return pd.DataFrame(rows)

def load_option_prices(root: Path, expiries: dict, signals: pd.DataFrame) -> dict:
    prices = {}
    if signals.empty:
        return prices
    con = duckdb.connect()
    con.execute("SET TimeZone='Asia/Kolkata'")
    for expiry, g in signals.groupby("expiry"):
        expiry = pd.Timestamp(expiry).date()
        if expiry not in expiries:
            continue
        path = str(expiries[expiry]).replace("'", "''")
        dates = sorted(pd.to_datetime(g["day"]).dt.date.unique().tolist())
        date_sql = ",".join(f"DATE '{d}'" for d in dates)
        strikes = set(float(v) for v in g["atm"].tolist())
        for r in g.itertuples(index=False):
            strikes.add(float(r.atm + (WING if r.side == "CALL" else -WING)))
        strike_sql = ",".join(str(v) for v in sorted(strikes))
        q = f"""
        WITH src AS (
            SELECT CAST(timestamp AS TIMESTAMP) ts,
                   CAST(CAST(timestamp AS TIMESTAMP) AS DATE) trade_date,
                   strftime(CAST(timestamp AS TIMESTAMP),'%H:%M:%S') local_time,
                   UPPER(CAST(option_type AS VARCHAR)) option_type,
                   CAST(strike AS DOUBLE) strike,
                   CAST(open AS DOUBLE) open_px,
                   CAST(close AS DOUBLE) close_px
            FROM read_parquet('{path}')
        )
        SELECT * FROM src
        WHERE trade_date IN ({date_sql})
          AND strike IN ({strike_sql})
          AND option_type IN ('CE','PE')
          AND local_time IN ('09:31:00','10:30:00','15:10:00')
          AND ((local_time='09:31:00' AND open_px>0)
               OR (local_time IN ('10:30:00','15:10:00') AND close_px>0))
        """
        z = con.execute(q).df()
        for r in z.itertuples(index=False):
            px = float(r.open_px) if r.local_time == "09:31:00" else float(r.close_px)
            prices[price_key(r.trade_date, expiry, r.option_type, r.strike, r.ts)] = px
    con.close()
    return prices


def trade_from_signal(row, prices, slippage: float):
    day = pd.Timestamp(row.day).date()
    expiry = pd.Timestamp(row.expiry).date()
    lot = lot_size(expiry)
    typ = "CE" if row.side == "CALL" else "PE"
    wing = row.atm + WING if row.side == "CALL" else row.atm - WING
    entry_ts = pd.Timestamp(f"{day} 09:31:00")
    exit_ts = pd.Timestamp(f"{day} {HORIZONS[row.horizon]}")
    legs = [(typ, row.atm, "BUY"), (typ, wing, "SELL")]

    raw = exec_gross = slippage_cost = transaction_costs = 0.0
    for opt, strike, action in legs:
        ep = prices.get(price_key(day, expiry, opt, strike, entry_ts))
        xp = prices.get(price_key(day, expiry, opt, strike, exit_ts))
        if ep is None or xp is None:
            return None

        if action == "BUY":
            executed_entry = ep + slippage
            executed_exit = max(0.0, xp - slippage)
            raw_leg = (xp - ep) * lot
            exec_leg = (executed_exit - executed_entry) * lot
            exit_action = "SELL"
        else:
            executed_entry = max(0.0, ep - slippage)
            executed_exit = xp + slippage
            raw_leg = (ep - xp) * lot
            exec_leg = (executed_entry - executed_exit) * lot
            exit_action = "BUY"

        raw += raw_leg
        exec_gross += exec_leg
        slippage_cost += raw_leg - exec_leg
        transaction_costs += charge(executed_entry, action, 1, lot, day)
        transaction_costs += charge(executed_exit, exit_action, 1, lot, day)

    return {
        "day": str(day),
        "cell_id": row.cell_id,
        "state": row.state,
        "mapping": row.mapping,
        "horizon": row.horizon,
        "side": row.side,
        "expiry": str(expiry),
        "lot": lot,
        "raw_gross": raw,
        "slippage_cost": slippage_cost,
        "transaction_costs": transaction_costs,
        "net_pnl": exec_gross - transaction_costs,
    }


def summarize(trades: pd.DataFrame, expected: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for c in cells():
        key = c.cell_id
        exp = expected[expected["cell_id"] == key] if not expected.empty else expected
        g = trades[trades["cell_id"] == key] if not trades.empty else trades.iloc[0:0]
        expected_n = len(exp)
        executed_n = len(g)
        coverage = executed_n / expected_n if expected_n else 0.0
        if g.empty:
            rows.append({
                "cell_id": key, "state": c.state, "mapping": c.mapping, "horizon": c.horizon,
                "expected_signals": expected_n, "executed_trades": 0, "execution_coverage": coverage,
                "weeks": 0, "total_net": 0.0, "mean_weekly_net": 0.0, "median_weekly_net": 0.0,
                "positive_week_rate": 0.0, "worst_trade": np.nan, "worst_week": np.nan,
                "max_drawdown": np.nan, "raw_gross": 0.0, "slippage_cost": 0.0, "transaction_costs": 0.0,
                "accounting_ok": True,
                "promotion_pass": False,
            })
            continue

        wk = (g.assign(week=pd.to_datetime(g["day"]).dt.to_period("W-SUN").astype(str))
              .groupby("week", as_index=True)["net_pnl"].sum())
        eq = wk.sort_index().cumsum()
        dd = eq - eq.cummax()
        reconciliation = np.isclose(
            g["net_pnl"].sum(),
            g["raw_gross"].sum() - g["slippage_cost"].sum() - g["transaction_costs"].sum(),
            atol=0.01,
        )
        mean_week = float(wk.mean())
        median_week = float(wk.median())
        pos_rate = float((wk > 0).mean())
        promotion = (
            coverage >= COVERAGE_TARGET
            and mean_week >= WEEKLY_TARGET
            and median_week >= WEEKLY_TARGET
            and pos_rate >= POSITIVE_WEEK_TARGET
        )
        rows.append({
            "cell_id": key, "state": c.state, "mapping": c.mapping, "horizon": c.horizon,
            "expected_signals": expected_n, "executed_trades": executed_n, "execution_coverage": coverage,
            "weeks": len(wk), "total_net": float(g["net_pnl"].sum()),
            "mean_weekly_net": mean_week, "median_weekly_net": median_week,
            "positive_week_rate": pos_rate, "worst_trade": float(g["net_pnl"].min()),
            "worst_week": float(wk.min()), "max_drawdown": float(dd.min()),
            "raw_gross": float(g["raw_gross"].sum()), "slippage_cost": float(g["slippage_cost"].sum()),
            "transaction_costs": float(g["transaction_costs"].sum()),
            "accounting_ok": bool(reconciliation), "promotion_pass": bool(promotion),
        })
    return pd.DataFrame(rows)


def data_gate(panel: pd.DataFrame, expiries: dict) -> dict:
    raw=len(panel)
    post=panel.iloc[LOOKBACK:] if len(panel)>LOOKBACK else panel.iloc[0:0]
    post_warmup=len(post)
    term_valid=int(post["term_valid"].sum())
    eligible=int(post["feature_eligible"].sum())
    complete=int((post["feature_eligible"] & post["barrier_ok"]).sum())
    violations=int((post["feature_eligible"] & ~post["barrier_ok"]).sum())
    term_cov=term_valid/post_warmup if post_warmup else 0.0
    feature_cov=eligible/post_warmup if post_warmup else 0.0
    keys=sorted(expiries)
    eligible_dates=post.loc[post["feature_eligible"],"date"]
    expiry_ok=int(sum(bisect.bisect_left(keys,d)<len(keys)-1 for d in eligible_dates))
    exp_cov=expiry_ok/eligible if eligible else 0.0
    status="PASS" if feature_cov>=COVERAGE_TARGET and term_cov>=COVERAGE_TARGET and exp_cov>=COVERAGE_TARGET and violations==0 else "FAIL"
    fail_counts={str(k):int(v) for k,v in post.loc[~post["term_valid"],"term_fail_reason"].value_counts().head(12).to_dict().items()}
    return {
        "status":status,
        "raw_sessions":raw,
        "post_warmup_sessions":post_warmup,
        "feature_eligible_sessions":eligible,
        "post_warmup_feature_eligibility_rate":feature_cov,
        "current_0930_term_structure_valid_sessions":term_valid,
        "current_0930_term_structure_coverage":term_cov,
        "feature_expiry_mapping_coverage":exp_cov,
        "prior_information_violations":violations,
        "study_start":str(START),
        "study_end":str(END),
        "required_coverage":COVERAGE_TARGET,
        "term_states":list(STATES),
        "term_definition":"back ATM IV minus front ATM IV at 09:30",
        "front_expiry":"nearest listed expiry on/after trade date",
        "back_expiry":"next listed expiry strictly after front",
        "expiry_file_count":len(expiries),
        "term_failure_reasons":fail_counts,
    }

def run(data: Path, out: Path, slippage: float, gate_only: bool = False):
    out.mkdir(parents=True, exist_ok=True)
    root = Path(data)
    nifty = load_nifty(root)
    panel = build_feature_panel(nifty)
    expiries = expiry_map(root)
    panel = add_0930_spot(panel, nifty)
    panel = attach_current_atm_term_structure(panel, root, expiries)
    panel = attach_expiry(panel, expiries)

    gate = data_gate(panel, expiries)
    panel.to_csv(out / "feature_panel.csv", index=False)
    (out / "data_gate.json").write_text(json.dumps(gate, indent=2, default=str), encoding="utf-8")
    if gate_only or gate["status"] != "PASS":
        return gate

    signals = build_signals(panel)
    signals.to_csv(out / "true_signals.csv", index=False)
    prices = load_option_prices(root, expiries, signals)

    rows = []
    for r in signals.itertuples(index=False):
        t = trade_from_signal(r, prices, slippage)
        if t is not None:
            rows.append(t)
    trades = pd.DataFrame(rows)
    trades.to_csv(out / "trades.csv", index=False)

    summary = summarize(trades, signals)
    summary["friction"] = "base" if slippage == 0.20 else "stress"
    summary.to_csv(out / f"true_cell_summary_{summary['friction'].iloc[0] if not summary.empty else ('base' if slippage == 0.20 else 'stress')}.csv", index=False)

    if not trades.empty:
        (trades.assign(week=pd.to_datetime(trades["day"]).dt.to_period("W-SUN").astype(str))
         .groupby(["cell_id", "week"], as_index=False)
         .net_pnl.sum().to_csv(out / "weekly.csv", index=False))

    null_signal_rows = []
    for seed in NULL_SEEDS:
        ns = build_signals(panel, null_seed=seed)
        if not ns.empty:
            ns = ns.copy()
            ns["null_seed"] = seed
            null_signal_rows.append(ns)
    null_signals = pd.concat(null_signal_rows, ignore_index=True) if null_signal_rows else pd.DataFrame()
    null_signals.to_csv(out / "null_signals.csv", index=False)

    null_trades_rows = []
    for r in null_signals.itertuples(index=False):
        t = trade_from_signal(r, prices, slippage)
        if t is not None:
            t["null_seed"] = int(r.null_seed)
            null_trades_rows.append(t)
    null_trades = pd.DataFrame(null_trades_rows)
    null_trades.to_csv(out / "null_trades.csv", index=False)
    if not null_trades.empty:
        nt = []
        for seed in NULL_SEEDS:
            g = null_trades[null_trades["null_seed"] == seed]
            s = summarize(g, null_signals[null_signals["null_seed"] == seed])
            s.insert(1, "null_seed", seed)
            nt.append(s)
        pd.concat(nt, ignore_index=True).to_csv(out / "null_summary.csv", index=False)

    cov = summary[["cell_id", "expected_signals", "executed_trades", "execution_coverage"]].copy()
    cov.to_csv(out / "price_coverage.csv", index=False)

    if not summary.empty:
        assert len(summary) == 8
        assert (summary["execution_coverage"] >= 0).all() and (summary["execution_coverage"] <= 1).all()
        assert summary["accounting_ok"].all()

    result = {
        **gate,
        "friction": "base" if slippage == 0.20 else "stress",
        "true_signal_count": int(len(signals)),
        "executed_trade_count": int(len(trades)),
        "promotion_pass_count": int(summary["promotion_pass"].sum()),
    }
    (out / "run_summary.json").write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--slippage", type=float, required=True)
    ap.add_argument("--gate-only", action="store_true")
    args = ap.parse_args()
    print(json.dumps(run(args.data, args.out, args.slippage, args.gate_only), indent=2, default=str))def attach_current_atm_term_structure(panel: pd.DataFrame, root: Path, expiries: dict) -> pd.DataFrame:
    x=panel.copy()
    keys=sorted(expiries)
    con=duckdb.connect()
    con.execute("SET TimeZone='Asia/Kolkata'")
    work=x[x["date"].notna() & x["spot_0930"].notna() & x["atm"].notna()].copy()
    rows=[]
    for d in work["date"].tolist():
        pos=bisect.bisect_left(keys,d)
        if pos>=len(keys)-1:
            continue
        front=keys[pos]
        back=keys[pos+1]
        rows.append((pd.Timestamp(d).date(),front,back))
    if rows:
        for front in sorted(set(r[1] for r in rows)):
            back_dates=sorted(set(r[2] for r in rows if r[1]==front))
            if not back_dates: continue
            dates=[r[0] for r in rows if r[1]==front]
            strikes=sorted(set(float(v) for v in work.loc[work["date"].isin(dates),"atm"].dropna().tolist()))
            if not dates or not strikes: continue
            date_sql=",".join(f"DATE '{d}'" for d in sorted(set(dates)))
            strike_sql=",".join(str(v) for v in strikes)
            for expiry in [front,back_dates[0]]:
                p=str(expiries[expiry]).replace("'","''")
                q=f"""
                  SELECT CAST(timestamp AS TIMESTAMP) ts,
                         CAST(CAST(timestamp AS TIMESTAMP) AS DATE) date,
                         UPPER(CAST(option_type AS VARCHAR)) option_type,
                         CAST(strike AS DOUBLE) strike,
                         CAST(close AS DOUBLE) close_px
                  FROM read_parquet('{p}')
                  WHERE CAST(timestamp AS DATE) IN ({date_sql})
                    AND strftime(CAST(timestamp AS TIMESTAMP),'%H:%M:%S')='09:30:00'
                    AND strike IN ({strike_sql})
                    AND UPPER(CAST(option_type AS VARCHAR)) IN ('CE','PE')
                """
                z=con.execute(q).df()
                if not z.empty:
                    z["expiry"]=expiry
                    rows_quotes=z if 'rows_quotes' in locals() else z
                    if 'quotes' not in locals():
                        quotes=z.copy()
                    else:
                        quotes=pd.concat([quotes,z],ignore_index=True)
    con.close()
    if 'quotes' not in locals():
        quotes=pd.DataFrame()
    qmap={}
    if not quotes.empty:
        for r in quotes.itertuples(index=False):
            qmap[(pd.Timestamp(r.date).date(),pd.Timestamp(r.expiry).date(),str(r.option_type).upper(),float(r.strike))]=float(r.close_px) if pd.notna(r.close_px) else np.nan

    x["term_slope"]=np.nan
    x["front_iv"]=np.nan
    x["back_iv"]=np.nan
    x["term_valid"]=False
    x["term_fail_reason"]=""
    for i,r in x.iterrows():
        if pd.isna(r["date"]) or pd.isna(r["spot_0930"]) or pd.isna(r["atm"]):
            x.at[i,"term_fail_reason"]="MISSING_0930_SPOT_OR_ATM"; continue
        d=pd.Timestamp(r["date"]).date()
        pos=bisect.bisect_left(keys,d)
        if pos>=len(keys)-1:
            x.at[i,"term_fail_reason"]="NO_FRONT_OR_BACK_EXPIRY"; continue
        front=keys[pos]; back=keys[pos+1]
        spot=float(r["spot_0930"]); strike=float(r["atm"])
        t_front=max((pd.Timestamp(f"{front} 15:30:00")-pd.Timestamp(f"{d} 09:30:00")).total_seconds()/31536000.0,1e-8)
        t_back=max((pd.Timestamp(f"{back} 15:30:00")-pd.Timestamp(f"{d} 09:30:00")).total_seconds()/31536000.0,1e-8)
        vals=[]
        for exp,t in [(front,t_front),(back,t_back)]:
            ce=qmap.get((d,pd.Timestamp(exp).date(),"CE",strike),np.nan)
            pe=qmap.get((d,pd.Timestamp(exp).date(),"PE",strike),np.nan)
            if not np.isfinite(ce) or ce<=0 or not np.isfinite(pe) or pe<=0:
                vals.append(None); continue
            ivce=implied_vol(spot,strike,t,float(ce),True)
            ivpe=implied_vol(spot,strike,t,float(pe),False)
            if ivce is None or ivpe is None:
                vals.append(None); continue
            vals.append((ivce+ivpe)*50.0)
        if vals[0] is None or vals[1] is None:
            x.at[i,"term_fail_reason"]="MISSING_FRONT_OR_BACK_ATM_IV"; continue
        x.at[i,"front_iv"]=vals[0]
        x.at[i,"back_iv"]=vals[1]
        x.at[i,"term_slope"]=vals[1]-vals[0]
        x.at[i,"term_valid"]=True
        x.at[i,"term_fail_reason"]="OK"
        x.at[i,"state"]="STEEP_TERM" if x.at[i,"term_slope"]>=0 else "INVERTED_TERM"
    x["feature_eligible"]=x["feature_eligible"] & x["term_valid"]
    x["barrier_ok"]=x["barrier_ok"] & x["feature_eligible"]
    x["feature_date"]=x["date"].astype(str)
    return x

