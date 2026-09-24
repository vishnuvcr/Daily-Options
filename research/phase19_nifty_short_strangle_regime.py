from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from research.cost_model import OptionCostModel

ENTRY_TIMES = ("14:30:00", "14:45:00", "15:00:00")
SHORT_OFFSETS = (1, 2, 3)
ABS_RET_MAX = (0.0015, 0.0030)
RV_RATIO_MAX = (1.00, 1.25)
HOLDS = (15, 30)
STOPS = (1.25, 1.50)
TARGET_RATIO = 0.50
MAX_ENTRY_DELAY_MINUTES = 3
START_DATE = "2021-05-27"
END_DATE = "2026-08-04"


def expiry_files(root: Path):
    out = []
    for p in sorted((root / "options" / "NIFTY").glob("*.parquet")):
        try:
            out.append((pd.Timestamp(p.stem).date(), p))
        except Exception:
            pass
    if not out:
        raise FileNotFoundError("No exact-expiry NIFTY files")
    return out


def expiry_for_day(files, d):
    td = pd.Timestamp(d).date()
    fut = [x for x in files if x[0] >= td]
    return min(fut, key=lambda x: x[0]) if fut else None


def ist_wall(x):
    return (
        pd.to_datetime(x, utc=True)
        .dt.tz_convert("Asia/Kolkata")
        .dt.tz_localize(None)
        .dt.floor("min")
    )


def load_spot(root: Path):
    p = root / "index" / "NIFTY.parquet"
    con = duckdb.connect()
    con.execute("SET TimeZone='Asia/Kolkata'")
    q = f"""
    WITH b AS (
      SELECT "timestamp" AS ts,
             CAST(trading_day AS DATE) AS trade_date,
             CAST("close" AS DOUBLE) AS spot_close
      FROM read_parquet('{p}')
      WHERE CAST(trading_day AS DATE) BETWEEN DATE '{START_DATE}' AND DATE '{END_DATE}'
        AND "close" > 0
    ),
    r AS (
      SELECT *,
             spot_close / LAG(spot_close,10) OVER(PARTITION BY trade_date ORDER BY ts) - 1 AS ret10,
             spot_close / LAG(spot_close,1) OVER(PARTITION BY trade_date ORDER BY ts) - 1 AS ret1
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
               ),0
             ) AS rv_ratio
      FROM v
    )
    SELECT trade_date, ts, spot_close, ret10, rv20, rv_ratio
    FROM z
    WHERE ret10 IS NOT NULL
      AND rv20 IS NOT NULL
      AND rv_ratio IS NOT NULL
      AND strftime(ts,'%H:%M:%S') IN ('14:30:00','14:45:00','15:00:00')
    ORDER BY trade_date, ts
    """
    x = con.execute(q).df()
    con.close()
    if x.empty:
        return x
    x["trade_date"] = pd.to_datetime(x["trade_date"]).dt.date
    x["ts"] = ist_wall(x["ts"])
    return x


def variant_grid():
    return [
        dict(
            entry_time=e,
            short_offset=so,
            abs_ret=ar,
            rv_max=rv,
            hold=h,
            stop=st,
        )
        for e in ENTRY_TIMES
        for so in SHORT_OFFSETS
        for ar in ABS_RET_MAX
        for rv in RV_RATIO_MAX
        for h in HOLDS
        for st in STOPS
    ]


def variant_id(v):
    return (
        f'{v["entry_time"]}|so{v["short_offset"]}|'
        f'r{v["abs_ret"]}|rv{v["rv_max"]}|'
        f'h{v["hold"]}|s{v["stop"]}'
    )


def load_exact_quotes(root, spot):
    files = expiry_files(root)
    chosen = {d: expiry_for_day(files, d) for d in spot["trade_date"].unique()}
    chosen = {d: x for d, x in chosen.items() if x is not None}
    if not chosen:
        return pd.DataFrame()

    con = duckdb.connect()
    con.execute("SET TimeZone='Asia/Kolkata'")
    chunks = []

    for expiry_date, path in sorted(set(chosen.values()), key=lambda x: x[0]):
        dates = [d for d, (ed, _) in chosen.items() if ed == expiry_date]
        if not dates:
            continue
        vals = ",".join(f"DATE '{d}'" for d in dates)
        q = f"""
        SELECT "timestamp" AS ts,
               CAST(trading_day AS DATE) AS trade_date,
               CAST(strike AS DOUBLE) AS strike,
               CAST(option_type AS VARCHAR) AS option_type,
               CAST(open AS DOUBLE) AS open_px,
               CAST(high AS DOUBLE) AS high,
               CAST(low AS DOUBLE) AS low,
               CAST("close" AS DOUBLE) AS close_px
        FROM read_parquet('{path}')
        WHERE CAST(trading_day AS DATE) IN ({vals})
          AND "close" > 0
          AND strftime("timestamp",'%H:%M:%S') >= '14:30:00'
          AND strftime("timestamp",'%H:%M:%S') <= '15:03:00'
        """
        z = con.execute(q).df()
        if not z.empty:
            z["ts"] = ist_wall(z["ts"])
            z["expiry"] = expiry_date
            chunks.append(z)

    con.close()
    return pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()

def build_setups(spot, quotes):
    if quotes.empty:
        return pd.DataFrame()

    rows = []
    for (d, ts), sm in spot.groupby(["trade_date", "ts"], sort=False):
        sm = sm.iloc[0]
        q = quotes[
            (quotes["trade_date"] == d)
            & (quotes["ts"] >= ts)
            & (quotes["ts"] <= ts + pd.Timedelta(minutes=MAX_ENTRY_DELAY_MINUTES))
        ]
        sig = q[q["ts"] == ts]
        if sig.empty:
            continue

        strikes = np.sort(sig["strike"].dropna().unique())
        if len(strikes) < 7:
            continue

        atm = int(np.argmin(np.abs(strikes - float(sm["spot_close"]))))

        for so in SHORT_OFFSETS:
            pi = atm - so
            ci = atm + so
            if pi < 0 or ci >= len(strikes):
                continue

            put_strike = float(strikes[pi])
            call_strike = float(strikes[ci])

            put_q = q[
                (q["option_type"] == "PE")
                & (q["strike"] == put_strike)
                & (q["ts"] > ts)
            ]
            call_q = q[
                (q["option_type"] == "CE")
                & (q["strike"] == call_strike)
                & (q["ts"] > ts)
            ]
            if put_q.empty or call_q.empty:
                continue

            common = sorted(set(put_q["ts"]).intersection(set(call_q["ts"])))
            if not common:
                continue

            entry_ts = common[0]
            pr = put_q[put_q["ts"] == entry_ts].head(1)
            cr = call_q[call_q["ts"] == entry_ts].head(1)
            if pr.empty or cr.empty:
                continue

            put_entry = float(pr.iloc[0]["open_px"])
            call_entry = float(cr.iloc[0]["open_px"])
            entry_credit = put_entry + call_entry
            if not np.isfinite(entry_credit) or entry_credit <= 0:
                continue

            rows.append({
                "trade_date": d,
                "ts": ts,
                "entry_ts": entry_ts,
                "entry_delay_min": float((entry_ts - ts).total_seconds() / 60.0),
                "expiry": pr.iloc[0]["expiry"],
                "short_offset": so,
                "put_strike": put_strike,
                "call_strike": call_strike,
                "put_entry": put_entry,
                "call_entry": call_entry,
                "entry_credit": entry_credit,
                "spot_ret10": float(sm["ret10"]),
                "rv_ratio": float(sm["rv_ratio"]),
            })

    return pd.DataFrame(rows)


def filter_setups(setups):
    if setups.empty:
        return pd.DataFrame()

    out = []
    for v in variant_grid():
        s = setups[
            (setups["ts"].dt.strftime("%H:%M:%S") == v["entry_time"])
            & (setups["short_offset"] == v["short_offset"])
            & (setups["spot_ret10"].abs() <= v["abs_ret"])
            & (setups["rv_ratio"] <= v["rv_max"])
        ].copy()
        if s.empty:
            continue
        s["variant_id"] = variant_id(v)
        s["hold"] = v["hold"]
        s["stop"] = v["stop"]
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


def simulate(root, unique_setups, slippage):
    if unique_setups.empty:
        return pd.DataFrame()

    files = dict(expiry_files(root))
    setup_df = unique_setups.reset_index(drop=True).copy()
    setup_df["setup_id"] = np.arange(len(setup_df), dtype=np.int64)

    con = duckdb.connect()
    con.execute("SET TimeZone='Asia/Kolkata'")
    legs = setup_df[
        [
            "setup_id",
            "trade_date",
            "entry_ts",
            "expiry",
            "put_strike",
            "call_strike",
        ]
    ].drop_duplicates()
    con.register("legs", legs)

    chunks = []
    for expiry_date, path in sorted(files.items()):
        active = int(
            con.execute(
                "SELECT COUNT(*) FROM legs WHERE expiry=?",
                [expiry_date],
            ).fetchone()[0]
        )
        if active == 0:
            continue

        q = f"""
        SELECT
          l.setup_id,
          CAST(o."timestamp" AS TIMESTAMP) AS ts_local,
          CAST(o.trading_day AS DATE) AS trade_date,
          CAST(o.strike AS DOUBLE) AS strike,
          CAST(o.option_type AS VARCHAR) AS option_type,
          CAST(o.high AS DOUBLE) AS high,
          CAST(o.low AS DOUBLE) AS low,
          CAST(o."close" AS DOUBLE) AS close_px
        FROM read_parquet('{path}') o
        JOIN legs l
          ON l.expiry=DATE '{expiry_date}'
         AND CAST(o.trading_day AS DATE)=l.trade_date
         AND (
              (o.option_type='PE' AND CAST(o.strike AS DOUBLE)=l.put_strike)
              OR
              (o.option_type='CE' AND CAST(o.strike AS DOUBLE)=l.call_strike)
         )
         AND CAST(o."timestamp" AS TIMESTAMP)>=l.entry_ts
         AND CAST(o."timestamp" AS TIMESTAMP)<=l.entry_ts+INTERVAL '30 minutes'
        WHERE o."close">0
        """
        z = con.execute(q).df()
        if not z.empty:
            z["ts"] = pd.to_datetime(z["ts"]).dt.floor("min")
            z["expiry"] = expiry_date
            chunks.append(z)

    con.close()
    if not chunks:
        return pd.DataFrame()

    win = pd.concat(chunks, ignore_index=True)
    lookup = setup_df.set_index("setup_id")

    trades = []
    for setup_id, q in win.groupby("setup_id", sort=False):
        r = lookup.loc[setup_id]

        p = q[q["strike"] == r["put_strike"]][
            ["ts", "high", "low", "close_px"]
        ].rename(
            columns={"high": "phigh", "low": "plow", "close_px": "pclose"}
        )
        c = q[q["strike"] == r["call_strike"]][
            ["ts", "high", "low", "close_px"]
        ].rename(
            columns={"high": "chigh", "low": "clow", "close_px": "cclose"}
        )

        m = p.merge(c, on="ts").sort_values("ts")
        if m.empty:
            continue

        for hold in HOLDS:
            mm = m[m["ts"] <= r["entry_ts"] + pd.Timedelta(minutes=hold)]
            if mm.empty:
                continue

            debit_high = mm["phigh"] + mm["chigh"]
            debit_low = mm["plow"] + mm["clow"]

            for stop in STOPS:
                stop_value = float(r["entry_credit"]) * stop
                target_value = float(r["entry_credit"]) * TARGET_RATIO

                si = np.flatnonzero(debit_high.to_numpy() >= stop_value)
                ti = np.flatnonzero(debit_low.to_numpy() <= target_value)
                si = int(si[0]) if len(si) else 10**9
                ti = int(ti[0]) if len(ti) else 10**9

                if si <= ti and si < 10**9:
                    ix, reason = si, "STOP"
                elif ti < 10**9:
                    ix, reason = ti, "TARGET"
                else:
                    ix, reason = len(mm) - 1, "TIME"

                er = mm.iloc[ix]
                pnl = OptionCostModel().short_strangle_net_pnl(
                    float(r["put_entry"]),
                    float(r["call_entry"]),
                    float(er["pclose"]),
                    float(er["cclose"]),
                    lot(r["trade_date"]),
                    slippage_points=slippage,
                )
                trades.append({
                    "setup_id": int(setup_id),
                    "trade_date": r["trade_date"],
                    "ts": r["ts"],
                    "expiry": r["expiry"],
                    "short_offset": int(r["short_offset"]),
                    "hold": hold,
                    "stop": stop,
                    "put_strike": float(r["put_strike"]),
                    "call_strike": float(r["call_strike"]),
                    "net_pnl": pnl,
                    "reason": reason,
                    "entry_credit": float(r["entry_credit"]),
                    "entry_delay_min": float(r["entry_delay_min"]),
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
            "signal_rows": int(signal_count),
            "slippage": slippage,
        }

    rows = []
    for vid, g in trades.groupby("variant_id"):
        day = g.groupby("trade_date")["net_pnl"].sum()
        pos = float(g.loc[g["net_pnl"] > 0, "net_pnl"].sum())
        neg = float(-g.loc[g["net_pnl"] < 0, "net_pnl"].sum())
        rows.append({
            "variant_id": vid,
            "trades": int(len(g)),
            "active_days": int(len(day)),
            "mean_active_day_net": float(day.mean()),
            "mean_trade_net": float(g["net_pnl"].mean()),
            "win_rate": float((g["net_pnl"] > 0).mean()),
            "profit_factor": pos / max(1e-9, neg),
            "max_drawdown": float((day.cumsum() - day.cumsum().cummax()).min()),
            "total_net": float(g["net_pnl"].sum()),
        })

    board = pd.DataFrame(rows).sort_values("mean_active_day_net", ascending=False)
    board["target_qualified"] = board["mean_active_day_net"] >= 1000
    board.to_csv(out / "phase19_leaderboard.csv", index=False)
    best = board.iloc[0].to_dict() if not board.empty else None

    return {
        "trades": int(len(trades)),
        "variants": int(len(board)),
        "target_qualified": int(board["target_qualified"].sum()),
        "positive_variants": int((board["mean_active_day_net"] > 0).sum()),
        "best": best,
        "signal_rows": int(signal_count),
        "slippage": slippage,
    }


def run(root: Path, out: Path, slippage: float):
    out.mkdir(parents=True, exist_ok=True)
    spot = load_spot(root)
    if spot.empty:
        raise RuntimeError("No NIFTY index rows")

    quotes = load_exact_quotes(root, spot)
    setups = build_setups(spot, quotes)
    filtered = filter_setups(setups)

    summary_base = {
        "signal_rows": int(len(spot)),
        "quote_rows": int(len(quotes)),
        "setup_rows": int(len(setups)),
        "filtered_setup_rows": int(len(filtered)),
        "slippage": slippage,
    }

    if filtered.empty:
        summary = {
            **summary_base,
            "trades": 0,
            "variants": len(variant_grid()),
            "target_qualified": 0,
            "positive_variants": 0,
            "best": None,
        }
        (out / "phase19_summary.json").write_text(json.dumps(summary, indent=2, default=str))
        return summary

    unique = filtered.drop_duplicates(
        [
            "trade_date",
            "ts",
            "entry_ts",
            "expiry",
            "short_offset",
            "put_strike",
            "call_strike",
            "hold",
            "stop",
        ]
    ).copy()

    trades = simulate(root, unique, slippage)
    if trades.empty:
        summary = {
            **summary_base,
            "trades": 0,
            "variants": len(variant_grid()),
            "target_qualified": 0,
            "positive_variants": 0,
            "best": None,
        }
        (out / "phase19_summary.json").write_text(json.dumps(summary, indent=2, default=str))
        return summary

    rows = []
    variants = variant_grid()
    for _, vrow in filtered.drop_duplicates(
        [
            "trade_date",
            "ts",
            "entry_ts",
            "expiry",
            "short_offset",
            "put_strike",
            "call_strike",
            "hold",
            "stop",
            "variant_id",
        ]
    ).iterrows():
        m = (
            (trades["trade_date"] == vrow["trade_date"])
            & (trades["ts"] == vrow["ts"])
            & (trades["expiry"] == vrow["expiry"])
            & (trades["short_offset"] == vrow["short_offset"])
            & (trades["hold"] == vrow["hold"])
            & (trades["stop"] == vrow["stop"])
            & (trades["put_strike"] == vrow["put_strike"])
            & (trades["call_strike"] == vrow["call_strike"])
        )
        x = trades.loc[m].copy()
        if x.empty:
            continue
        x["variant_id"] = vrow["variant_id"]
        rows.append(x)

    final = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    if not final.empty:
        final.to_csv(out / "phase19_trades.csv", index=False)

    summary = summarize(final, len(spot), slippage, out)
    summary.update(summary_base)
    (out / "phase19_summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print(json.dumps(summary, indent=2, default=str))
    return summary


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--slippage", type=float, default=0.20)
    args = ap.parse_args()
    run(args.data, args.out, args.slippage)
