from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from research.contracts import nifty_lot_size
from research.cost_model import OptionCostModel
from research.walk_forward import expanding_windows, block_bootstrap_mean


ENTRY_MINUTES = (30, 45, 60)  # 09:45, 10:00, 10:15 IST
STOP_MULTS = (1.6, 1.8, 2.0)
TARGET_DECAYS = (0.35, 0.45, 0.55)
HOLDS = (120, 180)
GAP_MAXS = (0.005, None)
R15_MAXS = (0.005, None)
IVRV_MINS = (0.0, 0.5)
FILTERS = [
    (g, r, v)
    for g in GAP_MAXS
    for r in R15_MAXS
    for v in IVRV_MINS
]


def source_glob(root: Path) -> str:
    return (root / "**" / "*.parquet").as_posix()


def load_observations(root: Path) -> tuple[pd.DataFrame, dict[str, pd.DatetimeIndex]]:
    source = source_glob(root)
    sql = f"""
    SELECT
      datetime,
      CAST(date AS DATE) AS trade_date,
      expiry_type,
      option_type,
      strike_type,
      CAST(strike_price AS DOUBLE) AS strike_price,
      CAST(spot AS DOUBLE) AS spot,
      CAST(iv AS DOUBLE) AS iv,
      CAST(high AS DOUBLE) AS high,
      CAST(low AS DOUBLE) AS low,
      CAST(close AS DOUBLE) AS close
    FROM read_parquet('{source}', union_by_name=true)
    WHERE close > 0
      AND STRFTIME(datetime + INTERVAL '5 hours 30 minutes','%H:%M:%S')
          BETWEEN '09:15:00' AND '13:45:00'
    """
    con = duckdb.connect()
    raw = con.execute(sql).df()
    con.close()
    raw["datetime"] = pd.to_datetime(raw["datetime"]) + pd.Timedelta(hours=5, minutes=30)
    raw["trade_date"] = pd.to_datetime(raw["trade_date"])

    spot = (
        raw[["datetime","trade_date","spot"]]
        .drop_duplicates(["trade_date","datetime"], keep="last")
        .sort_values(["trade_date","datetime"])
    )
    opt = raw.copy().sort_values(["trade_date","datetime"])

    prev_close = (
        spot.groupby("trade_date")["spot"].last()
        .shift(1)
    )
    spot["prev_close"] = spot["trade_date"].map(prev_close)
    daily = spot.groupby("trade_date").agg(
        first_spot=("spot","first"),
        last_spot=("spot","last"),
        high15=("spot","max"),
        low15=("spot","min"),
    )
    daily["prev_close"] = daily["last_spot"].shift(1)
    first15 = spot[
        spot.datetime.dt.time.between(
            pd.Timestamp("09:15").time(),
            pd.Timestamp("09:29").time(),
            inclusive="both",
        )
    ].groupby("trade_date")["spot"].agg(["max","min"])
    daily["r15"] = (first15["max"] - first15["min"]) / daily["first_spot"]
    daily["gap"] = (daily["first_spot"] - daily["prev_close"]).abs() / daily["prev_close"].abs()
    daily = daily.reset_index()

    observations = []
    for (d, expiry), od in opt.groupby(["trade_date","expiry_type"], sort=True):
        day_spot = spot[spot.trade_date == d].sort_values("datetime")
        if day_spot.empty:
            continue
        base = daily[daily.trade_date == d]
        if base.empty:
            continue
        gap = float(base.gap.iloc[0]) if np.isfinite(base.gap.iloc[0]) else np.nan
        r15 = float(base.r15.iloc[0]) if np.isfinite(base.r15.iloc[0]) else np.nan

        for entry_min in ENTRY_MINUTES:
            entry_time = pd.Timestamp(d) + pd.Timedelta(hours=9, minutes=15 + entry_min)
            q = od[(od.datetime >= entry_time) & (od.datetime <= entry_time + pd.Timedelta(minutes=2))]
            ce = q[q.option_type == "CALL"].dropna(subset=["strike_price","close"]).sort_values("datetime")
            pe = q[q.option_type == "PUT"].dropna(subset=["strike_price","close"]).sort_values("datetime")
            if ce.empty or pe.empty:
                continue
            common_strikes = sorted(set(ce.strike_price) & set(pe.strike_price))
            if not common_strikes:
                continue
            spot_at_entry = float(
                day_spot.loc[day_spot.datetime >= entry_time, "spot"].iloc[0]
            ) if not day_spot.loc[day_spot.datetime >= entry_time, "spot"].empty else open_spot
            strike = float(min(common_strikes, key=lambda k: abs(k - spot_at_entry)))
            ce_row = ce[ce.strike_price == strike].iloc[0]
            pe_row = pe[pe.strike_price == strike].iloc[0]
            ce_ts = pd.Timestamp(ce_row.datetime)
            pe_ts = pd.Timestamp(pe_row.datetime)
            et = max(ce_ts, pe_ts)
            ce0 = float(ce_row.close)
            pe0 = float(pe_row.close)
            ivs = pd.Series([ce_row.iv, pe_row.iv]).dropna()
            entry = ce0 + pe0
            if entry <= 0 or ivs.empty:
                continue

            hist = day_spot[(day_spot.datetime < et) & (day_spot.datetime >= et - pd.Timedelta(minutes=30))].spot
            rv = float(hist.pct_change().dropna().std() * np.sqrt(252*375) * 100) if len(hist) >= 15 else np.nan
            iv_rv = float(ivs.mean() / rv) if np.isfinite(rv) and rv > 0 else np.nan

            path = od[
                (od.datetime > et)
                & (od.datetime <= et + pd.Timedelta(minutes=max(HOLDS)))
                & (od.strike_price == strike)
            ]
            piv = path.pivot_table(
                index="datetime",
                columns="option_type",
                values=["high","low","close"],
                aggfunc="last",
            )
            if piv.empty or not {"CALL","PUT"}.issubset(set(piv["close"].columns)):
                continue
            piv = piv.dropna(subset=[("close","CALL"),("close","PUT")])
            if piv.empty:
                continue

            observations.append(
                {
                    "obs_id": len(observations),
                    "trade_date": pd.Timestamp(d),
                    "expiry_type": expiry,
                    "entry_min": entry_min,
                    "entry": entry,
                    "gap": gap,
                    "r15": r15,
                    "iv_rv": iv_rv,
                    "lot": nifty_lot_size(d),
                    "hi": piv[("high","CALL")].to_numpy(float) + piv[("high","PUT")].to_numpy(float),
                    "lo": piv[("low","CALL")].to_numpy(float) + piv[("low","PUT")].to_numpy(float),
                    "close": piv[("close","CALL")].to_numpy(float) + piv[("close","PUT")].to_numpy(float),
                }
            )

    obs_columns = ["obs_id","trade_date","expiry_type","entry_min","entry","gap","r15","iv_rv","lot"]
    obs_df = pd.DataFrame(
        [{k: v for k, v in o.items() if k not in {"hi","lo","close"}} for o in observations],
        columns=obs_columns,
    )
    # Keep arrays outside the DataFrame for fast precomputation.
    obs_df.attrs["paths"] = [(o["hi"], o["lo"], o["close"]) for o in observations]
    calendars = {
        k: pd.DatetimeIndex(sorted(obs_df.loc[obs_df["expiry_type"] == k, "trade_date"].unique()))
        for k in ("WEEK","MONTH")
    }
    return obs_df, calendars


def short_straddle_net(cm: OptionCostModel, entry: float, exit_mark: float, lot: int) -> float:
    gross = (entry - exit_mark) * lot
    turnover = (entry + exit_mark) * lot
    brokerage = 4.0 * cm.brokerage_per_order
    exchange = turnover * cm.exchange_rate
    sebi = turnover * cm.sebi_rate
    stt = entry * lot * cm.stt_sell_rate
    stamp = exit_mark * lot * cm.stamp_buy_rate
    gst = cm.gst_rate * (brokerage + exchange + sebi)
    slippage = 4.0 * 0.20 * lot
    return gross - (brokerage + exchange + sebi + stt + stamp + gst + slippage)


def build_trade_table(obs_df: pd.DataFrame) -> pd.DataFrame:
    paths = obs_df.attrs["paths"]
    cm = OptionCostModel()
    rows = []
    for i, o in obs_df.iterrows():
        hi, lo, close = paths[int(o.obs_id)]
        for stop in STOP_MULTS:
            for target in TARGET_DECAYS:
                for hold in HOLDS:
                    n = min(len(close), hold)
                    if n <= 0:
                        continue
                    stop_px = float(o.entry) * stop
                    target_px = float(o.entry) * (1.0 - target)
                    sh = np.flatnonzero(hi[:n] >= stop_px)
                    th = np.flatnonzero(lo[:n] <= target_px)
                    if len(sh) == 0 and len(th) == 0:
                        exit_px = float(close[n-1])
                    elif len(sh) == 0:
                        exit_px = target_px
                    elif len(th) == 0:
                        exit_px = stop_px
                    else:
                        exit_px = stop_px if sh[0] <= th[0] else target_px
                    pnl = short_straddle_net(cm, float(o.entry), float(exit_px), int(o.lot))
                    rows.append(
                        {
                            "obs_id": int(o.obs_id),
                            "trade_date": o.trade_date,
                            "expiry_type": o.expiry_type,
                            "entry_min": int(o.entry_min),
                            "stop_mult": stop,
                            "target_decay": target,
                            "hold_minutes": hold,
                            "gap": float(o.gap),
                            "r15": float(o.r15),
                            "iv_rv": float(o.iv_rv),
                            "net_pnl": float(pnl),
                        }
                    )
    columns = [
        "obs_id","trade_date","expiry_type","entry_min","stop_mult","target_decay",
        "hold_minutes","gap","r15","iv_rv","net_pnl"
    ]
    return pd.DataFrame(rows, columns=columns)


def expand_filters(trades: pd.DataFrame) -> pd.DataFrame:
    f = pd.DataFrame(FILTERS, columns=["gap_max","r15_max","iv_rv_min"])
    t = trades.copy()
    t["_key"] = 1
    f["_key"] = 1
    x = t.merge(f, on="_key").drop(columns="_key")
    mask = (
        ((x["gap_max"].isna()) | (x["gap"].notna() & (x["gap"] <= x["gap_max"])))
        & ((x["r15_max"].isna()) | (x["r15"].notna() & (x["r15"] <= x["r15_max"])))
        & x["iv_rv"].notna()
        & (x["iv_rv"] >= x["iv_rv_min"])
    )
    return x.loc[mask].copy()


def metric_table(x: pd.DataFrame, dates: pd.DatetimeIndex) -> pd.DataFrame:
    if x.empty:
        return pd.DataFrame()
    group_cols = [
        "entry_min","stop_mult","target_decay","hold_minutes",
        "gap_max","r15_max","iv_rv_min",
    ]
    daily = (
        x.groupby(group_cols + ["trade_date"], as_index=False)["net_pnl"].sum()
    )
    base = pd.DataFrame({"trade_date": dates})
    rows = []
    for keys, g in daily.groupby(group_cols):
        s = base.merge(g[["trade_date","net_pnl"]], on="trade_date", how="left").fillna({"net_pnl":0.0})
        pnl = s.net_pnl
        wins = pnl[pnl > 0].sum()
        losses = -pnl[pnl < 0].sum()
        eq = pnl.cumsum()
        dd = eq - eq.cummax()
        rows.append(
            {
                **dict(zip(group_cols, keys)),
                "mean_day_net": float(pnl.mean()),
                "median_day_net": float(pnl.median()),
                "positive_day_rate": float((pnl > 0).mean()),
                "profit_factor": float(wins / losses) if losses > 0 else 999.0,
                "total_net": float(pnl.sum()),
                "max_drawdown": float(dd.min()),
                "trade_days": int((pnl != 0).sum()),
            }
        )
    return pd.DataFrame(rows)


def main(data: Path, out: Path) -> None:
    obs, calendars = load_observations(data)
    print(f"PHASE4_OBSERVATIONS={len(obs)}")
    trades = build_trade_table(obs)
    print(f"PHASE4_CORE_TRADE_ROWS={len(trades)}")
    # This is deliberately limited to 8 regime filters; all core stop/target/hold combinations
    # are computed once and reused across walk-forward windows.
    if trades.empty:
        out.mkdir(parents=True, exist_ok=True)
        summary = {
            "observations": int(len(obs)),
            "core_trade_rows": 0,
            "gate": "NO_VALID_TRADE_PATH",
            "reason": "No ATM call+put paired path survived the entry/holding-period construction.",
        }
        (out / "phase4_walk_forward_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(json.dumps(summary, indent=2))
        return

    expanded = expand_filters(trades)
    print(f"PHASE4_EXPANDED_ROWS={len(expanded)}")

    dates_all = pd.DatetimeIndex(sorted(obs.trade_date.unique()))
    windows = expanding_windows(
        dates_all,
        train_size=300,
        validation_size=60,
        test_size=60,
        embargo_size=5,
        step_size=60,
    )

    rows = []
    for widx, w in enumerate(windows):
        for expiry in ("WEEK","MONTH"):
            cal = calendars[expiry]
            train_dates = cal[(cal >= w.train_start) & (cal <= w.train_end)]
            val_dates = cal[(cal >= w.validation_start) & (cal <= w.validation_end)]
            test_dates = cal[(cal >= w.test_start) & (cal <= w.test_end)]
            if len(test_dates) < 20:
                continue

            train_x = expanded[(expanded.expiry_type == expiry) & (expanded.trade_date.isin(train_dates))]
            val_x = expanded[(expanded.expiry_type == expiry) & (expanded.trade_date.isin(val_dates))]
            test_x = expanded[(expanded.expiry_type == expiry) & (expanded.trade_date.isin(test_dates))]

            train_metrics = metric_table(train_x, train_dates)
            val_metrics = metric_table(val_x, val_dates)
            eligible = val_metrics[(val_metrics.trade_days >= 20) & (val_metrics.mean_day_net > 0)]
            if eligible.empty:
                rows.append({"window": widx, "expiry": expiry, "selected": False})
                continue
            choice = eligible.sort_values(
                ["mean_day_net","profit_factor","positive_day_rate"],
                ascending=[False,False,False],
            ).iloc[0]

            key_cols = [
                "entry_min","stop_mult","target_decay","hold_minutes",
                "gap_max","r15_max","iv_rv_min",
            ]
            mask = np.ones(len(test_x), dtype=bool)
            for k in key_cols:
                if pd.isna(choice[k]):
                    mask &= test_x[k].isna().to_numpy()
                else:
                    mask &= (test_x[k].to_numpy() == choice[k])
            test_choice = test_x.loc[mask]
            test_metrics = metric_table(test_choice, test_dates)
            if test_metrics.empty:
                rows.append({"window": widx, "expiry": expiry, "selected": False})
                continue
            m = test_metrics.iloc[0].to_dict()
            boot = block_bootstrap_mean(
                pd.DataFrame({"net": test_choice.groupby("trade_date")["net_pnl"].sum()})
                .reindex(test_dates, fill_value=0.0)["net"].values,
                block_size=5,
                iterations=2000,
                seed=42 + widx,
            )
            train_choice = train_metrics.copy()
            train_mask = np.ones(len(train_choice), dtype=bool)
            for k in key_cols:
                if pd.isna(choice[k]):
                    train_mask &= train_choice[k].isna().to_numpy()
                else:
                    train_mask &= (train_choice[k].to_numpy() == choice[k])
            tr = train_choice.loc[train_mask]
            vr = val_metrics.loc[
                (
                    (val_metrics.entry_min == choice.entry_min)
                    & (val_metrics.stop_mult == choice.stop_mult)
                    & (val_metrics.target_decay == choice.target_decay)
                    & (val_metrics.hold_minutes == choice.hold_minutes)
                    & (
                        (val_metrics.gap_max == choice.gap_max)
                        | (val_metrics.gap_max.isna() & pd.isna(choice.gap_max))
                    )
                    & (
                        (val_metrics.r15_max == choice.r15_max)
                        | (val_metrics.r15_max.isna() & pd.isna(choice.r15_max))
                    )
                    & (
                        (val_metrics.iv_rv_min == choice.iv_rv_min)
                    )
                )
            ]
            rows.append(
                {
                    "window": widx,
                    "expiry": expiry,
                    "selected": True,
                    **{f"param_{k}": choice[k] for k in key_cols},
                    "train_mean": float(tr.iloc[0].mean_day_net) if not tr.empty else None,
                    "validation_mean": float(vr.iloc[0].mean_day_net) if not vr.empty else None,
                    "test_mean": float(m["mean_day_net"]),
                    "test_median": float(m["median_day_net"]),
                    "test_positive_day_rate": float(m["positive_day_rate"]),
                    "test_pf": float(m["profit_factor"]),
                    "test_total_net": float(m["total_net"]),
                    "test_max_drawdown": float(m["max_drawdown"]),
                    "test_trade_days": int(m["trade_days"]),
                    "bootstrap_lower_95": float(boot["lower_95"]),
                    "bootstrap_upper_95": float(boot["upper_95"]),
                }
            )

    results = pd.DataFrame(rows)
    out.mkdir(parents=True, exist_ok=True)
    results.to_csv(out / "phase4_walk_forward_results.csv", index=False)

    selected = results[results["selected"] == True] if (not results.empty and "selected" in results.columns) else pd.DataFrame()
    summary = {
        "observations": int(len(obs)),
        "core_variants": int(len(ENTRY_MINUTES)*len(STOP_MULTS)*len(TARGET_DECAYS)*len(HOLDS)),
        "regime_filter_variants": int(len(FILTERS)),
        "total_parameter_variants": int(len(ENTRY_MINUTES)*len(STOP_MULTS)*len(TARGET_DECAYS)*len(HOLDS)*len(FILTERS)),
        "walk_forward_windows": int(len(windows)),
        "selected_tests": int(len(selected)),
        "positive_test_windows": int((selected.test_mean > 0).sum()) if not selected.empty else 0,
        "target_qualified_test_windows": int((selected.test_mean >= 1000).sum()) if not selected.empty else 0,
        "mean_test_window_net": float(selected.test_mean.mean()) if not selected.empty else None,
        "median_test_window_net": float(selected.test_mean.median()) if not selected.empty else None,
        "mean_test_positive_day_rate": float(selected.test_positive_day_rate.mean()) if not selected.empty else None,
        "all_bootstrap_lower_95_positive": bool((selected.bootstrap_lower_95 > 0).all()) if not selected.empty else False,
        "gate": (
            "PASS_PRELIMINARY"
            if not selected.empty
            and (selected.test_mean > 0).all()
            and (selected.bootstrap_lower_95 > 0).all()
            and ((selected.test_mean >= 1000).mean() >= 0.8)
            else "FAIL_PRELIMINARY"
        ),
    }
    (out / "phase4_walk_forward_summary.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=Path("reports"))
    args = ap.parse_args()
    main(args.data, args.out)
