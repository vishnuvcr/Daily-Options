from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from research.cost_model import OptionCostModel
from research.phase10_contracts import index_option_lot_size
from research.phase12_zenodo_pilot import (
    load_zenodo_market,
    discover_option_manifest,
    _load_option_path,
    _coverage_columns,
)

GLOBAL_SETS = ("SP500", "GLOBAL3")
GLOBAL_Z_THRESHOLDS = (0.5, 1.0)
GAP_THRESHOLDS = (0.0025, 0.0050, 0.0075)
MODES = ("CONT", "FADE")
SIGNAL_TIMES = ("09:20:00", "09:30:00")
STRUCTURES = ("LONG", "DEBIT")
EXPIRY_MODES = ("WEEK", "MONTH")
HOLDS = (10, 20)
RISK_PROFILES = (
    {"stop_pct": 0.30, "target_pct": 0.60},
    {"stop_pct": 0.50, "target_pct": 1.00},
)


@dataclass(frozen=True)
class Variant:
    global_set: str
    global_z: float
    gap_threshold: float
    mode: str
    signal_time: str
    structure: str
    expiry_mode: str
    hold: int
    risk_id: int

    @property
    def key(self) -> str:
        return (
            f"{self.global_set}|gz{self.global_z:.1f}|gap{self.gap_threshold:.4f}|"
            f"{self.mode}|{self.signal_time}|{self.structure}|"
            f"{self.expiry_mode}|h{self.hold}|r{self.risk_id}"
        )


def variant_grid() -> list[Variant]:
    return [
        Variant(gs, gz, gap, mode, st, structure, em, hold, risk)
        for gs in GLOBAL_SETS
        for gz in GLOBAL_Z_THRESHOLDS
        for gap in GAP_THRESHOLDS
        for mode in MODES
        for st in SIGNAL_TIMES
        for structure in STRUCTURES
        for em in EXPIRY_MODES
        for hold in HOLDS
        for risk in range(len(RISK_PROFILES))
    ]


def load_global_data(root: Path) -> dict[str, pd.DataFrame]:
    out: dict[str, pd.DataFrame] = {}
    for name in ("SP500", "NASDAQ", "NIKKEI"):
        p = root / f"{name}.csv"
        if not p.exists():
            raise FileNotFoundError(p)
        df = pd.read_csv(p)
        if "Date" not in df.columns or "Close" not in df.columns:
            raise ValueError(f"{p} lacks Date/Close")
        df["date"] = pd.to_datetime(df["Date"], errors="coerce").dt.date
        df["close"] = pd.to_numeric(df["Close"], errors="coerce")
        df = df.dropna(subset=["date", "close"]).sort_values("date")
        df = df.drop_duplicates("date", keep="last")
        out[name] = df[["date", "close"]].copy()
    return out


def _daily_nifty(spot: pd.DataFrame) -> pd.DataFrame:
    x = spot.copy().sort_values("datetime")
    local = x["datetime"].dt.tz_localize("UTC").dt.tz_convert("Asia/Kolkata")
    x["date"] = local.dt.date
    x["time"] = local.dt.strftime("%H:%M:%S")
    daily = (
        x.groupby("date", sort=True)
        .agg(open=("spot_close", "first"), close=("spot_close", "last"))
        .reset_index()
    )
    daily["prev_close"] = daily["close"].shift(1)
    daily["gap_return"] = daily["open"] / daily["prev_close"] - 1.0
    return daily


def _global_zscore_series(df: pd.DataFrame) -> pd.DataFrame:
    x = df.sort_values("date").copy()
    x["ret"] = x["close"].pct_change()
    # The z-score for date D only uses returns through the preceding observation.
    mean = x["ret"].shift(1).rolling(20, min_periods=10).mean()
    std = x["ret"].shift(1).rolling(20, min_periods=10).std()
    x["z"] = (x["ret"] - mean) / std.replace(0, np.nan)
    return x[["date", "z"]]


def _last_before(global_df: pd.DataFrame, dates: pd.Series) -> pd.Series:
    left = pd.DataFrame({"date": pd.to_datetime(dates)})
    right = global_df.copy()
    right["date"] = pd.to_datetime(right["date"])
    merged = pd.merge_asof(
        left.sort_values("date"),
        right.sort_values("date"),
        on="date",
        direction="backward",
        allow_exact_matches=False,
    )
    return merged["z"].to_numpy()


def build_features(spot: pd.DataFrame, global_data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    x = spot.copy().sort_values("datetime")
    local = x["datetime"].dt.tz_localize("UTC").dt.tz_convert("Asia/Kolkata")
    x["trade_date"] = local.dt.date
    x["trade_time_ist"] = local.dt.strftime("%H:%M:%S")

    daily = _daily_nifty(spot)
    x = x.merge(daily[["date", "prev_close", "gap_return"]], left_on="trade_date", right_on="date", how="left")
    x["gap_signal"] = x["gap_return"]

    zmap = {name: _global_zscore_series(df) for name, df in global_data.items()}
    x["z_sp500"] = _last_before(zmap["SP500"], x["trade_date"])
    x["z_nasdaq"] = _last_before(zmap["NASDAQ"], x["trade_date"])
    x["z_nikkei"] = _last_before(zmap["NIKKEI"], x["trade_date"])
    x["global_sp500"] = x["z_sp500"]
    x["global_global3"] = x[["z_sp500", "z_nasdaq", "z_nikkei"]].mean(axis=1)
    return x


def _choose_expiry(manifest: pd.DataFrame, trade_date, mode: str):
    x = _coverage_columns(manifest)
    x = x[(x["expiry"] > trade_date) & (x["expiry_type"] == mode)]
    x = x[x["coverage_start"].isna() | (x["coverage_start"] <= trade_date)]
    x = x[x["coverage_end"].isna() | (x["coverage_end"] >= trade_date)]
    if x.empty:
        return None
    return x["expiry"].min()


def _choose_option(manifest: pd.DataFrame, expiry, side: str, spot: float, trade_date, spread: bool):
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
    a = x[x["strike"] == atm].sort_values("path")
    if a.empty:
        return None
    if not spread:
        return a.iloc[0], None

    if side == "CE":
        higher = strikes[strikes > atm]
        if len(higher) < 1:
            return None
        wing = float(higher[0])
    else:
        lower = strikes[strikes < atm]
        if len(lower) < 1:
            return None
        wing = float(lower[-1])

    w = x[x["strike"] == wing].sort_values("path")
    if w.empty:
        return None
    return a.iloc[0], w.iloc[0]


def build_entries(features: pd.DataFrame, manifest: pd.DataFrame) -> pd.DataFrame:
    rows = []
    cov = _coverage_columns(manifest)
    expiry_cache: dict[tuple[object, str], object] = {}
    eligible_cache: dict[tuple[object, object, str], pd.DataFrame] = {}

    for v in variant_grid():
        global_col = "global_sp500" if v.global_set == "SP500" else "global_global3"
        x = features[features["trade_time_ist"] >= v.signal_time].copy()
        x = x[x[global_col].abs() >= v.global_z]
        x = x[x["gap_signal"].abs() >= v.gap_threshold]

        same = np.sign(x[global_col]) == np.sign(x["gap_signal"])
        mode_ok = same if v.mode == "CONT" else ~same
        x = x[mode_ok]

        for d, day in x.groupby("trade_date", sort=True):
            r = day.iloc[0]
            expiry_key = (d, v.expiry_mode)
            if expiry_key not in expiry_cache:
                expiry_cache[expiry_key] = _choose_expiry(cov, d, v.expiry_mode)
            expiry = expiry_cache[expiry_key]
            if expiry is None:
                continue

            # CONT follows the global/gap direction; FADE trades against the gap.
            if v.mode == "CONT":
                direction_up = float(r[global_col]) > 0
            else:
                direction_up = float(r["gap_signal"]) < 0

            side = "CE" if direction_up else "PE"
            key = (d, expiry, side)
            if key not in eligible_cache:
                eligible = cov[(cov["expiry"] == expiry) & (cov["option_type"] == side)].copy()
                eligible = eligible[eligible["coverage_start"].isna() | (eligible["coverage_start"] <= d)]
                eligible = eligible[eligible["coverage_end"].isna() | (eligible["coverage_end"] >= d)]
                eligible_cache[key] = eligible

            eligible = eligible_cache[key]
            if eligible.empty:
                continue
            spot = float(r["spot_close"])
            strikes = np.sort(eligible["strike"].unique())
            atm = float(strikes[np.argmin(np.abs(strikes - spot))])
            a = eligible[eligible["strike"] == atm].sort_values("path")
            if a.empty:
                continue
            if v.structure == "LONG":
                p_atm = a.iloc[0]
                p_wing = None
            else:
                if side == "CE":
                    higher = strikes[strikes > atm]
                    if len(higher) < 1:
                        continue
                    wing = float(higher[0])
                else:
                    lower = strikes[strikes < atm]
                    if len(lower) < 1:
                        continue
                    wing = float(lower[-1])
                w = eligible[eligible["strike"] == wing].sort_values("path")
                if w.empty:
                    continue
                p_atm, p_wing = a.iloc[0], w.iloc[0]

            rows.append({
                "variant_id": v.key,
                "trade_date": d,
                "signal_time_actual": r["datetime"],
                "entry_time": r["datetime"] + pd.Timedelta(minutes=1),
                "direction": "CALL" if side == "CE" else "PUT",
                "expiry": expiry,
                "side": side,
                "atm_strike": atm,
                "wing_strike": None if p_wing is None else float(p_wing["strike"]),
                "atm_path": p_atm["path"],
                "wing_path": None if p_wing is None else p_wing["path"],
                "spot": spot,
                "hold_minutes": v.hold,
                "risk_id": v.risk_id,
            })
    return pd.DataFrame(rows)


@lru_cache(maxsize=8192)
def _window(path: str, entry_iso: str, hold: int) -> pd.DataFrame:
    df = _load_option_path(path)
    entry = pd.Timestamp(entry_iso)
    end = entry + pd.Timedelta(minutes=hold)
    return df[(df["datetime"] >= entry) & (df["datetime"] <= end)].copy()


@lru_cache(maxsize=8192)
def _spread_window(a: str, b: str, entry_iso: str, hold: int) -> pd.DataFrame:
    da = _window(a, entry_iso, hold).rename(columns={"open":"open_a","high":"high_a","low":"low_a","close":"close_a"})
    db = _window(b, entry_iso, hold).rename(columns={"open":"open_b","high":"high_b","low":"low_b","close":"close_b"})
    if da.empty or db.empty:
        return pd.DataFrame()
    return da.merge(db, on="datetime", how="inner").sort_values("datetime")


def _has_wing(value) -> bool:
    return pd.notna(value) and str(value).strip().lower() not in {"", "nan", "none"}


def simulate(entries: pd.DataFrame, slippage: float, out: Path) -> pd.DataFrame:
    if entries.empty:
        return pd.DataFrame()

    cm = OptionCostModel()
    setup_cols = [
        "trade_date", "entry_time", "expiry", "side", "atm_strike",
        "wing_strike", "atm_path", "wing_path", "spot", "hold_minutes", "risk_id"
    ]
    unique = entries[setup_cols].drop_duplicates()
    rows = []

    for rec in unique.itertuples(index=False):
        has_wing = _has_wing(rec.wing_path)
        entry_iso = str(rec.entry_time)
        bars = _spread_window(rec.atm_path, str(rec.wing_path), entry_iso, rec.hold_minutes) if has_wing else _window(rec.atm_path, entry_iso, rec.hold_minutes)
        if bars.empty:
            continue

        first = bars.iloc[0]
        entry_px = float(first["open_a"] - first["open_b"]) if has_wing else float(first["open"])
        if entry_px <= 0:
            continue

        for risk_id, prof in enumerate(RISK_PROFILES):
            stop_level = entry_px * (1 - prof["stop_pct"])
            target_level = entry_px * (1 + prof["target_pct"])
            exit_ts = bars["datetime"].iloc[-1]
            reason = "TIME"

            for _, bar in bars.iterrows():
                if has_wing:
                    high = float(bar["high_a"] - bar["low_b"])
                    low = float(bar["low_a"] - bar["high_b"])
                else:
                    high = float(bar["high"])
                    low = float(bar["low"])

                if low <= stop_level:
                    exit_ts = bar["datetime"]
                    reason = "STOP"
                    break
                if high >= target_level:
                    exit_ts = bar["datetime"]
                    reason = "TARGET"
                    break

            ex = bars[bars["datetime"] == exit_ts].iloc[-1]
            if has_wing:
                net = cm.vertical_debit_spread_net_pnl(
                    float(first["open_a"]), float(first["open_b"]),
                    float(ex["close_a"]), float(ex["close_b"]),
                    lot_size=index_option_lot_size("NIFTY", rec.expiry),
                    qty=1, slippage_points=slippage
                )
            else:
                net = cm.net_pnl(
                    float(first["open"]), float(ex["close"]),
                    qty=1, lot_size=index_option_lot_size("NIFTY", rec.expiry),
                    slippage_points=slippage
                )

            rows.append({**rec._asdict(), "risk_id": risk_id, "exit_time": exit_ts, "reason": reason, "entry_premium": entry_px, "net_pnl": net})

    sim = pd.DataFrame(rows)
    if sim.empty:
        trades = pd.DataFrame()
    else:
        trades = entries.merge(sim, on=setup_cols, how="inner", suffixes=("", "_sim"))
    out.mkdir(parents=True, exist_ok=True)
    trades.to_csv(out / "phase14_trades.csv", index=False)
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
    dates = sorted(x.trade_date.unique())
    train_len, val_len, embargo, test_len, step = 120, 40, 5, 40, 40
    rows = []
    start = 0
    while start + train_len + val_len + embargo + test_len <= len(dates):
        trd = set(dates[start:start+train_len])
        vad = set(dates[start+train_len:start+train_len+val_len])
        ted = set(dates[start+train_len+val_len+embargo:start+train_len+val_len+embargo+test_len])
        tr = x[x.trade_date.isin(trd)]
        va = x[x.trade_date.isin(vad)]
        te = x[x.trade_date.isin(ted)]

        train_scores = []
        for variant, g in tr.groupby("variant_id"):
            if len(g) >= 8:
                train_scores.append((variant, float(g.groupby("trade_date").net_pnl.sum().mean())))
        train_scores.sort(key=lambda q: q[1], reverse=True)

        validation = []
        for variant, _ in train_scores[:16]:
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
            "test_start": str(min(ted)),
            "test_end": str(max(ted)),
            "selected_variant": selected,
            "validation_mean": validation[0][1],
            "test_mean": float(d.mean()),
            "test_median": float(d.median()),
            "positive_day_rate": float((d > 0).mean()),
            "trade_days": int(d.size),
        })
        start += step
    return pd.DataFrame(rows)


def run(root: Path, global_root: Path, out: Path, slippage: float) -> dict:
    _, spot = load_zenodo_market(root / "market")
    global_data = load_global_data(global_root)
    features = build_features(spot, global_data)
    manifest = discover_option_manifest(root / "options")
    entries = build_entries(features, manifest)
    trades = simulate(entries, slippage, out)
    board = leaderboard(trades)
    board.to_csv(out / "phase14_leaderboard.csv", index=False)
    wf = walk_forward(trades)
    wf.to_csv(out / "phase14_walk_forward.csv", index=False)
    summary = {
        "variants": len(variant_grid()),
        "signals_entries": int(len(entries)),
        "trades": int(len(trades)),
        "target_qualified_prelim": int((board.mean_active_day_net >= 1000).sum()) if not board.empty else 0,
        "positive_cells": int((board.mean_active_day_net > 0).sum()) if not board.empty else 0,
        "best": board.iloc[0].to_dict() if not board.empty else None,
        "walk_forward_windows": int(len(wf)),
        "positive_test_windows": int((wf.test_mean > 0).sum()) if not wf.empty else 0,
        "target_test_windows": int((wf.test_mean >= 1000).sum()) if not wf.empty else 0,
        "mean_test_window_net": float(wf.test_mean.mean()) if not wf.empty else None,
        "slippage_points_per_leg": slippage,
        "source": "Zenodo 10899828 (NIFTY/options 2019-2020) + yfinance (^GSPC,^IXIC,^N225) daily global closes",
    }
    (out / "phase14_summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print(json.dumps(summary, indent=2, default=str))
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--global-root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--slippage", type=float, default=0.20)
    args = ap.parse_args()
    run(args.root, args.global_root, args.out, args.slippage)


if __name__ == "__main__":
    main()
