from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

from research.cost_model import OptionCostModel
from research.phase10_contracts import index_option_lot_size
from research.phase12_zenodo_pilot import (
    load_zenodo_market,
    discover_option_manifest,
    _load_option_path,
)

SIGNAL_WINDOWS = (10, 15)
Z_THRESHOLDS = (1.0, 1.5)
VOL_PCTS = (60, 80)
SIGNAL_TIMES = ("14:45:00", "15:00:00", "15:15:00")
STRUCTURES = ("LONG", "DEBIT")
EXPIRY_MODES = ("WEEK", "MONTH")
HOLDS = (10, 20)
RISK_PROFILES = (
    {"stop_pct": 0.30, "target_pct": 0.60},
    {"stop_pct": 0.50, "target_pct": 1.00},
)
GLOBAL_Z_THRESHOLD = 0.5
GAP_THRESHOLD = 0.0075


@dataclass(frozen=True)
class Variant:
    window: int
    z: float
    vol_pct: int
    signal_time: str
    structure: str
    expiry_mode: str
    hold: int
    risk_id: int

    @property
    def key(self) -> str:
        return (
            f"w{self.window}|z{self.z:.1f}|vp{self.vol_pct}|{self.signal_time}|"
            f"{self.structure}|{self.expiry_mode}|h{self.hold}|r{self.risk_id}"
        )


def variant_grid() -> list[Variant]:
    return [
        Variant(w, z, vp, st, s, em, h, r)
        for w in SIGNAL_WINDOWS
        for z in Z_THRESHOLDS
        for vp in VOL_PCTS
        for st in SIGNAL_TIMES
        for s in STRUCTURES
        for em in EXPIRY_MODES
        for h in HOLDS
        for r in range(len(RISK_PROFILES))
    ]


def _feature_table(spot: pd.DataFrame) -> pd.DataFrame:
    x = spot[["datetime", "spot_close"]].copy().sort_values("datetime")
    local = x["datetime"].dt.tz_localize("UTC").dt.tz_convert("Asia/Kolkata")
    x["trade_date"] = local.dt.date
    x["trade_time_ist"] = local.dt.strftime("%H:%M:%S")

    ret_1 = x["spot_close"].pct_change()
    vol_60 = ret_1.rolling(60, min_periods=30).std()
    x["rv_1m"] = vol_60

    for w in SIGNAL_WINDOWS:
        rr = x["spot_close"].pct_change(w)
        x[f"z{w}"] = rr / vol_60.replace(0, np.nan)

    x["prior_30_high"] = x["spot_close"].rolling(30, min_periods=30).max().shift(1)
    x["prior_30_low"] = x["spot_close"].rolling(30, min_periods=30).min().shift(1)

    # Volatility state is estimated only from prior observations.
    x["rv_percentile"] = x["rv_1m"].rolling(390, min_periods=120).rank(pct=True) * 100.0
    return x


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


def _choose_option(manifest: pd.DataFrame, expiry, side: str, spot: float, trade_date, width_steps: int | None):
    x = _coverage_columns(manifest)
    x = x[(x["expiry"] == expiry) & (x["option_type"] == side)]
    x = x[x["coverage_start"].isna() | (x["coverage_start"] <= trade_date)]
    x = x[x["coverage_end"].isna() | (x["coverage_end"] >= trade_date)]
    if x.empty:
        return None

    strikes = np.sort(x["strike"].unique())
    if len(strikes) == 0:
        return None

    atm = float(strikes[np.argmin(np.abs(strikes - spot))])
    if width_steps is None:
        a = x[x["strike"] == atm].sort_values("path")
        return (a.iloc[0],) if not a.empty else None

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


def _signal_rows(features: pd.DataFrame, variant: Variant) -> pd.DataFrame:
    x = features[features["trade_time_ist"] >= variant.signal_time].copy()
    z = x[f"z{variant.window}"]
    direction_up = (
        (z >= variant.z)
        & (x["spot_close"] > x["prior_30_high"])
        & (x["rv_percentile"] >= variant.vol_pct)
    )
    direction_dn = (
        (z <= -variant.z)
        & (x["spot_close"] < x["prior_30_low"])
        & (x["rv_percentile"] >= variant.vol_pct)
    )
    return x.loc[direction_up | direction_dn].copy()


def build_entries(features: pd.DataFrame, manifest: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for v in variant_grid():
        sig = _signal_rows(features, v)
        for d, day in sig.groupby("trade_date", sort=True):
            r = day.iloc[0]
            expiry = _choose_expiry(manifest, d, v.expiry_mode)
            if expiry is None:
                continue
            side = "CE" if r[f"z{v.window}"] > 0 else "PE"
            width = None if v.structure == "LONG" else 1
            legs = _choose_option(
                manifest, expiry, side, float(r["spot_close"]), d, width
            )
            if legs is None:
                continue

            p_atm = legs[0]
            p_wing = None if width is None else legs[1]
            rows.append({
                "variant_id": v.key,
                "trade_date": d,
                "signal_time_actual": r["datetime"],
                "entry_time": r["datetime"] + pd.Timedelta(minutes=1),
                "direction": "CALL" if side == "CE" else "PUT",
                "expiry": expiry,
                "side": side,
                "atm_strike": float(p_atm["strike"]),
                "wing_strike": None if p_wing is None else float(p_wing["strike"]),
                "atm_path": p_atm["path"],
                "wing_path": None if p_wing is None else p_wing["path"],
                "spot": float(r["spot_close"]),
                "hold_minutes": v.hold,
                "risk_id": v.risk_id,
            })
    return pd.DataFrame(rows)


@lru_cache(maxsize=4096)
def _window_bars(path: str, entry_time_iso: str, hold: int) -> pd.DataFrame:
    df = _load_option_path(path)
    entry = pd.Timestamp(entry_time_iso)
    end = entry + pd.Timedelta(minutes=hold)
    return df[(df["datetime"] >= entry) & (df["datetime"] <= end)].copy()


@lru_cache(maxsize=4096)
def _spread_window(a: str, b: str, entry_iso: str, hold: int) -> pd.DataFrame:
    da = _window_bars(a, entry_iso, hold).rename(
        columns={"open": "open_a", "high": "high_a", "low": "low_a", "close": "close_a"}
    )
    db = _window_bars(b, entry_iso, hold).rename(
        columns={"open": "open_b", "high": "high_b", "low": "low_b", "close": "close_b"}
    )
    if da.empty or db.empty:
        return pd.DataFrame()
    return da.merge(db, on="datetime", how="inner").sort_values("datetime")



def _load_global_series(root: Path, name: str, symbol: str) -> pd.DataFrame:
    root.mkdir(parents=True, exist_ok=True)
    p = root / f"{name}.csv"
    if not p.exists() or p.stat().st_size < 100:
        df = yf.download(symbol, start="2018-01-01", end="2021-01-01", auto_adjust=False, progress=False)
        if df.empty:
            raise RuntimeError(f"No global data for {symbol}")
        if hasattr(df.columns, "levels"):
            if "Close" not in df.columns.get_level_values(0):
                raise RuntimeError(f"No Close for {symbol}")
            df = df["Close"]
            if hasattr(df, "columns"):
                df = df.iloc[:, 0]
        else:
            df = df["Close"]
        df.rename("Close").reset_index().to_csv(p, index=False)

    x = pd.read_csv(p)
    x["date"] = pd.to_datetime(x["Date"], errors="coerce").dt.date
    x["close"] = pd.to_numeric(x["Close"], errors="coerce")
    x = x.dropna(subset=["date", "close"]).sort_values("date").drop_duplicates("date", keep="last")
    x["ret"] = x["close"].pct_change()
    mean = x["ret"].shift(1).rolling(20, min_periods=10).mean()
    std = x["ret"].shift(1).rolling(20, min_periods=10).std()
    x["z"] = (x["ret"] - mean) / std.replace(0, np.nan)
    return x[["date", "z"]].dropna()


def _previous_global_z(df: pd.DataFrame, dates: pd.Series) -> pd.Series:
    left = pd.DataFrame({"date": pd.to_datetime(dates)})
    right = df.copy()
    right["date"] = pd.to_datetime(right["date"])
    m = pd.merge_asof(
        left.sort_values("date"),
        right.sort_values("date"),
        on="date",
        direction="backward",
        allow_exact_matches=False,
    )
    return m["z"].to_numpy()


def global_gate_table(spot: pd.DataFrame, root: Path) -> pd.DataFrame:
    x = spot[["datetime", "spot_close"]].copy().sort_values("datetime")
    local = pd.to_datetime(x["datetime"], utc=True).dt.tz_convert("Asia/Kolkata").dt.tz_localize(None)
    x["trade_date"] = local.dt.date
    daily = (
        x.groupby("trade_date", sort=True)
        .agg(day_open=("spot_close", "first"), day_close=("spot_close", "last"))
        .reset_index()
    )
    daily["prev_close"] = daily["day_close"].shift(1)
    daily["gap_return"] = daily["day_open"] / daily["prev_close"] - 1.0

    sp = _load_global_series(root, "SP500", "^GSPC")
    nq = _load_global_series(root, "NASDAQ", "^IXIC")
    nk = _load_global_series(root, "NIKKEI", "^N225")

    daily["z_sp500"] = _previous_global_z(sp, daily["trade_date"])
    daily["z_nasdaq"] = _previous_global_z(nq, daily["trade_date"])
    daily["z_nikkei"] = _previous_global_z(nk, daily["trade_date"])
    daily["global3_z"] = daily[["z_sp500", "z_nasdaq", "z_nikkei"]].mean(axis=1)
    daily["pass_gate"] = (
        daily["global3_z"].abs().ge(GLOBAL_Z_THRESHOLD)
        & daily["gap_return"].abs().ge(GAP_THRESHOLD)
    )
    return daily

def simulate(entries: pd.DataFrame, slippage: float, out: Path) -> pd.DataFrame:
    if entries.empty:
        return pd.DataFrame()

    cm = OptionCostModel()
    keys = [
        "trade_date", "entry_time", "expiry", "side", "atm_strike", "wing_strike",
        "atm_path", "wing_path", "spot", "hold_minutes", "risk_id"
    ]
    unique = entries[keys].drop_duplicates()

    rows = []
    for rec in unique.itertuples(index=False):
        entry_iso = str(rec.entry_time)
        is_spread = isinstance(rec.wing_path, str) and bool(rec.wing_path)
        bars = (
            _spread_window(rec.atm_path, rec.wing_path, entry_iso, rec.hold_minutes)
            if is_spread
            else _window_bars(rec.atm_path, entry_iso, rec.hold_minutes)
        )
        if bars.empty:
            continue

        first = bars.iloc[0]
        entry_px = (
            float(first["open_a"] - first["open_b"])
            if is_spread
            else float(first["open"])
        )
        if entry_px <= 0:
            continue

        risk_id = int(rec.risk_id)
        prof = RISK_PROFILES[risk_id]
        stop_level = entry_px * (1 - prof["stop_pct"])
        target_level = entry_px * (1 + prof["target_pct"])
        exit_ts = bars["datetime"].iloc[-1]
        reason = "TIME"

        for _, bar in bars.iterrows():
            high = (
                float(bar["high_a"] - bar["low_b"])
                if is_spread
                else float(bar["high"])
            )
            low = (
                float(bar["low_a"] - bar["high_b"])
                if is_spread
                else float(bar["low"])
            )
            if low <= stop_level:
                exit_ts = bar["datetime"]
                reason = "STOP"
                break
            if high >= target_level:
                exit_ts = bar["datetime"]
                reason = "TARGET"
                break

        ex = bars[bars["datetime"] == exit_ts].iloc[-1]
        lot = index_option_lot_size("NIFTY", rec.expiry)

        if is_spread:
            net = cm.vertical_debit_spread_net_pnl(
                float(first["open_a"]),
                float(first["open_b"]),
                float(ex["close_a"]),
                float(ex["close_b"]),
                lot_size=lot,
                qty=1,
                slippage_points=slippage,
            )
            exit_px = float(ex["close_a"] - ex["close_b"])
        else:
            net = cm.net_pnl(
                float(first["open"]),
                float(ex["close"]),
                qty=1,
                lot_size=lot,
                slippage_points=slippage,
            )
            exit_px = float(ex["close"])

        rows.append({
            **rec._asdict(),
            "exit_time": exit_ts,
            "reason": reason,
            "entry_premium": entry_px,
            "exit_premium": exit_px,
            "net_pnl": net,
        })

    trades = entries.merge(
        pd.DataFrame(rows),
        on=keys,
        how="inner",
        suffixes=("", "_sim"),
    )
    out.mkdir(parents=True, exist_ok=True)
    trades.to_csv(out / "phase13_trades.csv", index=False)
    return trades

def leaderboard(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame()
    rows = []
    for variant, g in trades.groupby("variant_id", sort=False):
        d = g.groupby("trade_date")["net_pnl"].sum()
        wins = g.loc[g.net_pnl > 0, "net_pnl"].sum()
        losses = -g.loc[g.net_pnl < 0, "net_pnl"].sum()
        rows.append({
            "variant_id": variant,
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
    return pd.DataFrame(rows).sort_values("mean_active_day_net", ascending=False)


def walk_forward(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame()
    x = trades.copy()
    x["trade_date"] = pd.to_datetime(x["trade_date"]).dt.date
    dates = sorted(x["trade_date"].unique())
    train_len, val_len, embargo, test_len, step = 120, 40, 5, 40, 40
    rows = []
    start = 0
    while start + train_len + val_len + embargo + test_len <= len(dates):
        tr_days = set(dates[start:start+train_len])
        va_days = set(dates[start+train_len:start+train_len+val_len])
        te_days = set(dates[start+train_len+val_len+embargo:start+train_len+val_len+embargo+test_len])
        tr = x[x.trade_date.isin(tr_days)]
        va = x[x.trade_date.isin(va_days)]
        te = x[x.trade_date.isin(te_days)]

        scores = []
        for variant, g in tr.groupby("variant_id"):
            if len(g) >= 8:
                scores.append((variant, float(g.groupby("trade_date").net_pnl.sum().mean())))
        scores.sort(key=lambda q: q[1], reverse=True)

        validation = []
        for variant, _ in scores[:16]:
            g = va[va.variant_id.eq(variant)]
            if len(g) >= 5:
                validation.append((variant, float(g.groupby("trade_date").net_pnl.sum().mean())))
        if not validation:
            start += step
            continue

        validation.sort(key=lambda q: q[1], reverse=True)
        selected = validation[0][0]
        g = te[te.variant_id.eq(selected)]
        if g.empty:
            start += step
            continue
        d = g.groupby("trade_date").net_pnl.sum()
        rows.append({
            "test_start": str(min(te_days)),
            "test_end": str(max(te_days)),
            "selected_variant": selected,
            "validation_mean": validation[0][1],
            "test_mean": float(d.mean()),
            "test_median": float(d.median()),
            "positive_day_rate": float((d > 0).mean()),
            "trade_days": int(d.size),
        })
        start += step
    return pd.DataFrame(rows)


def run(root: Path, out: Path, slippage: float, global_root: Path | None = None) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    _, spot = load_zenodo_market(root / "market")
    features = _feature_table(spot)
    manifest = discover_option_manifest(root / "options")
    entries = build_entries(features, manifest)

    gate_days = None
    if global_root is not None:
        gate = global_gate_table(spot, global_root)
        gate_days = int(gate["pass_gate"].sum())
        entries = entries.merge(gate[["trade_date", "pass_gate"]], on="trade_date", how="inner")
        entries = entries[entries["pass_gate"]].drop(columns=["pass_gate"])

    trades = simulate(entries, slippage, out)
    board = leaderboard(trades)
    board.to_csv(out / "phase13_leaderboard.csv", index=False)
    wf = walk_forward(trades)
    wf.to_csv(out / "phase13_walk_forward.csv", index=False)

    summary = {
        "variants": len(variant_grid()),
        "signals_entries": int(len(entries)),
        "trades": int(len(trades)),
        "target_qualified_prelim": int((board.mean_active_day_net >= 1000).sum()) if not board.empty else 0,
        "best": board.iloc[0].to_dict() if not board.empty else None,
        "walk_forward_windows": int(len(wf)),
        "positive_test_windows": int((wf.test_mean > 0).sum()) if not wf.empty else 0,
        "target_test_windows": int((wf.test_mean >= 1000).sum()) if not wf.empty else 0,
        "mean_test_window_net": float(wf.test_mean.mean()) if not wf.empty else None,
        "slippage_points_per_leg": slippage,
        "source": "Zenodo 10899828, 2019-2020 pilot",
        "global_gate_z_threshold": GLOBAL_Z_THRESHOLD if global_root is not None else None,
        "global_gate_gap_threshold": GAP_THRESHOLD if global_root is not None else None,
        "global_gate_days": gate_days,
    }
    (out / "phase13_summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print(json.dumps(summary, indent=2, default=str))
    return summary

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--slippage", type=float, default=0.20)
    ap.add_argument("--global-root", type=Path, default=None)
    args = ap.parse_args()
    run(args.root, args.out, args.slippage, args.global_root)


if __name__ == "__main__":
    main()
