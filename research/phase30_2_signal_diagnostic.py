from __future__ import annotations

import json
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path("data/cache/phase30_2_rissin")
OUT = Path("reports/phase30_2_signal_diagnostic.json")
CHECKS = [
    ("2025-09-09", "2025-09-03"),
    ("2025-09-16", "2025-09-10"),
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


def inspect(con, expiry, entry_date):
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
    if df.empty:
        return {"expiry": expiry, "entry_date": entry_date, "rows": 0}

    df["ts"] = normalize(df["ts_raw"])
    out = {
        "expiry": expiry,
        "entry_date": entry_date,
        "rows": int(len(df)),
        "raw_timestamp_sample": sorted(df.ts_raw.dropna().unique().tolist())[:20],
        "normalized_min": str(df.ts.min()),
        "normalized_max": str(df.ts.max()),
        "signal_counts": {},
        "fill_counts": {},
        "target_examples": {},
    }

    for t in ENTRY_TIMES:
        signal_ts = pd.Timestamp(f"{entry_date} {t}")
        fill_ts = signal_ts + pd.Timedelta(minutes=1)
        s = df[df.ts == signal_ts]
        f = df[df.ts == fill_ts]

        out["signal_counts"][t] = {
            "rows": int(len(s)),
            "CE": int((s.option_type == "CE").sum()),
            "PE": int((s.option_type == "PE").sum()),
        }
        out["fill_counts"][t] = {
            "rows": int(len(f)),
            "CE": int((f.option_type == "CE").sum()),
            "PE": int((f.option_type == "PE").sum()),
        }

        ex = {}
        for side in ("CE", "PE"):
            ss = s[s.option_type == side]
            vals = {}
            for target in TARGETS:
                if ss.empty:
                    vals[str(target)] = None
                    continue
                row = ss.iloc[(ss.close_px - target).abs().argmin()]
                same = f[(f.option_type == side) & (f.strike == row.strike)]
                vals[str(target)] = {
                    "strike": float(row.strike),
                    "close_px": float(row.close_px),
                    "fill_rows_same_strike": int(len(same)),
                    "fill_open": None if same.empty else float(same.iloc[0].open_px),
                }
            ex[side] = vals
        out["target_examples"][t] = ex

    return out


def main():
    con = duckdb.connect()
    con.execute("SET TimeZone='Asia/Kolkata'")
    report = {
        "source": str(ROOT),
        "checks": [inspect(con, expiry, entry) for expiry, entry in CHECKS],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
