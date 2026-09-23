from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from research.contracts import nifty_lot_size
from research.cost_model import OptionCostModel


ENTRY_IST = ("09:45:00", "10:00:00", "10:15:00")
IVRV_MIN = (1.0, 1.25, 1.50)
ABS_RET_MAX = (0.0005, 0.0010, 0.0020)
ABS_OI_MAX = (0.05, 0.10, 0.20)
ABS_VOL_MAX = (0.05, 0.10, 0.20)

STAGE2_STOPS = (1.3, 1.5, 2.0)
STAGE2_TARGETS = (0.25, 0.50, 0.75)
STAGE2_HOLDS = (60, 120, 180)


def glob(root: Path) -> str:
    return (root / "**" / "*.parquet").as_posix()


def load_data(root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    source = glob(root)
    times = ",".join(repr(x) for x in ENTRY_IST)
    feature_sql = f"""
    WITH base AS (
      SELECT
        datetime,
        CAST(date AS DATE) AS trade_date,
        expiry_type,
        option_type,
        strike_type,
        CAST(spot AS DOUBLE) AS spot,
        CAST(iv AS DOUBLE) AS iv,
        CASE WHEN volume >= 0 THEN CAST(volume AS DOUBLE) ELSE NULL END AS volume,
        CAST(oi AS DOUBLE) AS oi,
        CAST(close AS DOUBLE) AS close
      FROM read_parquet('{source}', union_by_name=true)
      WHERE close > 0
    ),
    minute AS (
      SELECT
        datetime,
        trade_date,
        expiry_type,
        MAX(spot) AS spot,
        AVG(CASE WHEN strike_type='ATM' AND option_type='CALL' AND iv BETWEEN 0 AND 300 THEN iv END) AS atm_call_iv,
        AVG(CASE WHEN strike_type='ATM' AND option_type='PUT'  AND iv BETWEEN 0 AND 300 THEN iv END) AS atm_put_iv,
        SUM(CASE WHEN strike_type IN ('ATM-2','ATM-1','ATM','ATM+1','ATM+2') AND option_type='CALL' THEN volume ELSE 0 END) AS call_vol,
        SUM(CASE WHEN strike_type IN ('ATM-2','ATM-1','ATM','ATM+1','ATM+2') AND option_type='PUT'  THEN volume ELSE 0 END) AS put_vol,
        SUM(CASE WHEN strike_type IN ('ATM-2','ATM-1','ATM','ATM+1','ATM+2') AND option_type='CALL' THEN oi ELSE 0 END) AS call_oi,
        SUM(CASE WHEN strike_type IN ('ATM-2','ATM-1','ATM','ATM+1','ATM+2') AND option_type='PUT'  THEN oi ELSE 0 END) AS put_oi
      FROM base
      GROUP BY ALL
    ),
    lagged AS (
      SELECT
        *,
        (call_oi-put_oi)/NULLIF(call_oi+put_oi,0) AS oi_imb,
        (call_vol-put_vol)/NULLIF(call_vol+put_vol,0) AS vol_imb,
        (atm_call_iv+atm_put_iv)/2.0 AS atm_iv,
        spot/LAG(spot,15) OVER (PARTITION BY trade_date,expiry_type ORDER BY datetime)-1 AS spot_ret15,
        LN(spot/LAG(spot) OVER (PARTITION BY trade_date,expiry_type ORDER BY datetime)) AS log_ret
      FROM minute
    ),
    rv AS (
      SELECT *,
        STDDEV_SAMP(log_ret) OVER (
          PARTITION BY trade_date,expiry_type ORDER BY datetime
          ROWS BETWEEN 14 PRECEDING AND CURRENT ROW
        ) * SQRT(252.0*375.0) * 100.0 AS rv15_pct
      FROM lagged
    )
    SELECT
      datetime, trade_date, expiry_type, spot, atm_iv, spot_ret15, oi_imb, vol_imb,
      atm_iv / NULLIF(rv15_pct,0) AS iv_rv_ratio
    FROM rv
    WHERE STRFTIME(datetime + INTERVAL '5 hours 30 minutes','%H:%M:%S') IN ({times})
      AND spot_ret15 IS NOT NULL
      AND oi_imb IS NOT NULL
      AND vol_imb IS NOT NULL
      AND atm_iv IS NOT NULL
    ORDER BY trade_date, expiry_type, datetime
    """

    raw_sql = f"""
    SELECT
      datetime,
      CAST(date AS DATE) AS trade_date,
      expiry_type,
      option_type,
      strike_type,
      CAST(strike_price AS DOUBLE) AS strike_price,
      CAST(close AS DOUBLE) AS close
    FROM read_parquet('{source}', union_by_name=true)
    WHERE close > 0
      AND STRFTIME(datetime + INTERVAL '5 hours 30 minutes','%H:%M:%S')
          BETWEEN '09:40:00' AND '13:30:00'
    """

    con = duckdb.connect()
    features = con.execute(feature_sql).df()
    raw = con.execute(raw_sql).df()
    con.close()
    features["datetime"] = pd.to_datetime(features["datetime"])
    raw["datetime"] = pd.to_datetime(raw["datetime"])
    return features, raw


def entry_quotes(features: pd.DataFrame, raw: pd.DataFrame) -> pd.DataFrame:
    signals = []
    for ivmin in IVRV_MIN:
        for rmax in ABS_RET_MAX:
            for omax in ABS_OI_MAX:
                for vmax in ABS_VOL_MAX:
                    x = features[
                        (features.iv_rv_ratio >= ivmin)
                        & (features.spot_ret15.abs() <= rmax)
                        & (features.oi_imb.abs() <= omax)
                        & (features.vol_imb.abs() <= vmax)
                    ].copy()
                    if x.empty:
                        continue
                    x["iv_rv_min"] = ivmin
                    x["abs_ret_max"] = rmax
                    x["abs_oi_max"] = omax
                    x["abs_vol_max"] = vmax
                    x["entry_time"] = x["datetime"] + pd.Timedelta(minutes=1)
                    x = x.sort_values(["trade_date","expiry_type","datetime"]).drop_duplicates(
                        ["trade_date","expiry_type"], keep="first"
                    )
                    signals.append(x)
    if not signals:
        return pd.DataFrame()
    sig = pd.concat(signals, ignore_index=True)

    q = raw[["trade_date","expiry_type","datetime","option_type","strike_type","strike_price","close"]].drop_duplicates(
        ["trade_date","expiry_type","datetime","option_type","strike_type"], keep="last"
    )
    entry = q[q.strike_type.isin(["ATM","ATM+2","ATM-2"])].copy()

    for option_type, strike_type, sname, pname in [
        ("CALL","ATM","ce_short_strike","ce_short_entry"),
        ("PUT","ATM","pe_short_strike","pe_short_entry"),
        ("CALL","ATM+2","ce_long_strike","ce_long_entry"),
        ("PUT","ATM-2","pe_long_strike","pe_long_entry"),
    ]:
        e = entry[(entry.option_type == option_type) & (entry.strike_type == strike_type)].rename(
            columns={"datetime":"entry_time","strike_price":sname,"close":pname}
        )
        sig = sig.merge(
            e[["trade_date","expiry_type","entry_time",sname,pname]],
            on=["trade_date","expiry_type","entry_time"],
            how="left",
        )

    sig = sig.dropna(subset=[
        "ce_short_strike","pe_short_strike","ce_long_strike","pe_long_strike",
        "ce_short_entry","pe_short_entry","ce_long_entry","pe_long_entry",
    ]).copy()
    sig["credit"] = (
        sig.ce_short_entry + sig.pe_short_entry
        - sig.ce_long_entry - sig.pe_long_entry
    )
    sig = sig[sig.credit > 0].copy()
    return sig


def exact_exit(sig: pd.DataFrame, raw: pd.DataFrame, hold: int) -> pd.DataFrame:
    x = sig.copy()
    x["exit_time"] = x["entry_time"] + pd.Timedelta(minutes=hold)
    q = raw[["trade_date","expiry_type","datetime","option_type","strike_price","close"]].drop_duplicates(
        ["trade_date","expiry_type","datetime","option_type","strike_price"], keep="last"
    )
    for option_type, strike_col, out_col in [
        ("CALL","ce_short_strike","ce_short_exit"),
        ("PUT","pe_short_strike","pe_short_exit"),
        ("CALL","ce_long_strike","ce_long_exit"),
        ("PUT","pe_long_strike","pe_long_exit"),
    ]:
        e = q.rename(columns={"datetime":"exit_time","option_type":"_ot","strike_price":"_strike","close":out_col})
        e = e[e._ot == option_type]
        x = x.merge(
            e[["trade_date","expiry_type","exit_time","_strike",out_col]],
            left_on=["trade_date","expiry_type","exit_time",strike_col],
            right_on=["trade_date","expiry_type","exit_time","_strike"],
            how="left",
        ).drop(columns=["_strike"])
    return x.dropna(subset=["ce_short_exit","pe_short_exit","ce_long_exit","pe_long_exit"]).copy()


def ironfly_cost(cm: OptionCostModel, df: pd.DataFrame) -> np.ndarray:
    lot = df.trade_date.map(lambda d: nifty_lot_size(d)).to_numpy(float)
    return cm.ironfly_net_pnl(
        df.ce_short_entry, df.pe_short_entry,
        df.ce_long_entry, df.pe_long_entry,
        df.ce_short_exit, df.pe_short_exit,
        df.ce_long_exit, df.pe_long_exit,
        lot_size=int(lot[0]) if len(np.unique(lot)) == 1 else 75,
    )


def net_vector(cm: OptionCostModel, d: pd.DataFrame) -> np.ndarray:
    lot = d.trade_date.map(lambda x: nifty_lot_size(x)).to_numpy(float)
    multiplier = lot
    gross = (
        d.credit - (
            d.ce_short_exit + d.pe_short_exit
            - d.ce_long_exit - d.pe_long_exit
        )
    ).to_numpy(float) * multiplier
    turnover = (
        d.ce_short_entry + d.pe_short_entry + d.ce_long_entry + d.pe_long_entry
        + d.ce_short_exit + d.pe_short_exit + d.ce_long_exit + d.pe_long_exit
    ).to_numpy(float) * multiplier
    brokerage = 8.0 * cm.brokerage_per_order
    exchange = turnover * cm.exchange_rate
    sebi = turnover * cm.sebi_rate
    stt = (
        d.ce_short_entry + d.pe_short_entry + d.ce_long_exit + d.pe_long_exit
    ).to_numpy(float) * multiplier * cm.stt_sell_rate
    stamp = (
        d.ce_long_entry + d.pe_long_entry + d.ce_short_exit + d.pe_short_exit
    ).to_numpy(float) * multiplier * cm.stamp_buy_rate
    gst = cm.gst_rate * (brokerage + exchange + sebi)
    slippage = 8.0 * 0.20 * multiplier
    return gross - (brokerage + exchange + sebi + stt + stamp + gst + slippage)


def metrics(df: pd.DataFrame, calendar_days: int) -> dict:
    if df.empty:
        return {
            "trades": 0, "active_days": 0, "calendar_days": calendar_days,
            "mean_active_day_net": None, "mean_all_day_net": None,
            "win_rate": None, "positive_day_rate": None,
            "profit_factor": None, "total_net": None, "max_drawdown": None,
        }
    daily = df.groupby("trade_date")["net_pnl"].sum()
    wins = df.loc[df.net_pnl > 0, "net_pnl"].sum()
    losses = -df.loc[df.net_pnl < 0, "net_pnl"].sum()
    return {
        "trades": int(len(df)),
        "active_days": int(len(daily)),
        "calendar_days": int(calendar_days),
        "mean_active_day_net": float(daily.mean()),
        "mean_all_day_net": float(df.net_pnl.sum() / max(1, calendar_days)),
        "median_trade": float(df.net_pnl.median()),
        "win_rate": float((df.net_pnl > 0).mean()),
        "positive_day_rate": float((daily > 0).sum() / max(1, calendar_days)),
        "profit_factor": float(wins / losses) if losses > 0 else 999.0,
        "total_net": float(df.net_pnl.sum()),
        "max_drawdown": float((daily.cumsum()-daily.cumsum().cummax()).min()),
        "mean_credit": float(df.credit.mean()),
    }


def stage1(features: pd.DataFrame, raw: pd.DataFrame, out: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    sig = entry_quotes(features, raw)
    rows = []
    all_trades = []
    cm = OptionCostModel()
    for hold in [120]:
        if sig.empty:
            continue
        d = exact_exit(sig, raw, hold)
        if d.empty:
            continue
        d["hold_minutes"] = hold
        d["net_pnl"] = net_vector(cm, d)
        group = ["expiry_type","iv_rv_min","abs_ret_max","abs_oi_max","abs_vol_max"]
        for keys, g in d.groupby(group):
            vals = metrics(g, int(features[features.expiry_type.eq(keys[0])].trade_date.nunique()))
            rows.append({**dict(zip(group, keys)), **vals})
        all_trades.append(d)
    board = pd.DataFrame(rows)
    trades = pd.concat(all_trades, ignore_index=True) if all_trades else pd.DataFrame()
    if not board.empty:
        board = board.sort_values(
            ["mean_all_day_net","positive_day_rate","profit_factor"],
            ascending=[False,False,False],
        ).reset_index(drop=True)
    out.mkdir(parents=True, exist_ok=True)
    board.to_csv(out/"phase3f_ironfly_stage1.csv", index=False)
    trades.to_csv(out/"phase3f_ironfly_stage1_trades.csv", index=False)
    return sig, board, {"signals": int(len(sig)), "variants": int(len(board))}


def path_mark(raw_index: pd.Series, row: pd.Series, exit_time: pd.Timestamp) -> float | None:
    ts = pd.date_range(row.entry_time + pd.Timedelta(minutes=1), exit_time, freq="min")
    keys = []
    for t in ts:
        keys.extend([
            (row.trade_date, row.expiry_type, t, "CALL", row.ce_short_strike),
            (row.trade_date, row.expiry_type, t, "PUT", row.pe_short_strike),
            (row.trade_date, row.expiry_type, t, "CALL", row.ce_long_strike),
            (row.trade_date, row.expiry_type, t, "PUT", row.pe_long_strike),
        ])
    vals = raw_index.reindex(keys).to_numpy()
    if len(vals) < 4 or np.any(pd.isna(vals)):
        return None
    marks = (
        vals[0::4] + vals[1::4] - vals[2::4] - vals[3::4]
    )
    return marks


def stage2(sig: pd.DataFrame, board: pd.DataFrame, raw: pd.DataFrame, out: Path) -> tuple[pd.DataFrame, dict]:
    top = board.head(10).copy()
    if top.empty or sig.empty:
        return pd.DataFrame(), {"variants": 0}

    sig_key = ["expiry_type","iv_rv_min","abs_ret_max","abs_oi_max","abs_vol_max"]
    candidate_rows = []
    for _, p in top.iterrows():
        q = sig[
            (sig.expiry_type == p.expiry_type)
            & (sig.iv_rv_min == p.iv_rv_min)
            & (sig.abs_ret_max == p.abs_ret_max)
            & (sig.abs_oi_max == p.abs_oi_max)
            & (sig.abs_vol_max == p.abs_vol_max)
        ].copy()
        if not q.empty:
            candidate_rows.append(q)

    if not candidate_rows:
        return pd.DataFrame(), {"variants": 0}

    candidates = pd.concat(candidate_rows, ignore_index=True)
    cm = OptionCostModel()
    idx = raw.set_index(["trade_date","expiry_type","datetime","option_type","strike_price"])["close"]

    results = []
    for stop_mult in STAGE2_STOPS:
        for target_decay in STAGE2_TARGETS:
            for hold in STAGE2_HOLDS:
                recs = []
                for row in candidates.itertuples(index=False):
                    entry_credit = float(row.credit)
                    exit_deadline = row.entry_time + pd.Timedelta(minutes=hold)
                    mark_arr = path_mark(idx, row, exit_deadline)
                    if mark_arr is None or len(mark_arr) == 0:
                        continue
                    target = entry_credit * (1.0 - target_decay)
                    stop = entry_credit * stop_mult
                    stop_idx = np.flatnonzero(mark_arr >= stop)
                    target_idx = np.flatnonzero(mark_arr <= target)
                    sidx = int(stop_idx[0]) if len(stop_idx) else None
                    tidx = int(target_idx[0]) if len(target_idx) else None
                    if sidx is None and tidx is None:
                        ix = len(mark_arr)-1
                        exit_mark = float(mark_arr[ix])
                    elif sidx is None:
                        ix = tidx
                        exit_mark = target
                    elif tidx is None:
                        ix = sidx
                        exit_mark = stop
                    elif sidx <= tidx:
                        ix = sidx
                        exit_mark = stop
                    else:
                        ix = tidx
                        exit_mark = target
                    ce_short_exit = float(pd.Series([row.ce_short_strike]))
                    # To keep path P&L deterministic, convert the selected iron-fly mark
                    # into net spread P&L and apply the exact eight-leg cost using the
                    # original entry and the observed exit mark.
                    lot = nifty_lot_size(row.trade_date)
                    gross = (entry_credit - exit_mark) * lot
                    turnover = (
                        row.ce_short_entry + row.pe_short_entry
                        + row.ce_long_entry + row.pe_long_entry
                    ) * lot
                    # Approximate exit turnover from the mark while retaining conservative
                    # four-leg slippage and statutory costs. Full leg exit reconciliation
                    # is reserved for a promoted candidate.
                    exit_turnover = max(0.0, abs(exit_mark)) * lot
                    brokerage = 8.0 * cm.brokerage_per_order
                    exchange = (turnover + exit_turnover) * cm.exchange_rate
                    sebi = (turnover + exit_turnover) * cm.sebi_rate
                    stt = (
                        row.ce_short_entry + row.pe_short_entry
                    ) * lot * cm.stt_sell_rate
                    stamp = (
                        row.ce_long_entry + row.pe_long_entry
                    ) * lot * cm.stamp_buy_rate
                    gst = cm.gst_rate * (brokerage + exchange + sebi)
                    slippage = 8.0 * 0.20 * lot
                    net = gross - (brokerage + exchange + sebi + stt + stamp + gst + slippage)
                    recs.append({
                        "trade_date": row.trade_date,
                        "expiry_type": row.expiry_type,
                        "iv_rv_min": row.iv_rv_min,
                        "abs_ret_max": row.abs_ret_max,
                        "abs_oi_max": row.abs_oi_max,
                        "abs_vol_max": row.abs_vol_max,
                        "entry_time": row.entry_time,
                        "credit": entry_credit,
                        "stop_mult": stop_mult,
                        "target_decay": target_decay,
                        "hold_minutes": hold,
                        "net_pnl": net,
                    })
                if not recs:
                    continue
                d = pd.DataFrame(recs)
                m = metrics(d, int(features[features.expiry_type.eq(d.expiry_type.iloc[0])].trade_date.nunique()))
                results.append({
                    "expiry_type": d.expiry_type.iloc[0],
                    "iv_rv_min": d.iv_rv_min.iloc[0],
                    "abs_ret_max": d.abs_ret_max.iloc[0],
                    "abs_oi_max": d.abs_oi_max.iloc[0],
                    "abs_vol_max": d.abs_vol_max.iloc[0],
                    "stop_mult": stop_mult,
                    "target_decay": target_decay,
                    "hold_minutes": hold,
                    **m,
                })

    board2 = pd.DataFrame(results)
    if not board2.empty:
        board2 = board2.sort_values(
            ["mean_all_day_net","positive_day_rate","profit_factor"],
            ascending=[False,False,False],
        ).reset_index(drop=True)
    board2.to_csv(out/"phase3f_ironfly_stage2.csv", index=False)
    return board2, {"variants": int(len(board2))}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=Path("reports"))
    args = ap.parse_args()

    features, raw = load_data(args.data)
    sig, board1, extra = stage1(features, raw, args.out)
    board2, extra2 = stage2(sig, board1, raw, args.out)

    best1 = board1.iloc[0].to_dict() if not board1.empty else None
    best2 = board2.iloc[0].to_dict() if not board2.empty else None
    promoted1 = int((board1.mean_all_day_net >= 1000).sum()) if not board1.empty else 0
    promoted2 = int((board2.mean_all_day_net >= 1000).sum()) if not board2.empty else 0

    summary = {
        "feature_rows": int(len(features)),
        "raw_rows": int(len(raw)),
        "stage1_signals": int(extra["signals"]),
        "stage1_variants": int(extra["variants"]),
        "stage1_target_qualified": promoted1,
        "stage1_best": best1,
        "stage2_variants": int(extra2["variants"]),
        "stage2_target_qualified": promoted2,
        "stage2_best": best2,
        "gate": (
            "PASS_PRELIMINARY" if max(
                [x for x in [best1["mean_all_day_net"] if best1 else -1e18,
                              best2["mean_all_day_net"] if best2 else -1e18] if x is not None]
            ) >= 1000 else "FAIL_PRELIMINARY"
        ),
        "cost_note": "Stage 2 uses exact entry quotes plus conservative four-leg slippage; exit statutory turnover is approximated from the observed iron-fly mark. A promoted candidate must be rerun with exact four-leg exit quotes.",
    }
    (args.out / "phase3f_ironfly_summary.json").write_text(
        json.dumps(summary, indent=2, default=str),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
