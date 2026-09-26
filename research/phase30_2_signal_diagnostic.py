from __future__ import annotations

import json
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path("data/cache/phase30_2_rissin")
OUT = Path("reports/phase30_2_signal_diagnostic.json")
CHECKS = [
    ("2025-09-09", "2025-09-16", "2025-09-03"),
    ("2025-09-16", "2025-09-23", "2025-09-10"),
]
ENTRY_TIMES = ["09:30:00", "10:00:00", "11:00:00", "13:00:00", "14:00:00"]
TARGETS = [20.0, 25.0, 30.0]


def normalize(raw):
    raw = pd.Series(raw, copy=False).astype(str).str.strip()
    aware = raw.str.contains(r"(?:[+-]\d{2}:?\d{2}|Z)$", regex=True, na=False)
    ts = pd.Series(pd.NaT, index=raw.index, dtype="datetime64[ns]")
    if aware.any():
        parsed = pd.to_datetime(raw[aware], errors="coerce", utc=True)
        ts.loc[aware] = parsed.dt.tz_convert("Asia/Kolkata").dt.tz_localize(None)
    naive = ~aware
    if naive.any():
        parsed = pd.to_datetime(raw[naive], errors="coerce")
        ts.loc[naive] = parsed.dt.tz_localize("Asia/Kolkata").dt.tz_localize(None)
    return ts.dt.floor("min")


def load_day(con, expiry, entry_date):
    path = str(ROOT / "NIFTY_*.parquet")
    q = f"""
    SELECT CAST(timestamp AS VARCHAR) AS ts_raw,
           CAST(expiry AS DATE) AS expiry,
           CAST(strike AS DOUBLE) AS strike,
           upper(option_type) AS option_type,
           CAST(open AS DOUBLE) AS open_px,
           CAST(close AS DOUBLE) AS close_px
    FROM read_parquet('{path}')
    WHERE upper(underlying)='NIFTY'
      AND granularity='1min'
      AND CAST(expiry AS DATE)=DATE '{expiry}'
      AND CAST(date AS DATE)=DATE '{entry_date}'
      AND CAST(timestamp AS TIMESTAMP)
            BETWEEN TIMESTAMP '{entry_date} 09:00:00'
            AND TIMESTAMP '{entry_date} 15:15:00'
      AND open > 0
      AND close > 0
    ORDER BY option_type, strike, ts_raw
    """
    df = con.execute(q).df()
    if not df.empty:
        df["ts"] = normalize(df["ts_raw"])
    return df


def select_near(df, side, target):
    s = df[df.option_type == side]
    if s.empty:
        return None
    return s.iloc[(s.close_px - target).abs().argmin()]


def select_far(df, side, target, ref_strike, mode):
    s = df[df.option_type == side].copy()
    if mode == "SAME_STRIKE":
        s = s[s.strike == float(ref_strike)]
    elif side == "CE":
        s = s[s.strike >= float(ref_strike)]
    else:
        s = s[s.strike <= float(ref_strike)]
    if s.empty:
        return None
    return s.iloc[(s.close_px - target).abs().argmin()]


def inspect(con, near_expiry, far_expiry, entry_date):
    near = load_day(con, near_expiry, entry_date)
    far = load_day(con, far_expiry, entry_date)
    out = {
        "near_expiry": near_expiry,
        "far_expiry": far_expiry,
        "entry_date": entry_date,
        "near_rows": int(len(near)),
        "far_rows": int(len(far)),
        "near_timestamp_range": None if near.empty else [str(near.ts.min()), str(near.ts.max())],
        "far_timestamp_range": None if far.empty else [str(far.ts.min()), str(far.ts.max())],
        "checks": {},
    }
    for t in ENTRY_TIMES:
        signal_ts = pd.Timestamp(f"{entry_date} {t}")
        fill_ts = signal_ts + pd.Timedelta(minutes=1)
        ns = near[near.ts == signal_ts]
        nf = near[near.ts == fill_ts]
        fs = far[far.ts == signal_ts]
        ff = far[far.ts == fill_ts]
        record = {
            "near_signal_rows": int(len(ns)),
            "far_signal_rows": int(len(fs)),
            "near_fill_rows": int(len(nf)),
            "far_fill_rows": int(len(ff)),
            "modes": {},
        }
        for target in TARGETS:
            nce = select_near(ns, "CE", target)
            npe = select_near(ns, "PE", target)
            if nce is None or npe is None:
                record["modes"][str(target)] = None
                continue
            mode_out = {}
            for mode in ("SAME_STRIKE", "DIAGONAL_PREMIUM"):
                fce = select_far(fs, "CE", target, nce.strike, mode)
                fpe = select_far(fs, "PE", target, npe.strike, mode)
                if fce is None or fpe is None:
                    mode_out[mode] = {"far_selection": False}
                    continue
                nce_fill = nf[(nf.option_type == "CE") & (nf.strike == nce.strike)]
                npe_fill = nf[(nf.option_type == "PE") & (nf.strike == npe.strike)]
                fce_fill = ff[(ff.option_type == "CE") & (ff.strike == fce.strike)]
                fpe_fill = ff[(ff.option_type == "PE") & (ff.strike == fpe.strike)]
                if any(x.empty for x in (nce_fill, npe_fill, fce_fill, fpe_fill)):
                    mode_out[mode] = {
                        "far_selection": True,
                        "fill_complete": False,
                        "near_strikes": [float(nce.strike), float(npe.strike)],
                        "far_strikes": [float(fce.strike), float(fpe.strike)],
                    }
                    continue
                sc = float(nce_fill.iloc[0].open_px)
                sp = float(npe_fill.iloc[0].open_px)
                fc = float(fce_fill.iloc[0].open_px)
                fp = float(fpe_fill.iloc[0].open_px)
                credit = 5.0 * (sc + sp) - 3.0 * (fc + fp)
                mode_out[mode] = {
                    "far_selection": True,
                    "fill_complete": True,
                    "near_strikes": [float(nce.strike), float(npe.strike)],
                    "far_strikes": [float(fce.strike), float(fpe.strike)],
                    "entry_prices": {"sc": sc, "sp": sp, "fc": fc, "fp": fp},
                    "credit": credit,
                    "positive_credit": bool(credit > 0),
                }
            record["modes"][str(target)] = mode_out
        out["checks"][t] = record
    return out


def main():
    con = duckdb.connect()
    con.execute("SET TimeZone='Asia/Kolkata'")
    report = {
        "source": str(ROOT),
        "checks": [inspect(con, near, far, entry) for near, far, entry in CHECKS],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
