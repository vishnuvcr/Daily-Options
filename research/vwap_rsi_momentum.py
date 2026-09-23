from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from research.contracts import nifty_lot_size
from research.cost_model import OptionCostModel


@dataclass(frozen=True)
class Config:
    entry_minute: int
    required_conditions: int
    rsi_long: float
    rsi_short: float
    volume_ratio: float
    stop: float
    target: float
    hold: int
    trailing: bool


def add_features(day: pd.DataFrame) -> pd.DataFrame:
    x = day.sort_values("timestamp").copy()
    x["ema20"] = x.close.ewm(span=20, adjust=False).mean()
    x["ema50"] = x.close.ewm(span=50, adjust=False).mean()

    d = x.close.diff()
    up = d.clip(lower=0).ewm(alpha=1 / 14, adjust=False).mean()
    dn = -d.clip(upper=0).ewm(alpha=1 / 14, adjust=False).mean()
    rs = up.div(dn)
    x["rsi"] = (100 - 100 / (1 + rs)).where(
        dn != 0, np.where(up > 0, 100.0, 50.0)
    )

    tr = pd.concat(
        [
            x.high - x.low,
            (x.high - x.close.shift()).abs(),
            (x.low - x.close.shift()).abs(),
        ],
        axis=1,
    ).max(axis=1)
    x["atr_pct"] = tr.rolling(14).mean() / x.close
    x["atr_pctile"] = x.atr_pct.rolling(60, min_periods=20).rank(pct=True)
    return x


def add_option_features(day: pd.DataFrame) -> pd.DataFrame:
    x = day.sort_values("timestamp").copy()
    x["trade_date"] = x.timestamp.dt.date
    x["volume"] = pd.to_numeric(x.volume, errors="coerce").fillna(0).clip(lower=0)

    typical = (x.open + x.high + x.low + x.close) / 4
    x["pv"] = typical * x.volume

    group_keys = ["trade_date", "option_type", "strike"]
    grouped = x.groupby(group_keys, sort=False)
    x["cum_volume"] = grouped["volume"].cumsum()
    x["cum_pv"] = grouped["pv"].cumsum()
    x["option_vwap"] = x.cum_pv / x.cum_volume.replace(0, np.nan)
    x["volume_ma20"] = grouped["volume"].transform(
        lambda s: s.rolling(20, min_periods=10).mean()
    )
    x["vol_ratio"] = x.volume / x.volume_ma20.replace(0, np.nan)
    return x


def _nearest_strikes(spot_prices: np.ndarray, strikes: np.ndarray) -> np.ndarray:
    if len(strikes) == 1:
        return np.full(len(spot_prices), strikes[0], dtype=float)
    idx = np.searchsorted(strikes, spot_prices, side="left")
    idx = np.clip(idx, 0, len(strikes) - 1)
    left_idx = np.clip(idx - 1, 0, len(strikes) - 1)
    right_idx = idx
    left = strikes[left_idx]
    right = strikes[right_idx]
    choose_right = np.abs(right - spot_prices) < np.abs(spot_prices - left)
    return np.where(choose_right, right, left).astype(float)


def _merge_option_features(spot_features: pd.DataFrame, option_day: pd.DataFrame, option_type: str):
    left = spot_features[
        ["timestamp", "close", "ema20", "ema50", "rsi"]
    ].copy()
    strikes = np.asarray(
        sorted(option_day.loc[option_day.option_type == option_type, "strike"].dropna().unique()),
        dtype=float,
    )
    if len(strikes) == 0:
        return left.iloc[0:0].copy()

    left["strike"] = _nearest_strikes(left.close.to_numpy(dtype=float), strikes)
    left = left.sort_values("timestamp")

    right = option_day[
        option_day.option_type == option_type
    ][
        ["timestamp", "strike", "close", "option_vwap", "vol_ratio"]
    ].sort_values("timestamp")

    merged = pd.merge_asof(
        left,
        right,
        on="timestamp",
        by="strike",
        direction="backward",
        allow_exact_matches=True,
        suffixes=("_spot", "_option"),
    )
    return merged


def _first_signal(
    merged_ce: pd.DataFrame,
    merged_pe: pd.DataFrame,
    cfg: Config,
    day,
):
    start = pd.Timestamp(day) + pd.Timedelta(minutes=cfg.entry_minute)
    end = start + pd.Timedelta(minutes=45)

    candidates = []

    for typ, merged in (("CE", merged_ce), ("PE", merged_pe)):
        if merged.empty:
            continue
        z = merged[(merged.timestamp >= start) & (merged.timestamp <= end)].copy()
        if z.empty:
            continue
        z = z.replace([np.inf, -np.inf], np.nan).dropna(
            subset=["close_spot", "ema20", "ema50", "rsi", "close_option", "option_vwap", "vol_ratio"]
        )
        if z.empty:
            continue

        if typ == "CE":
            conds = [
                z.rsi > cfg.rsi_long,
                z.ema20 > z.ema50,
                z.close_option > z.option_vwap,
                z.vol_ratio >= cfg.volume_ratio,
            ]
        else:
            conds = [
                z.rsi < cfg.rsi_short,
                z.ema20 < z.ema50,
                z.close_option > z.option_vwap,
                z.vol_ratio >= cfg.volume_ratio,
            ]

        hits = sum(conds)
        hits = z.loc[hits >= cfg.required_conditions]
        if not hits.empty:
            row = hits.iloc[0]
            candidates.append(
                (
                    row.timestamp,
                    typ,
                    float(row.strike),
                    float(row.close_option),
                    float(row.option_vwap),
                    float(row.vol_ratio),
                )
            )

    return min(candidates, key=lambda r: r[0]) if candidates else None


def build_bases(spot, opt, configs):
    spot_days = {d: ds for d, ds in spot.groupby(spot.timestamp.dt.date)}
    opt_days = {
        d: add_option_features(do)
        for d, do in opt.groupby(opt.timestamp.dt.date)
    }

    signal_keys = sorted(
        {
            (
                cfg.entry_minute,
                cfg.required_conditions,
                cfg.rsi_long,
                cfg.rsi_short,
                cfg.volume_ratio,
            )
            for cfg in configs
        }
    )

    bases = []

    for d, ds in spot_days.items():
        do = opt_days.get(d)
        if do is None:
            continue

        x = add_features(ds)
        merged = {
            typ: _merge_option_features(x, do, typ)
            for typ in ("CE", "PE")
        }

        for entry, req, rsi_long, rsi_short, vol_ratio in signal_keys:
            cfg = Config(
                entry_minute=entry,
                required_conditions=req,
                rsi_long=rsi_long,
                rsi_short=rsi_short,
                volume_ratio=vol_ratio,
                stop=0.2,
                target=0.4,
                hold=60,
                trailing=False,
            )
            sig = _first_signal(merged["CE"], merged["PE"], cfg, d)
            if sig is None:
                continue

            st, typ, strike, signal_option_px, signal_option_vwap, signal_vol_ratio = sig

            # Enforce a one-minute delay: the signal uses information through
            # st, but execution starts with a later option bar.
            q = do[
                (do.option_type == typ)
                & (do.strike == strike)
                & (do.timestamp >= st + pd.Timedelta(minutes=1))
                & (do.timestamp <= st + pd.Timedelta(minutes=4))
                & (do.close > 0)
            ].sort_values("timestamp")
            if q.empty:
                continue

            entry_px = float(q.close.iloc[0])
            et = q.timestamp.iloc[0]
            path = do[
                (do.option_type == typ)
                & (do.strike == strike)
                & (do.timestamp > et)
                & (do.timestamp <= et + pd.Timedelta(minutes=90))
            ].sort_values("timestamp")
            if path.empty:
                continue

            bases.append(
                {
                    "date": d,
                    "entry_minute": entry,
                    "required_conditions": req,
                    "rsi_long": rsi_long,
                    "rsi_short": rsi_short,
                    "volume_ratio": vol_ratio,
                    "signal_time": st,
                    "signal_option_px": signal_option_px,
                    "signal_option_vwap": signal_option_vwap,
                    "signal_option_vol_ratio": signal_vol_ratio,
                    "entry": entry_px,
                    "entry_time": et,
                    "option_type": typ,
                    "strike": strike,
                    "lot": nifty_lot_size(d),
                    "path": path,
                }
            )

    return bases, sorted(spot_days.keys())


def precompute_outcomes(bases, configs, cm):
    risk_keys = sorted({(cfg.stop, cfg.target, cfg.hold) for cfg in configs})
    out = {}
    for i, b in enumerate(bases):
        path = b["path"]
        for stop, target, hold in risk_keys:
            p = path[path.timestamp <= b["entry_time"] + pd.Timedelta(minutes=hold)]
            if p.empty:
                continue

            stop_px = b["entry"] * (1 - stop)
            target_px = b["entry"] * (1 + target)
            exit_px = None

            for _, r in p.iterrows():
                if float(r.low) <= stop_px:
                    exit_px = stop_px
                    break
                if float(r.high) >= target_px:
                    exit_px = target_px
                    break

            if exit_px is None:
                exit_px = float(p.iloc[-1].close)

            out[(i, stop, target, hold)] = float(
                cm.net_pnl(b["entry"], exit_px, 1, b["lot"])
            )
    return out


def evaluate_bases(bases, all_dates, configs, outcomes):
    results = []

    for cfg in configs:
        daily = pd.Series(0.0, index=pd.Index(all_dates, name="date"))
        trade_wins = 0
        trade_count = 0
        active_net = []

        for i, b in enumerate(bases):
            if (
                b["entry_minute"],
                b["required_conditions"],
                b["rsi_long"],
                b["rsi_short"],
                b["volume_ratio"],
            ) != (
                cfg.entry_minute,
                cfg.required_conditions,
                cfg.rsi_long,
                cfg.rsi_short,
                cfg.volume_ratio,
            ):
                continue

            key = (i, cfg.stop, cfg.target, cfg.hold)
            if key not in outcomes:
                continue

            net = outcomes[key]
            daily.loc[b["date"]] += net
            active_net.append(net)
            trade_count += 1
            trade_wins += int(net > 0)

        if trade_count < max(60, int(0.45 * len(all_dates))):
            continue

        eq = daily.cumsum()
        dd = eq - eq.cummax()
        wins = daily[daily > 0].sum()
        losses = -daily[daily < 0].sum()

        results.append(
            {
                "entry_minute": cfg.entry_minute,
                "required_conditions": cfg.required_conditions,
                "rsi_long": cfg.rsi_long,
                "rsi_short": cfg.rsi_short,
                "volume_ratio": cfg.volume_ratio,
                "stop": cfg.stop,
                "target": cfg.target,
                "hold": cfg.hold,
                "trades": trade_count,
                "coverage": trade_count / len(all_dates),
                "mean_day_net": float(daily.mean()),
                "mean_active_net": float(np.mean(active_net)),
                "median_day_net": float(daily.median()),
                "p10_day_net": float(daily.quantile(0.10)),
                "positive_day_rate": float((daily > 0).mean()),
                "win_rate_trade": trade_wins / trade_count,
                "profit_factor": float(wins / losses) if losses else 999.0,
                "max_drawdown": float(dd.min()),
            }
        )

    board = pd.DataFrame(results)
    if not board.empty:
        board = board.sort_values(
            ["mean_day_net", "positive_day_rate", "profit_factor"],
            ascending=[False, False, False],
        )
    return board


def run(data, out):
    spot = pd.read_excel(data, sheet_name="Spot_1min")
    opt = pd.read_excel(data, sheet_name="ATM_Options_1min")

    spot["timestamp"] = pd.to_datetime(
        spot["Date"].astype(str) + " " + spot["Time"].astype(str),
        errors="coerce",
    )
    opt["timestamp"] = (
        pd.to_datetime(opt["Timestamp"], utc=True, errors="coerce")
        .dt.tz_convert("Asia/Kolkata")
        .dt.tz_localize(None)
    )

    spot = spot.rename(
        columns={
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        }
    ).dropna(subset=["timestamp", "close"])

    opt = opt.rename(
        columns={
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
            "Type": "option_type",
            "Strike": "strike",
        }
    ).dropna(subset=["timestamp", "close", "strike"])

    opt["option_type"] = (
        opt["option_type"]
        .astype(str)
        .str.upper()
        .replace({"CALL": "CE", "PUT": "PE", "C": "CE", "P": "PE"})
    )

    for col in ["open", "high", "low", "close", "volume", "strike"]:
        opt[col] = pd.to_numeric(opt[col], errors="coerce")

    configs = [
        Config(
            entry,
            req,
            rl,
            rs,
            vr,
            stop,
            target,
            hold,
            False,
        )
        for entry in (9 * 60 + 30, 9 * 60 + 45, 10 * 60, 10 * 60 + 15)
        for req in (3, 4)
        for rl, rs in ((55, 45), (60, 40))
        for vr in (1.0, 1.2, 1.5)
        for stop in (0.15, 0.20, 0.25)
        for target in (0.30, 0.40, 0.50)
        for hold in (30, 60, 90)
    ]

    cm = OptionCostModel()
    bases, all_dates = build_bases(spot, opt, configs)
    outcomes = precompute_outcomes(bases, configs, cm)
    board = evaluate_bases(bases, all_dates, configs, outcomes)

    out.mkdir(parents=True, exist_ok=True)
    board.head(300).to_csv(
        out / "vwap_rsi_momentum_leaderboard.csv", index=False
    )

    qualified = board[board.mean_day_net >= 1000] if not board.empty else pd.DataFrame()
    summary = {
        "calendar_days": len(all_dates),
        "trade_bases": len(bases),
        "variants_tested": len(configs),
        "target_daily_net_inr": 1000.0,
        "target_qualified_count": int(len(qualified)),
        "best": board.iloc[0].to_dict() if not board.empty else None,
        "feature_spec": "spot RSI + spot EMA trend + traded-option session-VWAP + traded-option volume-ratio",
        "methodology_correction": "NIFTY spot index volume is not used; option VWAP/volume are computed from actual option candles available at or before signal time; entries are delayed by at least one option minute; daily metrics include zero-trade days.",
    }
    (out / "vwap_rsi_momentum_summary.json").write_text(
        json.dumps(summary, indent=2, default=str)
    )
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=Path("reports"))
    args = ap.parse_args()
    run(args.data, args.out)
