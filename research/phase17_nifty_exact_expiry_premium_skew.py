from __future__ import annotations
import argparse, json
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from research.cost_model import OptionCostModel

ENTRY_TIMES = ("14:30:00", "14:45:00", "15:00:00")
SKEW_THRESHOLDS = (0.10, 0.15)
JUMP_MAX = (0.0030, 0.0050)
RV_MIN = (1.00, 1.25)
WIDTHS = (1, 2)
HOLDS = (15, 30)
STOPS = (1.25, 1.50)
TARGET_RATIO = 0.50
START_DATE = "2021-05-27"
END_DATE = "2026-08-04"
SIDE_CODE = {"PUT": "PE", "CALL": "CE"}


def expiry_files(root: Path):
    opts = root / "options" / "NIFTY"
    files = []
    for p in sorted(opts.glob("*.parquet")):
        try:
            d = pd.Timestamp(p.stem).date()
        except Exception:
            continue
        files.append((d, p))
    if not files:
        raise FileNotFoundError(f"No exact-expiry NIFTY files in {opts}")
    return files


def expiry_for_day(files, trade_date):
    td = pd.Timestamp(trade_date).date()
    fut = [(d, p) for d, p in files if d >= td]
    if not fut:
        return None
    return min(fut, key=lambda x: x[0])


def variant_grid():
    return [
        dict(entry_time=e, skew=s, jump=j, rv=r, width=w, hold=h, stop=st, side=side)
        for e in ENTRY_TIMES
        for s in SKEW_THRESHOLDS
        for j in JUMP_MAX
        for r in RV_MIN
        for w in WIDTHS
        for h in HOLDS
        for st in STOPS
        for side in ("PUT", "CALL")
    ]


def variant_id(v):
    return (
        f'{v["entry_time"]}|sk{v["skew"]}|j{v["jump"]}|rv{v["rv"]}|'
        f'w{v["width"]}|h{v["hold"]}|stop{v["stop"]}|{v["side"]}'
    )


def load_spot(root: Path):
    p = root / "index" / "NIFTY.parquet"
    con = duckdb.connect()
    con.execute("SET TimeZone='Asia/Kolkata'")
    q = f"""
    WITH b AS (
      SELECT CAST(timestamp AS TIMESTAMP) AS ts,
             CAST(trading_day AS DATE) AS trade_date,
             CAST(close AS DOUBLE) AS close
      FROM read_parquet('{p}')
      WHERE CAST(trading_day AS DATE) BETWEEN DATE '{START_DATE}' AND DATE '{END_DATE}'
        AND close > 0
    ),
    r AS (
      SELECT *,
             close / LAG(close, 1) OVER(PARTITION BY trade_date ORDER BY ts) - 1 AS ret1,
             close / LAG(close, 10) OVER(PARTITION BY trade_date ORDER BY ts) - 1 AS ret10
      FROM b
    ),
    v AS (
      SELECT *,
             STDDEV_SAMP(ret1) OVER(
               PARTITION BY trade_date ORDER BY ts
               ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
             ) AS rv20
      FROM r
    ),
    z AS (
      SELECT *,
             rv20 / NULLIF(
               AVG(rv20) OVER(
                 PARTITION BY trade_date ORDER BY ts
                 ROWS BETWEEN 119 PRECEDING AND CURRENT ROW
               ), 0
             ) AS rv_ratio
      FROM v
    )
    SELECT trade_date, ts, close, ret10, rv20, rv_ratio
    FROM z
    WHERE ret10 IS NOT NULL
      AND rv20 IS NOT NULL
      AND rv_ratio IS NOT NULL
      AND CAST(ts AS TIME) IN (
        TIME '14:30:00', TIME '14:45:00', TIME '15:00:00'
      )
    ORDER BY trade_date, ts
    """
    x = con.execute(q).df()
    con.close()
    if x.empty:
        return x
    x["trade_date"] = pd.to_datetime(x["trade_date"]).dt.date
    x["ts"] = pd.to_datetime(x["ts"]).dt.floor("min")
    return x


def load_option_quotes(root, spot_candidates):
    files = expiry_files(root)
    chosen = {}
    for d in sorted(spot_candidates.trade_date.unique()):
        ef = expiry_for_day(files, d)
        if ef:
            chosen[d] = ef
    if not chosen:
        return pd.DataFrame()

    wanted = spot_candidates[["trade_date", "ts"]].drop_duplicates().copy()
    wanted["entry_ts"] = wanted["ts"] + pd.Timedelta(minutes=1)

    con = duckdb.connect()
    con.execute("SET TimeZone='Asia/Kolkata'")
    con.register("wanted", wanted)
    chunks = []

    for expiry_date, path in sorted(set(chosen.values()), key=lambda x: x[0]):
        dates = [d for d, (ed, _) in chosen.items() if ed == expiry_date]
        vals = ",".join(f"DATE '{d}'" for d in dates)
        q = f"""
        SELECT CAST(o.timestamp AS TIMESTAMP) AS ts,
               CAST(o.trading_day AS DATE) AS trade_date,
               CAST(o.strike AS DOUBLE) AS strike,
               CAST(o.option_type AS VARCHAR) AS option_type,
               CAST(o.open AS DOUBLE) AS open_px,
               CAST(o.close AS DOUBLE) AS close_px,
               CAST(o.volume AS DOUBLE) AS volume,
               CAST(o.open_interest AS DOUBLE) AS oi
        FROM read_parquet('{path}') o
        JOIN wanted w
          ON CAST(o.trading_day AS DATE) = w.trade_date
         AND CAST(o.timestamp AS TIMESTAMP) IN (w.ts, w.entry_ts)
        WHERE CAST(o.trading_day AS DATE) IN ({vals})
          AND o.close > 0
        """
        z = con.execute(q).df()
        if not z.empty:
            z["expiry"] = expiry_date
            chunks.append(z)

    con.close()
    if not chunks:
        return pd.DataFrame()

    q = pd.concat(chunks, ignore_index=True)
    q["ts"] = pd.to_datetime(q["ts"]).dt.floor("min")
    q["trade_date"] = pd.to_datetime(q["trade_date"]).dt.date
    q["option_type"] = q["option_type"].astype(str)
    return q


def first_quote(q, strike, option_code):
    z = q[(q["strike"] == float(strike)) & (q["option_type"] == option_code)]
    return z.sort_values(["ts", "strike"]).head(1)


def build_setups(signal_df, quotes):
    if quotes.empty:
        return pd.DataFrame()

    signal_keys = signal_df[["trade_date", "ts", "close", "ret10", "rv_ratio"]].drop_duplicates()
    setups = []

    for (d, ts), g in quotes.groupby(["trade_date", "ts"], sort=False):
        meta = signal_keys[(signal_keys.trade_date == d) & (signal_keys.ts == ts)]
        if meta.empty:
            continue

        signal_quotes = g[g.ts == ts].copy()
        entry_ts = ts + pd.Timedelta(minutes=1)
        entry_quotes = g[g.ts == entry_ts].copy()
        if signal_quotes.empty or entry_quotes.empty:
            continue

        spot = float(meta.iloc[0].close)
        strikes = np.sort(signal_quotes["strike"].dropna().unique())
        if len(strikes) < 7:
            continue

        atm_i = int(np.argmin(np.abs(strikes - spot)))
        atm_plus2 = float(strikes[min(atm_i + 2, len(strikes) - 1)])
        atm_minus2 = float(strikes[max(atm_i - 2, 0)])

        call_sig = first_quote(signal_quotes, atm_plus2, SIDE_CODE["CALL"])
        put_sig = first_quote(signal_quotes, atm_minus2, SIDE_CODE["PUT"])
        if call_sig.empty or put_sig.empty:
            continue

        call_row = call_sig.iloc[0]
        put_row = put_sig.iloc[0]

        call_premium = float(call_row.close_px)
        put_premium = float(put_row.close_px)
        denom = max(1e-9, abs(put_premium) + abs(call_premium))
        skew = (put_premium - call_premium) / denom

        vol_denom = max(1e-9, float(put_row.volume) + float(call_row.volume))
        oi_denom = max(1e-9, float(put_row.oi) + float(call_row.oi))
        vol_imb = (float(put_row.volume) - float(call_row.volume)) / vol_denom
        oi_imb = (float(put_row.oi) - float(call_row.oi)) / oi_denom

        for side in ("PUT", "CALL"):
            short_i = atm_i - 2 if side == "PUT" else atm_i + 2
            if short_i < 0 or short_i >= len(strikes):
                continue

            short_strike = float(strikes[short_i])
            for width in WIDTHS:
                wing_i = short_i - width if side == "PUT" else short_i + width
                if wing_i < 0 or wing_i >= len(strikes):
                    continue

                wing_strike = float(strikes[wing_i])
                code = SIDE_CODE[side]
                short_entry_q = first_quote(entry_quotes, short_strike, code)
                wing_entry_q = first_quote(entry_quotes, wing_strike, code)
                if short_entry_q.empty or wing_entry_q.empty:
                    continue

                short_entry = float(short_entry_q.iloc[0].open_px)
                wing_entry = float(wing_entry_q.iloc[0].open_px)
                credit = short_entry - wing_entry
                if not np.isfinite(credit) or credit <= 0:
                    continue

                setups.append({
                    "trade_date": d,
                    "ts": ts,
                    "entry_ts": entry_ts,
                    "expiry": call_row["expiry"],
                    "side": side,
                    "option_code": code,
                    "width": width,
                    "short_strike": short_strike,
                    "wing_strike": wing_strike,
                    "short_entry": short_entry,
                    "wing_entry": wing_entry,
                    "entry_credit": credit,
                    "skew": skew,
                    "vol_imb": vol_imb,
                    "oi_imb": oi_imb,
                    "spot_ret10": float(meta.iloc[0].ret10),
                    "rv_ratio": float(meta.iloc[0].rv_ratio),
                })
    return pd.DataFrame(setups)


def filter_setups(setups, variants):
    if setups.empty:
        return pd.DataFrame()

    out = []
    for v in variants:
        m = (
            setups.side.eq(v["side"])
            & setups.width.eq(v["width"])
            & (setups.skew.ge(v["skew"]) if v["side"] == "PUT" else setups.skew.le(-v["skew"]))
            & (setups.vol_imb.ge(0) if v["side"] == "PUT" else setups.vol_imb.le(0))
            & (setups.oi_imb.ge(0) if v["side"] == "PUT" else setups.oi_imb.le(0))
            & (setups.spot_ret10.ge(0) if v["side"] == "PUT" else setups.spot_ret10.le(0))
            & setups.rv_ratio.ge(v["rv"])
            & setups.spot_ret10.abs().le(v["jump"])
            & setups.ts.dt.strftime("%H:%M:%S").eq(v["entry_time"])
        )
        s = setups.loc[m].copy()
        if not s.empty:
            s["variant_id"] = variant_id(v)
            out.append(s)
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def lot(d):
    d = pd.Timestamp(d).date()
    if d < pd.Timestamp("2024-04-26").date():
        return 50
    if d < pd.Timestamp("2024-11-21").date():
        return 25
    if d < pd.Timestamp("2026-01-06").date():
        return 75
    return 65


def simulate(root, setups, out, slippage):
    if setups.empty:
        return pd.DataFrame()

    files = {d: path for d, path in expiry_files(root)}
    max_hold = max(HOLDS)
    legs_df = setups[[
        "trade_date", "entry_ts", "expiry", "option_code",
        "side", "short_strike", "wing_strike"
    ]].drop_duplicates().copy()

    con = duckdb.connect()
    con.execute("SET TimeZone='Asia/Kolkata'")
    con.register("legs", legs_df)
    chunks = []

    for expiry_date, path in sorted(files.items()):
        active = con.execute(
            "SELECT COUNT(*) FROM legs WHERE expiry=?",
            [expiry_date]
        ).fetchone()[0]
        if not active:
            continue

        q = f"""
        SELECT CAST(o.timestamp AS TIMESTAMP) ts,
               CAST(o.trading_day AS DATE) trade_date,
               CAST(o.strike AS DOUBLE) strike,
               CAST(o.option_type AS VARCHAR) option_type,
               CAST(o.high AS DOUBLE) high,
               CAST(o.low AS DOUBLE) low,
               CAST(o.close AS DOUBLE) close_px
        FROM read_parquet('{path}') o
        JOIN legs l
          ON l.expiry = DATE '{expiry_date}'
         AND CAST(o.trading_day AS DATE) = l.trade_date
         AND CAST(o.option_type AS VARCHAR) = l.option_code
         AND CAST(o.strike AS DOUBLE) IN (l.short_strike, l.wing_strike)
         AND CAST(o.timestamp AS TIMESTAMP) >= l.entry_ts
         AND CAST(o.timestamp AS TIMESTAMP) <= l.entry_ts + INTERVAL '30 minutes'
        WHERE o.close > 0
        """
        z = con.execute(q).df()
        if not z.empty:
            z["expiry"] = expiry_date
            chunks.append(z)

    con.close()
    if not chunks:
        return pd.DataFrame()

    win = pd.concat(chunks, ignore_index=True)
    win["ts"] = pd.to_datetime(win["ts"]).dt.floor("min")
    win["trade_date"] = pd.to_datetime(win["trade_date"]).dt.date

    trades = []
    unique_setups = setups.drop_duplicates(
        ["trade_date", "entry_ts", "expiry", "side", "width", "short_strike", "wing_strike"]
    )

    for _, r in unique_setups.iterrows():
        q = win[
            (win.trade_date == r.trade_date)
            & (win.expiry == r.expiry)
            & (win.option_type == r.option_code)
            & (win.strike.isin([r.short_strike, r.wing_strike]))
            & (win.ts >= r.entry_ts)
            & (win.ts <= r.entry_ts + pd.Timedelta(minutes=max_hold))
        ]
        if q.empty:
            continue

        a = q[q.strike == r.short_strike][["ts", "high", "low", "close_px"]].rename(
            columns={"high": "shigh", "low": "slow", "close_px": "sclose"}
        )
        b = q[q.strike == r.wing_strike][["ts", "high", "low", "close_px"]].rename(
            columns={"high": "whigh", "low": "wlow", "close_px": "wclose"}
        )
        m = a.merge(b, on="ts").sort_values("ts")
        if m.empty:
            continue

        for hold in HOLDS:
            mm = m[m.ts <= r.entry_ts + pd.Timedelta(minutes=hold)]
            if mm.empty:
                continue

            spread_high_loss = mm.shigh - mm.wlow
            spread_low_loss = mm.slow - mm.whigh

            for stop in STOPS:
                stop_value = float(r.entry_credit) * stop
                target_value = float(r.entry_credit) * TARGET_RATIO
                si = np.flatnonzero(spread_high_loss >= stop_value)
                ti = np.flatnonzero(spread_low_loss <= target_value)
                si = int(si[0]) if len(si) else 10**9
                ti = int(ti[0]) if len(ti) else 10**9

                if si <= ti and si < 10**9:
                    ix, reason = si, "STOP"
                elif ti < 10**9:
                    ix, reason = ti, "TARGET"
                else:
                    ix, reason = len(mm) - 1, "TIME"

                er = mm.iloc[ix]
                net = OptionCostModel().vertical_credit_spread_net_pnl(
                    float(r.short_entry),
                    float(r.wing_entry),
                    float(er.sclose),
                    float(er.wclose),
                    lot(r.trade_date),
                    slippage_points=slippage,
                )
                trades.append({
                    "trade_date": r.trade_date,
                    "ts": r.ts,
                    "expiry": r.expiry,
                    "side": r.side,
                    "width": r.width,
                    "hold": hold,
                    "stop": stop,
                    "net_pnl": net,
                    "reason": reason,
                    "skew": r.skew,
                    "vol_imb": r.vol_imb,
                    "oi_imb": r.oi_imb,
                    "entry_credit": float(r.entry_credit),
                    "short_strike": float(r.short_strike),
                    "wing_strike": float(r.wing_strike),
                })

    return pd.DataFrame(trades)


def summarize(trades, signal_count, slippage, out):
    if trades.empty:
        return {
            "trades": 0,
            "variants": 0,
            "target_qualified": 0,
            "positive_variants": 0,
            "best": None,
            "slippage": slippage,
        }

    board = trades.groupby("variant_id").agg(
        trades=("net_pnl", "size"),
        total_net=("net_pnl", "sum"),
        mean_trade=("net_pnl", "mean"),
        win_rate=("net_pnl", lambda s: float((s > 0).mean())),
    ).reset_index()

    day = trades.groupby(["variant_id", "trade_date"]).net_pnl.sum().reset_index()
    board = board.merge(
        day.groupby("variant_id").net_pnl.mean().rename("mean_active_day_net"),
        on="variant_id",
    )

    pf_rows = []
    for vid, g in trades.groupby("variant_id"):
        pos = g.loc[g.net_pnl > 0, "net_pnl"].sum()
        neg = -g.loc[g.net_pnl < 0, "net_pnl"].sum()
        pf_rows.append((vid, pos / max(neg, 1e-9)))
    board = board.merge(pd.DataFrame(pf_rows, columns=["variant_id", "profit_factor"]), on="variant_id")
    board["target_qualified"] = board.mean_active_day_net >= 1000
    board = board.sort_values("mean_active_day_net", ascending=False)
    board.to_csv(out / "phase17_leaderboard.csv", index=False)

    return {
        "trades": int(len(trades)),
        "variants": int(board.variant_id.nunique()),
        "target_qualified": int(board.target_qualified.sum()),
        "positive_variants": int((board.mean_active_day_net > 0).sum()),
        "best": board.iloc[0].to_dict() if not board.empty else None,
        "signal_rows": int(signal_count),
        "slippage": slippage,
    }


def run(root: Path, out: Path, slippage: float):
    out.mkdir(parents=True, exist_ok=True)
    spot = load_spot(root)
    if spot.empty:
        raise RuntimeError("No NIFTY index rows")

    variants = variant_grid()
    candidates = spot[["trade_date", "ts", "close", "ret10", "rv_ratio"]].drop_duplicates()
    quotes = load_option_quotes(root, candidates)
    if quotes.empty:
        raise RuntimeError("No exact-expiry option quote rows for candidate timestamps")

    setups = build_setups(candidates, quotes)
    filtered = filter_setups(setups, variants)

    if filtered.empty:
        summary = {
            "trades": 0,
            "variants": len(variants),
            "target_qualified": 0,
            "positive_variants": 0,
            "best": None,
            "signal_rows": len(candidates),
            "setup_rows": int(len(setups)),
            "filtered_rows": 0,
            "slippage": slippage,
        }
        (out / "phase17_summary.json").write_text(json.dumps(summary, indent=2, default=str))
        return summary

    unique = filtered.drop_duplicates(
        ["trade_date", "ts", "entry_ts", "expiry", "side", "width", "short_strike", "wing_strike"]
    ).copy()

    trades = simulate(root, unique, out, slippage)
    if trades.empty:
        summary = {
            "trades": 0,
            "variants": len(variants),
            "target_qualified": 0,
            "positive_variants": 0,
            "best": None,
            "signal_rows": len(candidates),
            "setup_rows": int(len(setups)),
            "filtered_rows": int(len(filtered)),
            "slippage": slippage,
        }
        (out / "phase17_summary.json").write_text(json.dumps(summary, indent=2, default=str))
        return summary

    rows = []
    for _, v in filtered.drop_duplicates("variant_id").iterrows():
        mask = (
            trades.trade_date.eq(v.trade_date)
            & trades.ts.eq(v.ts)
            & trades.expiry.eq(v.expiry)
            & trades.side.eq(v.side)
            & trades.width.eq(v.width)
            & trades.hold.eq(v.hold)
            & trades.stop.eq(v.stop)
            & trades.short_strike.eq(v.short_strike)
            & trades.wing_strike.eq(v.wing_strike)
        )
        x = trades.loc[mask].copy()
        if x.empty:
            continue
        x["variant_id"] = v.variant_id
        rows.append(x)

    final = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    final.to_csv(out / "phase17_trades.csv", index=False)
    summary = summarize(final, len(candidates), slippage, out)
    summary["setup_rows"] = int(len(setups))
    summary["filtered_rows"] = int(len(filtered))
    (out / "phase17_summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print(json.dumps(summary, indent=2, default=str))
    return summary


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--slippage", type=float, default=0.20)
    args = ap.parse_args()
    run(args.data, args.out, args.slippage)
