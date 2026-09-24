from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from research.cost_model import OptionCostModel
from research.phase10_contracts import index_option_lot_size

MIN_TRADING_DAYS = 300
MIN_OVERLAP = 0.90

LEAD_WINDOWS = (1, 3)
THRESHOLDS = (0.75, 1.00, 1.50)
ENTRY_TIMES = ("09:45:00", "10:00:00")
EXPIRY_MODES = ("WEEK", "MONTH")
WIDTH_STEPS = (1, 2)
HOLDS = (10, 20, 30)
RISK_PROFILES = (
    {"stop_pct": 0.30, "target_pct": 0.60},
    {"stop_pct": 0.50, "target_pct": 1.00},
)

@dataclass(frozen=True)
class Variant:
    lead_window: int
    threshold: float
    entry_time: str
    expiry_mode: str
    width_steps: int
    hold_minutes: int
    risk_id: int

    @property
    def key(self) -> str:
        return (
            f"lw{self.lead_window}|z{self.threshold:.2f}|{self.entry_time}|"
            f"{self.expiry_mode}|w{self.width_steps}|h{self.hold_minutes}|r{self.risk_id}"
        )

def variant_grid() -> list[Variant]:
    return [
        Variant(lw, z, et, em, w, h, r)
        for lw in LEAD_WINDOWS
        for z in THRESHOLDS
        for et in ENTRY_TIMES
        for em in EXPIRY_MODES
        for w in WIDTH_STEPS
        for h in HOLDS
        for r in range(len(RISK_PROFILES))
    ]

def _utc_naive(series: pd.Series) -> pd.Series:
    x = pd.to_datetime(series, errors="coerce")
    if getattr(x.dt, "tz", None) is not None:
        return x.dt.tz_convert("UTC").dt.tz_localize(None)
    # Zenodo files are documented as NSE-local trade date/time fields.
    return x.dt.tz_localize("Asia/Kolkata", ambiguous="NaT", nonexistent="NaT").dt.tz_convert("UTC").dt.tz_localize(None)

def _read_table(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    if suffix not in {".txt", ".csv"}:
        raise ValueError(f"unsupported table suffix: {suffix}")

    raw = pd.read_csv(path, header=None, dtype=str, sep=",", on_bad_lines="skip")
    if raw.empty:
        return raw

    first = raw.iloc[0].astype(str).str.strip().str.lower().str.replace(" ", "_", regex=False).tolist()
    header_tokens = {"open", "high", "low", "close", "date", "time", "trade_date", "trade_time"}
    if set(first) & header_tokens:
        return pd.read_csv(path, sep=",", engine="python")

    cols = list(raw.columns)
    first_is_date = pd.to_datetime(raw[cols[0]], errors="coerce", dayfirst=False).notna().mean()
    second_is_date = pd.to_datetime(raw[cols[1]], errors="coerce", dayfirst=False).notna().mean() if len(cols) > 1 else 0.0

    if first_is_date >= 0.80:
        # Option record: [trade_date, trade_time, open, high, low, close, volume, open_interest]
        names = [
            "trade_date", "trade_time", "open", "high", "low",
            "close", "volume", "open_interest"
        ]
    elif second_is_date >= 0.80:
        # Market record: [symbol, trade_date, trade_time, open, high, low, close, volume, open_interest]
        names = [
            "symbol", "trade_date", "trade_time", "open", "high",
            "low", "close", "volume", "open_interest"
        ]
    else:
        raise ValueError("unsupported headerless schema: cannot identify date column")

    n = raw.shape[1]
    if n < 6:
        raise ValueError(f"unsupported headerless schema with {n} columns")
    if n <= len(names):
        raw.columns = names[:n]
    else:
        raw.columns = names + [f"extra_{i}" for i in range(n - len(names))]
    return raw

def _norm_cols(df: pd.DataFrame) -> dict[str, str]:
    return {str(c).strip().lower().replace(" ", "_").replace("-", "_"): c for c in df.columns}

def _combine_datetime(df: pd.DataFrame) -> pd.Series:
    m = _norm_cols(df)
    if "datetime" in m:
        return _utc_naive(df[m["datetime"]])
    date_col = next((m[k] for k in ("trade_date", "trade_dt", "date") if k in m), None)
    time_col = next((m[k] for k in ("trade_time", "time") if k in m), None)
    if date_col is None or time_col is None:
        raise ValueError("market file lacks date/time columns")
    return _utc_naive(df[date_col].astype(str) + " " + df[time_col].astype(str))

def _standardize_ohlc(df: pd.DataFrame) -> pd.DataFrame:
    m = _norm_cols(df)
    out = pd.DataFrame()

    # Header-based sources.
    if any(k in m for k in ("datetime", "trade_date", "date")):
        out["datetime"] = _combine_datetime(df)
        for k in ("open", "high", "low", "close", "volume"):
            src = m.get(k)
            if src is not None:
                out[k] = pd.to_numeric(df[src], errors="coerce")
    else:
        # Headerless Zenodo records:
        # market: [symbol, date, time, open, high, low, close, volume, oi]
        # option: [date, time, open, high, low, close, volume, oi]
        cols = list(df.columns)
        if len(cols) < 6:
            raise ValueError("headerless OHLC record has fewer than 6 columns")
        first_as_date = pd.to_datetime(df[cols[0]], errors="coerce", format="%Y/%m/%d").notna().mean()
        second_as_date = pd.to_datetime(df[cols[1]], errors="coerce", format="%Y/%m/%d").notna().mean() if len(cols) > 1 else 0.0
        if second_as_date >= 0.80:
            date_col, time_col, price_start = cols[1], cols[2], 3
        elif first_as_date >= 0.80:
            date_col, time_col, price_start = cols[0], cols[1], 2
        else:
            raise ValueError("unable to identify date/time columns in headerless OHLC file")
        out["datetime"] = _utc_naive(df[date_col].astype(str) + " " + df[time_col].astype(str))
        if price_start + 3 >= len(cols):
            raise ValueError("headerless OHLC record lacks OHLC columns")
        out["open"] = pd.to_numeric(df[cols[price_start]], errors="coerce")
        out["high"] = pd.to_numeric(df[cols[price_start + 1]], errors="coerce")
        out["low"] = pd.to_numeric(df[cols[price_start + 2]], errors="coerce")
        out["close"] = pd.to_numeric(df[cols[price_start + 3]], errors="coerce")
        if price_start + 4 < len(cols):
            out["volume"] = pd.to_numeric(df[cols[price_start + 4]], errors="coerce")

    return out.dropna(subset=["datetime", "close"]).loc[lambda x: x["close"] > 0].sort_values("datetime")

def load_zenodo_market(root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    files = [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in {".csv", ".txt", ".xlsx", ".xls"}]
    futures, spots = [], []
    for p in files:
        name = p.name.upper()
        stem = re.sub(r"[^A-Za-z0-9]", "", p.stem).upper()
        try:
            df = _standardize_ohlc(_read_table(p))
        except Exception:
            continue
        if df.empty:
            continue
        if name == "NIFTY_F1.CSV" or "NIFTYF1" in stem or stem.endswith("F1"):
            futures.append(df)
        elif name == "NIFTY.CSV" or (stem.startswith("NIFTY") and "F1" not in stem):
            spots.append(df)
    if not futures or not spots:
        raise RuntimeError(f"Unable to discover NIFTY_F1 and spot files. futures={len(futures)} spots={len(spots)}")
    f = pd.concat(futures, ignore_index=True).drop_duplicates("datetime", keep="last").sort_values("datetime")
    s = pd.concat(spots, ignore_index=True).drop_duplicates("datetime", keep="last").sort_values("datetime")
    f = f.rename(columns={"close": "futures_close"})
    s = s.rename(columns={"close": "spot_close"})
    return f, s

def data_gate(futures: pd.DataFrame, spot: pd.DataFrame) -> dict:
    f = futures.copy()
    s = spot.copy()
    dates = f["datetime"].dt.date.nunique()
    overlap = len(set(f["datetime"]).intersection(set(s["datetime"])))
    denom = min(len(f), len(s))
    ratio = overlap / denom if denom else 0.0
    return {
        "futures_rows": int(len(f)),
        "spot_rows": int(len(s)),
        "futures_trading_days": int(dates),
        "timestamp_overlap_rows": int(overlap),
        "timestamp_overlap_ratio_min_side": float(ratio),
        "gate": "PASS" if dates >= MIN_TRADING_DAYS and ratio >= MIN_OVERLAP else "FAIL",
        "contract_source_note": "Zenodo Nifty_F1 continuous first-month futures series; exact expiry identity is not present in the source row schema.",
    }

def lead_features(futures: pd.DataFrame, spot: pd.DataFrame, window: int) -> pd.DataFrame:
    x = futures[["datetime", "futures_close"]].merge(
        spot[["datetime", "spot_close"]], on="datetime", how="inner"
    ).sort_values("datetime").copy()
    fr = x["futures_close"].pct_change(window)
    sr = x["spot_close"].pct_change(window)
    fv = fr.rolling(60, min_periods=60).std()
    sv = sr.rolling(60, min_periods=60).std()
    x["fut_z"] = fr / fv.replace(0, np.nan)
    x["spot_z"] = sr / sv.replace(0, np.nan)
    x["lead_gap"] = x["fut_z"] - x["spot_z"]
    x["direction"] = np.where(x["fut_z"] > 0, "CALL", np.where(x["fut_z"] < 0, "PUT", ""))
    local = x["datetime"].dt.tz_localize("UTC").dt.tz_convert("Asia/Kolkata")
    x["trade_date"] = local.dt.date
    x["trade_time_ist"] = local.dt.strftime("%H:%M:%S")
    x["trade_time_utc"] = x["datetime"].dt.strftime("%H:%M:%S")
    return x

def _parse_expiry(parts: tuple[str, ...]) -> pd.Timestamp | None:
    month_map = {
        "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
        "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12,
    }
    candidates: list[pd.Timestamp] = []
    for part in parts:
        q = part.upper().replace("_", "-").replace("/", "-")
        for y, m, d in re.findall(r"(?<!\d)(20\d{2})-(\d{1,2})-(\d{1,2})(?!\d)", q):
            try:
                candidates.append(pd.Timestamp(year=int(y), month=int(m), day=int(d)))
            except Exception:
                pass
        for d, mon, y in re.findall(
            r"(?<!\d)(\d{1,2})-([A-Z]{3,9})-(\d{2,4})(?!\d)", q
        ):
            mon_num = month_map.get(mon[:3])
            if not mon_num:
                continue
            yy = int(y)
            yy = 2000 + yy if yy < 100 else yy
            try:
                candidates.append(pd.Timestamp(year=yy, month=mon_num, day=int(d)))
            except Exception:
                pass
        for d, m, y in re.findall(r"(?<!\d)(\d{1,2})-(\d{1,2})-(\d{2,4})(?!\d)", q):
            yy = int(y)
            yy = 2000 + yy if yy < 100 else yy
            try:
                candidates.append(pd.Timestamp(year=yy, month=int(m), day=int(d)))
            except Exception:
                pass
    return max(candidates).normalize() if candidates else None

def _last_thursday(year: int, month: int) -> pd.Timestamp:
    d = pd.Timestamp(year=year, month=month, day=1) + pd.offsets.MonthEnd(0)
    while d.weekday() != 3:
        d -= pd.Timedelta(days=1)
    return d.normalize()


def _path_coverage_dates(path: Path) -> tuple[pd.Timestamp | None, pd.Timestamp | None]:
    text = " ".join(path.parts)
    patterns = [
        r"(\d{1,2})-(\d{1,2})-(\d{2,4})\s+to\s+(\d{1,2})-(\d{1,2})-(\d{2,4})",
        r"(\d{1,2})-([A-Za-z]{3})-(\d{2,4})\s+to\s+(\d{1,2})-([A-Za-z]{3})-(\d{2,4})",
    ]
    out = []
    for pat in patterns:
        for m in re.finditer(pat, text, flags=re.IGNORECASE):
            g = m.groups()
            try:
                if len(g) == 6 and g[1].isdigit():
                    d1,m1,y1,d2,m2,y2 = map(int,g)
                else:
                    month_map = {"jan":1,"feb":2,"mar":3,"apr":4,"may":5,"jun":6,"jul":7,"aug":8,"sep":9,"oct":10,"nov":11,"dec":12}
                    d1,m1,y1,d2,m2,y2 = int(g[0]),month_map[g[1][:3].lower()],int(g[2]),int(g[3]),month_map[g[4][:3].lower()],int(g[5])
                y1 = 2000+y1 if y1 < 100 else y1
                y2 = 2000+y2 if y2 < 100 else y2
                out.append((pd.Timestamp(y1,m1,d1).normalize(), pd.Timestamp(y2,m2,d2).normalize()))
            except Exception:
                continue
    if not out:
        return None, None
    starts = [x[0] for x in out]
    ends = [x[1] for x in out]
    return min(starts), max(ends)

def discover_option_manifest(root: Path) -> pd.DataFrame:
    rows = []
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in {".csv", ".txt", ".xlsx", ".xls"}:
            continue
        stem = re.sub(r"[^A-Za-z0-9]", "", p.stem).upper()
        m = re.search(r"(?:NIFTY)?(?:(\d{4,6})(CE|PE)|((?:CE|PE))(\d{4,6}))$", stem)
        if not m:
            continue
        if m.group(1):
            strike = float(m.group(1))
            option_type = m.group(2)
        else:
            strike = float(m.group(4))
            option_type = m.group(3)
        expiry = _parse_expiry(tuple(p.parts))
        coverage_start, coverage_end = _path_coverage_dates(p)
        if expiry is None:
            continue
        expiry_type = "MONTH" if expiry == _last_thursday(expiry.year, expiry.month) else "WEEK"
        rows.append({
            "path": str(p),
            "strike": strike,
            "option_type": option_type,
            "expiry": expiry.date(),
            "expiry_type": expiry_type,
            "coverage_start": coverage_start.date() if coverage_start is not None else None,
            "coverage_end": coverage_end.date() if coverage_end is not None else None,
        })
    man = pd.DataFrame(rows).drop_duplicates(["path"]).sort_values(["expiry", "option_type", "strike", "path"])
    if man.empty:
        raise RuntimeError("No NIFTY option files discovered")
    return man

@lru_cache(maxsize=512)
def _load_option_path(path_str: str) -> pd.DataFrame:
    return _standardize_ohlc(_read_table(Path(path_str)))

def _coverage_columns(x: pd.DataFrame) -> pd.DataFrame:
    x = x.copy()
    if "coverage_start" not in x.columns:
        x["coverage_start"] = None
    if "coverage_end" not in x.columns:
        x["coverage_end"] = None
    return x


def _choose_expiry(manifest: pd.DataFrame, trade_date, mode: str):
    x = _coverage_columns(manifest)
    x = x[(x["expiry"] > trade_date) & (x["expiry_type"] == mode)]
    x = x[x["coverage_start"].isna() | (x["coverage_start"] <= trade_date)]
    x = x[x["coverage_end"].isna() | (x["coverage_end"] >= trade_date)]
    if x.empty:
        return None
    return x["expiry"].min()


def _choose_strikes(manifest: pd.DataFrame, expiry, side: str, spot: float, width_steps: int, trade_date):
    x = _coverage_columns(manifest)
    x = x[(x["expiry"] == expiry) & (x["option_type"] == side)].copy()
    x = x[x["coverage_start"].isna() | (x["coverage_start"] <= trade_date)]
    x = x[x["coverage_end"].isna() | (x["coverage_end"] >= trade_date)]
    if x.empty:
        return None
    strikes = np.sort(x["strike"].unique())
    if len(strikes) < width_steps + 1:
        return None
    atm = float(strikes[np.argmin(np.abs(strikes - spot))])
    if side == "CE":
        higher = strikes[strikes > atm]
        if len(higher) < width_steps:
            return None
        wing = float(higher[width_steps - 1])
    else:
        lower = strikes[strikes < atm]
        if len(lower) < width_steps:
            return None
        wing = float(lower[-width_steps])
    a = x[x["strike"] == atm].sort_values("path")
    w = x[x["strike"] == wing].sort_values("path")
    if a.empty or w.empty:
        return None
    return a.iloc[0], w.iloc[0]

@lru_cache(maxsize=2048)
def _load_merged_paths(path_a: str, path_b: str) -> pd.DataFrame:
    a = _load_option_path(path_a).rename(columns={"open":"open_a","high":"high_a","low":"low_a","close":"close_a"})
    b = _load_option_path(path_b).rename(columns={"open":"open_b","high":"high_b","low":"low_b","close":"close_b"})
    return a.merge(b, on="datetime", how="inner").sort_values("datetime")


def _merge_leg_bars(path_a: str, path_b: str, entry_time: pd.Timestamp, max_hold: int) -> pd.DataFrame:
    bars = _load_merged_paths(path_a, path_b)
    end = entry_time + pd.Timedelta(minutes=max_hold)
    return bars[(bars["datetime"] >= entry_time) & (bars["datetime"] <= end)].copy()

def build_entries(features_by_window: dict[int, pd.DataFrame], manifest: pd.DataFrame) -> pd.DataFrame:
    rows = []
    expiry_cache: dict[tuple[object, str], object] = {}
    strike_cache: dict[tuple[object, object, str], tuple[object, object] | None] = {}

    for v in variant_grid():
        x = features_by_window[v.lead_window]
        x = x[(x["trade_time_ist"] >= v.entry_time)].copy()
        x = x[(x["lead_gap"].abs() >= v.threshold)]
        x = x[((x["fut_z"] > 0) & (x["spot_z"] > 0)) | ((x["fut_z"] < 0) & (x["spot_z"] < 0))]

        for d, day in x.groupby("trade_date", sort=True):
            r = day.iloc[0]
            signal_time = r["datetime"]
            entry_time = signal_time + pd.Timedelta(minutes=1)

            expiry_key = (d, v.expiry_mode)
            if expiry_key not in expiry_cache:
                expiry_cache[expiry_key] = _choose_expiry(manifest, d, v.expiry_mode)
            expiry = expiry_cache[expiry_key]
            if expiry is None:
                continue

            side = "CE" if r["direction"] == "CALL" else "PE"
            strike_key = (d, expiry, side)
            if strike_key not in strike_cache:
                strike_cache[strike_key] = _choose_strikes(
                    manifest, expiry, side, float(r["spot_close"]), v.width_steps, d
                )

            pair = strike_cache[strike_key]
            if pair is None:
                continue

            # Width selection is the only variant-specific part of the cached strike universe.
            if v.width_steps == 1:
                pair = _choose_strikes(manifest, expiry, side, float(r["spot_close"]), 1, d)
            else:
                pair = _choose_strikes(manifest, expiry, side, float(r["spot_close"]), v.width_steps, d)
            if pair is None:
                continue

            p_atm, p_wing = pair
            rows.append({
                "variant_id": v.key,
                "trade_date": d,
                "signal_time": signal_time,
                "entry_time": entry_time,
                "direction": r["direction"],
                "expiry": expiry,
                "side": side,
                "atm_strike": float(p_atm["strike"]),
                "wing_strike": float(p_wing["strike"]),
                "atm_path": p_atm["path"],
                "wing_path": p_wing["path"],
                "spot": float(r["spot_close"]),
                "lead_gap": float(r["lead_gap"]),
                "lead_window": v.lead_window,
                "hold_minutes": v.hold_minutes,
                "risk_id": v.risk_id,
            })
    return pd.DataFrame(rows)

def simulate_unique(entries: pd.DataFrame, out: Path, slippage: float) -> pd.DataFrame:
    if entries.empty:
        return pd.DataFrame()

    cm = OptionCostModel()
    setup_cols = [
        "trade_date", "entry_time", "direction", "expiry", "side",
        "atm_strike", "wing_strike", "atm_path", "wing_path", "spot"
    ]

    # The same executable setup can be produced by multiple signal variants.
    # Simulate the setup once, then join its exact P&L back to every variant,
    # hold and risk cell that generated it.
    unique_setups = entries[setup_cols].drop_duplicates()
    rows = []

    for rec in unique_setups.itertuples(index=False):
        bars = _merge_leg_bars(rec.atm_path, rec.wing_path, pd.Timestamp(rec.entry_time), 30)
        if bars.empty:
            continue

        first = bars.iloc[0]
        long_entry = float(first["open_a"])
        short_entry = float(first["open_b"])
        debit = long_entry - short_entry
        if debit <= 0:
            continue

        for hold in HOLDS:
            slice_ = bars[bars["datetime"] <= pd.Timestamp(rec.entry_time) + pd.Timedelta(minutes=hold)]
            if slice_.empty:
                continue

            for risk_id, prof in enumerate(RISK_PROFILES):
                stop_level = debit * (1 - prof["stop_pct"])
                target_level = debit * (1 + prof["target_pct"])
                exit_ts = slice_["datetime"].iloc[-1]
                reason = "TIME"

                for _, bar in slice_.iterrows():
                    spread_high = float(bar["high_a"] - bar["low_b"])
                    spread_low = float(bar["low_a"] - bar["high_b"])
                    if spread_low <= stop_level:
                        exit_ts = bar["datetime"]
                        reason = "STOP"
                        break
                    if spread_high >= target_level:
                        exit_ts = bar["datetime"]
                        reason = "TARGET"
                        break

                ex = slice_.loc[slice_["datetime"] == exit_ts].iloc[-1]
                long_exit = float(ex["close_a"])
                short_exit = float(ex["close_b"])

                net = cm.vertical_debit_spread_net_pnl(
                    long_entry,
                    short_entry,
                    long_exit,
                    short_exit,
                    lot_size=index_option_lot_size("NIFTY", rec.expiry),
                    qty=1,
                    slippage_points=slippage,
                )

                rows.append({
                    **rec._asdict(),
                    "hold_minutes": hold,
                    "risk_id": risk_id,
                    "exit_time": exit_ts,
                    "reason": reason,
                    "entry_debit": debit,
                    "exit_debit": long_exit - short_exit,
                    "net_pnl": net,
                })

    setup_pnl = pd.DataFrame(rows)
    if setup_pnl.empty:
        trades = pd.DataFrame()
    else:
        trades = entries.merge(
            setup_pnl,
            on=setup_cols + ["hold_minutes", "risk_id"],
            how="inner",
            suffixes=("", "_sim"),
        )

    out.mkdir(parents=True, exist_ok=True)
    trades.to_csv(out / "phase12_zenodo_trades.csv", index=False)
    return trades

def leaderboard(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame()
    rows = []
    for v, g in trades.groupby("variant_id", sort=False):
        d = g.groupby("trade_date")["net_pnl"].sum()
        wins = g.loc[g.net_pnl > 0, "net_pnl"].sum()
        losses = -g.loc[g.net_pnl < 0, "net_pnl"].sum()
        rows.append({
            "variant_id": v,
            "trades": len(g),
            "active_days": int(d.size),
            "mean_active_day_net": float(d.mean()),
            "median_active_day_net": float(d.median()),
            "win_rate": float((g.net_pnl > 0).mean()),
            "positive_day_rate": float((d > 0).mean()),
            "profit_factor": float(wins / losses) if losses > 0 else 999.0,
            "max_drawdown": float((d.cumsum() - d.cumsum().cummax()).min()),
            "total_net": float(g.net_pnl.sum()),
        })
    return pd.DataFrame(rows).sort_values("mean_active_day_net", ascending=False).reset_index(drop=True)

def walk_forward(trades: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    if trades.empty:
        return pd.DataFrame(), {"gate": "NO_TRADES"}
    x = trades.copy()
    x["trade_date"] = pd.to_datetime(x["trade_date"]).dt.date
    dates = sorted(x["trade_date"].unique())
    train_len, val_len, embargo, test_len, step = 180, 60, 5, 60, 60
    rows = []
    start = 0
    while start + train_len + val_len + embargo + test_len <= len(dates):
        train_days = set(dates[start:start+train_len])
        val_days = set(dates[start+train_len:start+train_len+val_len])
        test_days = set(dates[start+train_len+val_len+embargo:start+train_len+val_len+embargo+test_len])
        tr = x[x.trade_date.isin(train_days)]
        va = x[x.trade_date.isin(val_days)]
        te = x[x.trade_date.isin(test_days)]
        train_scores = []
        for v, g in tr.groupby("variant_id"):
            if len(g) >= 8:
                train_scores.append((v, float(g.groupby("trade_date").net_pnl.sum().mean())))
        train_scores.sort(key=lambda q: q[1], reverse=True)
        val_scores = []
        for v, _ in train_scores[:12]:
            g = va[va.variant_id.eq(v)]
            if len(g) >= 5:
                val_scores.append((v, float(g.groupby("trade_date").net_pnl.sum().mean())))
        if not val_scores:
            start += step
            continue
        val_scores.sort(key=lambda q: q[1], reverse=True)
        selected = val_scores[0][0]
        g = te[te.variant_id.eq(selected)]
        if g.empty:
            start += step
            continue
        d = g.groupby("trade_date").net_pnl.sum()
        rows.append({
            "test_start": str(min(test_days)),
            "test_end": str(max(test_days)),
            "selected_variant": selected,
            "validation_mean": val_scores[0][1],
            "test_mean": float(d.mean()),
            "test_median": float(d.median()),
            "positive_day_rate": float((d > 0).mean()),
            "trade_days": int(d.size),
        })
        start += step
    wf = pd.DataFrame(rows)
    if wf.empty:
        return wf, {"walk_forward_windows": 0, "positive_test_windows": 0, "target_windows": 0, "mean_test_window_net": None, "gate": "FAIL_PRELIMINARY"}
    return wf, {
        "walk_forward_windows": int(len(wf)),
        "positive_test_windows": int((wf.test_mean > 0).sum()),
        "target_windows": int((wf.test_mean >= 1000).sum()),
        "mean_test_window_net": float(wf.test_mean.mean()),
        "median_test_window_net": float(wf.test_mean.median()),
        "gate": "PASS_PRELIMINARY" if wf.test_mean.mean() > 0 and (wf.test_mean >= 1000).any() else "FAIL_PRELIMINARY",
    }

def run(root: Path, out: Path, slippage: float) -> dict:
    market_root = root / "market"
    options_root = root / "options"
    futures, spot = load_zenodo_market(market_root)
    gate = data_gate(futures, spot)
    if gate["gate"] != "PASS":
        raise SystemExit(json.dumps(gate))
    features = {w: lead_features(futures, spot, w) for w in LEAD_WINDOWS}
    manifest = discover_option_manifest(options_root)
    entries = build_entries(features, manifest)
    trades = simulate_unique(entries, out, slippage)
    board = leaderboard(trades)
    board.to_csv(out / "phase12_zenodo_leaderboard.csv", index=False)
    wf, wfs = walk_forward(trades)
    wf.to_csv(out / "phase12_zenodo_walk_forward.csv", index=False)
    summary = {
        "variants": len(variant_grid()),
        "signals_entries": int(len(entries)),
        "trades": int(len(trades)),
        "target_qualified_prelim": int((board.mean_active_day_net >= 1000).sum()) if not board.empty else 0,
        "best": board.iloc[0].to_dict() if not board.empty else None,
        "walk_forward": wfs,
        "slippage_points_per_leg": slippage,
        "source": "Zenodo 10899828, 2019-2020 pilot",
        "contract_identity_note": "Futures leg uses source-provided Nifty_F1 continuous first-month series; exact expiry identity is unavailable in the published futures schema.",
    }
    (out / "phase12_zenodo_summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print(json.dumps(summary, indent=2, default=str))
    return summary

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--slippage", type=float, default=0.20)
    args = ap.parse_args()
    run(args.root, args.out, args.slippage)

if __name__ == "__main__":
    main()
