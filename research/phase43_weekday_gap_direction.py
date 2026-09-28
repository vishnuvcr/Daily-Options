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
STATES = ("MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY")
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
    opens=(x[x["time"]=="09:15:00"][["date","open_px"]].drop_duplicates("date")
           .rename(columns={"open_px":"open_0915"}))
    closes=(x[x["time"]=="15:10:00"][["date","close_px"]].drop_duplicates("date")
            .rename(columns={"close_px":"close_1510"}))
    panel=opens.merge(closes,on="date",how="outer").sort_values("date").reset_index(drop=True)
    panel["opening_gap"]=(panel["open_0915"]/panel["close_1510"].shift(1))-1.0
    panel["prior_date"]=panel["date"].shift(1)
    panel["weekday"]=pd.to_datetime(panel["date"]).dt.day_name().str.upper()
    panel["feature_eligible"]=panel[["open_0915","close_1510","opening_gap","prior_date"]].notna().all(axis=1)
    panel["barrier_ok"]=panel["feature_eligible"] & (pd.to_datetime(panel["prior_date"]) < pd.to_datetime(panel["date"]))
    panel["direction"]=np.sign(panel["opening_gap"]).astype(int)
    panel["state"]=panel["weekday"].where(panel["feature_eligible"],"NO_TRADE")
    panel["feature_date"]=panel["date"].astype(str)
    return panel
def build_signals(panel: pd.DataFrame, null_seed: int | None = None) -> pd.DataFrame:
    x=panel.copy()
    if null_seed is not None:
        rng=np.random.default_rng(null_seed)
        vals=x["state"].to_numpy(dtype=object,copy=True)
        idx=np.flatnonzero(x["feature_eligible"].to_numpy())
        perm=vals[idx].copy(); rng.shuffle(perm); vals[idx]=perm; x["state"]=vals
    rows=[]
    for row in x.itertuples(index=False):
        if not row.feature_eligible or not row.barrier_ok or row.state not in STATES or row.direction==0: continue
        for mapping in DIRECTIONS:
            side="CALL" if ((mapping=="CONTINUE" and row.direction>0) or (mapping=="FADE" and row.direction<0)) else "PUT"
            for horizon in HORIZONS:
                rows.append({"day":row.date,"state":row.state,"mapping":mapping,"horizon":horizon,
                    "opening_gap":float(row.opening_gap),"expiry":row.expiry if hasattr(row,"expiry") else None,
                    "atm":int(row.atm),"side":side,"cell_id":cell_key(row.state,mapping,horizon),"null_seed":null_seed})
    return pd.DataFrame(rows)

