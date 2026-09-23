from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from research.contracts import nifty_lot_size
from research.cost_model import OptionCostModel
from research.walk_forward import expanding_windows, block_bootstrap_mean


ENTRY_MINUTES = (30, 45, 60)  # after 09:15 => 09:45, 10:00, 10:15
STOP_MULTS = (1.6, 1.8, 2.0)
TARGET_DECAYS = (0.35, 0.45, 0.55)
HOLDS = (120, 180)
GAP_MAXS = (0.005, None)
R15_MAXS = (0.005, None)
IVRV_MINS = (0.0, 0.5)


@dataclass(frozen=True)
class Observation:
    trade_date: pd.Timestamp
    expiry_type: str
    entry_clock: int
    entry: float
    gap: float
    r15: float
    iv_rv: float
    lot_size: int
    hi: np.ndarray
    lo: np.ndarray
    close: np.ndarray


def source_glob(root: Path) -> str:
    return (root / "**" / "*.parquet").as_posix()


def load_observations(root: Path) -> tuple[list[Observation], dict[str, pd.DatetimeIndex]]:
    source = source_glob(root)
    sql = f"""
    WITH base AS (
      SELECT
        datetime,
        CAST(date AS DATE) AS trade_date,
        expiry_type,
        option_type,
        strike_type,
        CAST(strike_price AS DOUBLE) AS strike_price,
        CAST(spot AS DOUBLE) AS spot,
        CAST(iv AS DOUBLE) AS iv,
        CAST(open AS DOUBLE) AS open,
        CAST(high AS DOUBLE) AS high,
        CAST(low AS DOUBLE) AS low,
        CAST(close AS DOUBLE) AS close
      FROM read_parquet('{source}', union_by_name=true)
      WHERE close > 0
    )
    SELECT * FROM base
    WHERE STRFTIME(datetime + INTERVAL '5 hours 30 minutes','%H:%M:%S')
          BETWEEN '09:15:00' AND '13:45:00'
    ORDER BY trade_date, expiry_type, datetime
    """
    con = duckdb.connect()
    raw = con.execute(sql).df()
    con.close()
    raw["datetime"] = pd.to_datetime(raw["datetime"])

    spots = (
        raw[["datetime", "trade_date", "spot"]]
        .drop_duplicates(["trade_date","datetime"], keep="last")
        .sort_values("datetime")
    )
    option = raw[raw.strike_type == "ATM"].copy()
    option = option.sort_values("datetime")

    observations: list[Observation] = []
    calendar: dict[str, set[pd.Timestamp]] = {"WEEK": set(), "MONTH": set()}

    prev_close_by_day: dict[pd.Timestamp, float] = {}
    daily_spot = {d: g.sort_values("datetime") for d, g in spots.groupby("trade_date")}
    ordered_days = sorted(daily_spot)
    for i, d in enumerate(ordered_days):
        prev_close_by_day[d] = float(daily_spot[ordered_days[i-1]].spot.iloc[-1]) if i else np.nan

    for d, day in daily_spot.items():
        prev_close = prev_close_by_day[d]
        open_spot = float(day.spot.iloc[0])
        gap = abs((open_spot - prev_close) / prev_close) if np.isfinite(prev_close) and prev_close else np.nan
        first15 = day[(day.datetime.dt.time >= pd.Timestamp("09:15").time()) &
                      (day.datetime.dt.time < pd.Timestamp("09:30").time())]
        r15 = (float(first15.spot.max()) - float(first15.spot.min())) / open_spot if not first15.empty else np.nan

        for expiry in ("WEEK", "MONTH"):
            od = option[(option.trade_date == d) & (option.expiry_type == expiry)].copy()
            if od.empty:
                continue
            calendar[expiry].add(pd.Timestamp(d))
            for entry_min in ENTRY_MINUTES:
                entry_clock = pd.Timestamp(d) + pd.Timedelta(minutes=entry_min + 15)
                q = od[(od.datetime >= entry_clock) & (od.datetime <= entry_clock + pd.Timedelta(minutes=2))]
                if q.empty:
                    continue
                ce = q[q.option_type == "CALL"].sort_values("datetime")
                pe = q[q.option_type == "PUT"].sort_values("datetime")
                if ce.empty or pe.empty:
                    continue
                et = max(ce.datetime.iloc[0], pe.datetime.iloc[0])
                ce0 = float(ce[ce.datetime == et].close.iloc[0]) if not ce[ce.datetime == et].empty else np.nan
                pe0 = float(pe[pe.datetime == et].close.iloc[0]) if not pe[pe.datetime == et].empty else np.nan
                entry = ce0 + pe0
                if not np.isfinite(entry) or entry <= 0:
                    continue

                hist = day[(day.datetime < et) & (day.datetime >= et - pd.Timedelta(minutes=30))].spot
                if len(hist) >= 15:
                    rv = float(hist.pct_change().dropna().std() * np.sqrt(252 * 375) * 100)
                else:
                    rv = np.nan
                ivs = q[q.datetime == et].iv
                iv = float(ivs[(q[q.datetime == et].option_type.isin(["CALL","PUT"]))].mean()) if not ivs.empty else np.nan
                iv_rv = iv / rv if np.isfinite(iv) and np.isfinite(rv) and rv > 0 else np.nan

                path = od[(od.datetime > et) & (od.datetime <= et + pd.Timedelta(minutes=max(HOLDS)))
                          & (od.strike_type == "ATM")]
                piv = path.pivot_table(index="datetime", columns="option_type",
                                        values=["high","low","close"], aggfunc="last")
                if piv.empty or not {"CALL","PUT"}.issubset(set(piv["close"].columns)):
                    continue
                piv = piv.dropna(subset=[("close","CALL"),("close","PUT")])
                if piv.empty:
                    continue

                observations.append(
                    Observation(
                        trade_date=pd.Timestamp(d),
                        expiry_type=expiry,
                        entry_clock=entry_min,
                        entry=float(entry),
                        gap=float(gap),
                        r15=float(r15),
                        iv_rv=float(iv_rv),
                        lot_size=nifty_lot_size(d),
                        hi=(piv[("high","CALL")].to_numpy(float) + piv[("high","PUT")].to_numpy(float)),
                        lo=(piv[("low","CALL")].to_numpy(float) + piv[("low","PUT")].to_numpy(float)),
                        close=(piv[("close","CALL")].to_numpy(float) + piv[("close","PUT")].to_numpy(float)),
                    )
                )
    calendars = {k: pd.DatetimeIndex(sorted(v)) for k, v in calendar.items()}
    return observations, calendars


def net_short_straddle(cm: OptionCostModel, entry: float, exit_mark: float, lot: int) -> float:
    # Exact cost model assumes both legs are filled at their closes; for stop/target
    # exits, the straddle mark is the defined exit value and costs remain conservative.
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


def precompute(observations: list[Observation]) -> dict[tuple[int,int,float,float,int], float]:
    cm = OptionCostModel()
    out = {}
    for idx, o in enumerate(observations):
        for stop in STOP_MULTS:
            for target in TARGET_DECAYS:
                for hold in HOLDS:
                    n = min(len(o.close), hold)
                    if n <= 0:
                        continue
                    stop_px = o.entry * stop
                    target_px = o.entry * (1.0 - target)
                    sh = np.flatnonzero(o.hi[:n] >= stop_px)
                    th = np.flatnonzero(o.lo[:n] <= target_px)
                    if len(sh) == 0 and len(th) == 0:
                        exit_px = float(o.close[n-1])
                    elif len(sh) == 0:
                        exit_px = float(target_px)
                    elif len(th) == 0:
                        exit_px = float(stop_px)
                    else:
                        exit_px = float(stop_px if sh[0] <= th[0] else target_px)
                    out[(idx, o.entry_clock, stop, target, hold)] = net_short_straddle(
                        cm, o.entry, exit_px, o.lot_size
                    )
    return out


def grid() -> list[dict]:
    rows = []
    for entry in ENTRY_MINUTES:
        for stop in STOP_MULTS:
            for target in TARGET_DECAYS:
                for hold in HOLDS:
                    for gap in GAP_MAXS:
                        for r15 in R15_MAXS:
                            for ivmin in IVRV_MINS:
                                rows.append(
                                    {
                                        "entry_clock": entry,
                                        "stop_mult": stop,
                                        "target_decay": target,
                                        "hold_minutes": hold,
                                        "gap_max": gap,
                                        "r15_max": r15,
                                        "iv_rv_min": ivmin,
                                    }
                                )
    return rows


def daily_series(obs: list[Observation], outcomes: dict, expiry: str, params: dict, dates: pd.DatetimeIndex) -> pd.Series:
    vals = pd.Series(0.0, index=dates)
    for idx, o in enumerate(obs):
        if o.expiry_type != expiry or o.entry_clock != params["entry_clock"]:
            continue
        if o.trade_date not in dates:
            continue
        if params["gap_max"] is not None and (not np.isfinite(o.gap) or o.gap > params["gap_max"]):
            continue
        if params["r15_max"] is not None and (not np.isfinite(o.r15) or o.r15 > params["r15_max"]):
            continue
        if not np.isfinite(o.iv_rv) or o.iv_rv < params["iv_rv_min"]:
            continue
        key = (idx, o.entry_clock, params["stop_mult"], params["target_decay"], params["hold_minutes"])
        if key in outcomes:
            vals.loc[o.trade_date] += outcomes[key]
    return vals


def score(series: pd.Series) -> dict:
    pnl = series.to_numpy(float)
    wins = pnl[pnl > 0].sum()
    losses = -pnl[pnl < 0].sum()
    dd = np.cumsum(pnl) - np.maximum.accumulate(np.cumsum(pnl))
    return {
        "mean_day_net": float(series.mean()),
        "median_day_net": float(series.median()),
        "positive_day_rate": float((series > 0).mean()),
        "profit_factor": float(wins / losses) if losses > 0 else 999.0,
        "total_net": float(series.sum()),
        "max_drawdown": float(dd.min()) if len(dd) else 0.0,
        "trade_days": int((series != 0).sum()),
    }


def choose(train: pd.DataFrame, validation: pd.DataFrame) -> pd.Series | None:
    # Require at least 20 validation trade-days and positive validation expectancy.
    eligible = validation[validation.trade_days >= 20].copy()
    if eligible.empty:
        return None
    eligible = eligible[eligible.mean_day_net > 0].copy()
    if eligible.empty:
        return None
    return eligible.sort_values(
        ["mean_day_net","profit_factor","positive_day_rate"],
        ascending=[False,False,False],
    ).iloc[0]


def main(data: Path, out: Path) -> None:
    observations, calendars = load_observations(data)
    outcomes = precompute(observations)
    params = grid()

    all_dates = pd.DatetimeIndex(sorted({o.trade_date for o in observations}))
    windows = expanding_windows(all_dates, train_size=300, validation_size=60, test_size=60, embargo_size=5, step_size=60)

    records = []
    selected = []
    for widx, window in enumerate(windows):
        for expiry in ("WEEK", "MONTH"):
            cal = calendars[expiry]
            train_dates = cal[(cal >= window.train_start) & (cal <= window.train_end)]
            val_dates = cal[(cal >= window.validation_start) & (cal <= window.validation_end)]
            test_dates = cal[(cal >= window.test_start) & (cal <= window.test_end)]
            if len(test_dates) < 20:
                continue

            rows_train, rows_val = [], []
            for p in params:
                st = daily_series(observations, outcomes, expiry, p, train_dates)
                sv = daily_series(observations, outcomes, expiry, p, val_dates)
                mt = score(st)
                mv = score(sv)
                rows_train.append({**p, **mt})
                rows_val.append({**p, **mv})
            train_df = pd.DataFrame(rows_train)
            val_df = pd.DataFrame(rows_val)
            choice = choose(train_df, val_df)

            if choice is None:
                selected.append({"window": widx, "expiry": expiry, "selected": False})
                continue
            selected.append(
                {
                    "window": widx,
                    "expiry": expiry,
                    "selected": True,
                    "train": score(
                        daily_series(observations, outcomes, expiry, choice.to_dict(), train_dates)
                    ),
                    "validation": score(
                        daily_series(observations, outcomes, expiry, choice.to_dict(), val_dates)
                    ),
                    "test": score(
                        daily_series(observations, outcomes, expiry, choice.to_dict(), test_dates)
                    ),
                    "params": {k: choice[k] for k in params[0].keys()},
                    "test_bootstrap": block_bootstrap_mean(
                        daily_series(observations, outcomes, expiry, choice.to_dict(), test_dates).values,
                        block_size=5,
                        iterations=2000,
                        seed=42 + widx,
                    ),
                }
            )

    selected_df = pd.DataFrame(
        [
            {
                "window": r["window"],
                "expiry": r["expiry"],
                "selected": r["selected"],
                "params": json.dumps(r.get("params", {}), default=str),
                "train_mean": r.get("train", {}).get("mean_day_net"),
                "validation_mean": r.get("validation", {}).get("mean_day_net"),
                "test_mean": r.get("test", {}).get("mean_day_net"),
                "test_pf": r.get("test", {}).get("profit_factor"),
                "test_positive_day_rate": r.get("test", {}).get("positive_day_rate"),
                "test_total_net": r.get("test", {}).get("total_net"),
                "test_max_drawdown": r.get("test", {}).get("max_drawdown"),
                "test_trade_days": r.get("test", {}).get("trade_days"),
                "bootstrap_lower_95": r.get("test_bootstrap", {}).get("lower_95"),
                "bootstrap_upper_95": r.get("test_bootstrap", {}).get("upper_95"),
            }
            for r in selected
        ]
    )

    out.mkdir(parents=True, exist_ok=True)
    selected_df.to_csv(out / "phase4_walk_forward_results.csv", index=False)

    test_rows = selected_df[selected_df.selected]
    summary = {
        "observations": len(observations),
        "variants_per_expiry": len(params),
        "windows": len(windows),
        "selected_windows": int(test_rows.shape[0]),
        "positive_test_windows": int((test_rows.test_mean > 0).sum()) if not test_rows.empty else 0,
        "target_qualified_test_windows": int((test_rows.test_mean >= 1000).sum()) if not test_rows.empty else 0,
        "mean_test_mean": float(test_rows.test_mean.mean()) if not test_rows.empty else None,
        "median_test_mean": float(test_rows.test_mean.median()) if not test_rows.empty else None,
        "overall_test_net": float(test_rows.test_total_net.sum()) if not test_rows.empty else None,
        "gate": (
            "PASS_PRELIMINARY"
            if not test_rows.empty
            and (test_rows.test_mean > 0).all()
            and (test_rows.bootstrap_lower_95 > 0).all()
            and (test_rows.test_mean >= 1000).mean() >= 0.8
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
