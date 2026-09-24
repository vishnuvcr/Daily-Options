from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from research.cost_model import OptionCostModel
from research.phase19_nifty_short_strangle_regime import (
    END_DATE,
    START_DATE,
    build_setups,
    expiry_files,
    filter_setups,
    load_exact_quotes,
    load_spot,
    lot,
    summarize,
    variant_grid,
)


def _vectorized_net_pnl(trades: pd.DataFrame, slippage: float) -> pd.Series:
    model = OptionCostModel()
    multiplier = trades["lot_size"].astype(float)
    gross = (
        (trades["put_entry"] - trades["put_exit"])
        + (trades["call_entry"] - trades["call_exit"])
    ) * multiplier
    turnover = (
        trades["put_entry"]
        + trades["call_entry"]
        + trades["put_exit"]
        + trades["call_exit"]
    ) * multiplier

    brokerage = 4.0 * model.brokerage_per_order
    exchange = turnover * model.exchange_rate
    sebi = turnover * model.sebi_rate
    stt = (trades["put_entry"] + trades["call_entry"]) * multiplier * model.stt_sell_rate
    stamp = (trades["put_exit"] + trades["call_exit"]) * multiplier * model.stamp_buy_rate
    gst = model.gst_rate * (brokerage + exchange + sebi)
    slippage_cost = 4.0 * slippage * multiplier
    return gross - (brokerage + exchange + sebi + stt + stamp + gst + slippage_cost)


def simulate(root: Path, unique_setups: pd.DataFrame, slippage: float) -> pd.DataFrame:
    """Vectorized-equivalent simulator for the frozen Phase 19 rule.

    The frozen entry/exit/stop/target parameters are unchanged. The important
    correction is that the option execution join derives the option trade date
    from the normalized timestamp, rather than using the dataset's separate
    trading_day field.
    """
    if unique_setups.empty:
        return pd.DataFrame()

    files = dict(expiry_files(root))
    setup_df = unique_setups.reset_index(drop=True).copy()
    setup_df["setup_id"] = np.arange(len(setup_df), dtype=np.int64)
    setup_df["signal_ts"] = pd.to_datetime(setup_df["ts"])

    con = duckdb.connect()
    con.execute("SET TimeZone='Asia/Kolkata'")

    legs = setup_df[
        [
            "setup_id",
            "trade_date",
            "signal_ts",
            "entry_ts",
            "expiry",
            "put_strike",
            "call_strike",
            "put_entry",
            "call_entry",
            "entry_credit",
        ]
    ].drop_duplicates()
    con.register("legs", legs)

    chunks: list[pd.DataFrame] = []
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
        WITH raw AS (
          SELECT
            l.setup_id,
            l.trade_date,
            l.signal_ts,
            l.entry_ts,
            l.put_entry,
            l.call_entry,
            l.entry_credit,
            CAST(o."timestamp" AS TIMESTAMP) AS ts_local,
            CAST(CAST(o."timestamp" AS TIMESTAMP) AS DATE) AS option_trade_date,
            CAST(o.strike AS DOUBLE) AS strike,
            CAST(o.option_type AS VARCHAR) AS option_type,
            CAST(o.high AS DOUBLE) AS high_px,
            CAST(o.low AS DOUBLE) AS low_px,
            CAST(o."close" AS DOUBLE) AS close_px
          FROM read_parquet('{path}') o
          JOIN legs l
            ON l.expiry=DATE '{expiry_date}'
           AND CAST(CAST(o."timestamp" AS TIMESTAMP) AS DATE)=l.trade_date
           AND (
                (o.option_type='PE' AND CAST(o.strike AS DOUBLE)=l.put_strike)
                OR
                (o.option_type='CE' AND CAST(o.strike AS DOUBLE)=l.call_strike)
           )
           AND CAST(o."timestamp" AS TIMESTAMP)>=l.entry_ts
           AND CAST(o."timestamp" AS TIMESTAMP)<=l.entry_ts+INTERVAL '30 minutes'
          WHERE o."close">0
        ),
        paired AS (
          SELECT
            setup_id,
            MAX(trade_date) AS trade_date,
            MAX(signal_ts) AS signal_ts,
            MAX(entry_ts) AS entry_ts,
            MAX(put_entry) AS put_entry,
            MAX(call_entry) AS call_entry,
            MAX(entry_credit) AS entry_credit,
            ts_local,
            MAX(CASE WHEN option_type='PE' THEN high_px END) AS phigh,
            MAX(CASE WHEN option_type='PE' THEN low_px END) AS plow,
            MAX(CASE WHEN option_type='PE' THEN close_px END) AS pclose,
            MAX(CASE WHEN option_type='CE' THEN high_px END) AS chigh,
            MAX(CASE WHEN option_type='CE' THEN low_px END) AS clow,
            MAX(CASE WHEN option_type='CE' THEN close_px END) AS cclose
          FROM raw
          WHERE option_trade_date=trade_date
          GROUP BY setup_id, ts_local
        ),
        params(hold_min, stop_mult) AS (
          VALUES
            (15, 1.25),
            (15, 1.50),
            (30, 1.25),
            (30, 1.50)
        ),
        windowed AS (
          SELECT p.*, prm.hold_min, prm.stop_mult
          FROM paired p
          CROSS JOIN params prm
          WHERE p.ts_local <= p.entry_ts + prm.hold_min * INTERVAL '1 minute'
            AND p.phigh IS NOT NULL
            AND p.plow IS NOT NULL
            AND p.chigh IS NOT NULL
            AND p.clow IS NOT NULL
            AND p.pclose IS NOT NULL
            AND p.cclose IS NOT NULL
        ),
        trigger_times AS (
          SELECT
            setup_id,
            hold_min,
            stop_mult,
            MIN(
              CASE
                WHEN phigh + chigh >= entry_credit * stop_mult THEN ts_local
              END
            ) AS stop_ts,
            MIN(
              CASE
                WHEN plow + clow <= entry_credit * 0.50 THEN ts_local
              END
            ) AS target_ts,
            MAX(ts_local) AS time_ts
          FROM windowed
          GROUP BY setup_id, hold_min, stop_mult
        ),
        decisions AS (
          SELECT
            setup_id,
            hold_min,
            stop_mult,
            CASE
              WHEN stop_ts IS NOT NULL
                   AND (target_ts IS NULL OR stop_ts <= target_ts)
                THEN stop_ts
              WHEN target_ts IS NOT NULL
                THEN target_ts
              ELSE time_ts
            END AS exit_ts,
            CASE
              WHEN stop_ts IS NOT NULL
                   AND (target_ts IS NULL OR stop_ts <= target_ts)
                THEN 'STOP'
              WHEN target_ts IS NOT NULL
                THEN 'TARGET'
              ELSE 'TIME'
            END AS reason
          FROM trigger_times
        )
        SELECT
          d.setup_id,
          w.trade_date,
          w.signal_ts,
          w.entry_ts,
          w.put_entry,
          w.call_entry,
          w.entry_credit,
          w.put_strike,
          w.call_strike,
          w.ts_local AS exit_ts,
          w.pclose AS put_exit,
          w.cclose AS call_exit,
          d.hold_min,
          d.stop_mult,
          d.reason
        FROM decisions d
        JOIN windowed w
          ON w.setup_id=d.setup_id
         AND w.hold_min=d.hold_min
         AND w.stop_mult=d.stop_mult
         AND w.ts_local=d.exit_ts
        JOIN legs l
          ON l.setup_id=d.setup_id
        """
        z = con.execute(q).df()
        if not z.empty:
            z["expiry"] = pd.Timestamp(expiry_date).date()
            chunks.append(z)

    con.close()
    if not chunks:
        return pd.DataFrame()

    trades = pd.concat(chunks, ignore_index=True)
    trades["trade_date"] = pd.to_datetime(trades["trade_date"]).dt.date
    trades["signal_ts"] = pd.to_datetime(trades["signal_ts"])
    trades["entry_ts"] = pd.to_datetime(trades["entry_ts"])
    trades["exit_ts"] = pd.to_datetime(trades["exit_ts"])

    trades["put_strike"] = trades["put_strike"].astype(float)
    trades["call_strike"] = trades["call_strike"].astype(float)
    trades["lot_size"] = trades["trade_date"].map(lot).astype(float)
    trades["net_pnl"] = _vectorized_net_pnl(trades, slippage)

    return trades[
        [
            "setup_id",
            "trade_date",
            "signal_ts",
            "entry_ts",
            "exit_ts",
            "expiry",
            "hold_min",
            "stop_mult",
            "put_strike",
            "call_strike",
            "put_entry",
            "call_entry",
            "put_exit",
            "call_exit",
            "net_pnl",
            "reason",
            "entry_credit",
        ]
    ].rename(
        columns={
            "signal_ts": "ts",
            "hold_min": "hold",
            "stop_mult": "stop",
        }
    )


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
        "runtime_version": "phase19-v2-vectorized-date-safe",
        "start_date": START_DATE,
        "end_date": END_DATE,
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
            "put_entry",
            "call_entry",
            "entry_credit",
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

    mapping_keys = [
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
    mapping = filtered[mapping_keys + ["variant_id"]].drop_duplicates()
    trades = trades.merge(mapping, on=mapping_keys, how="inner")

    trades.to_csv(out / "phase19_trades.csv", index=False)
    summary = summarize(trades, len(spot), slippage, out)
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
