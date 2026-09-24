from __future__ import annotations
import json
from pathlib import Path
import duckdb
import pandas as pd

ENTRY_TIMES=("14:30:00","14:45:00","15:00:00")

def expiry_files(root: Path):
    out=[]
    for p in sorted((root/"options"/"NIFTY").glob("*.parquet")):
        try:
            out.append((pd.Timestamp(p.stem).date(),p))
        except Exception:
            pass
    return out

def inspect_file(path: Path):
    con=duckdb.connect()
    con.execute("SET TimeZone='Asia/Kolkata'")
    p=str(path).replace("'", "''")
    sample=con.execute(f"""
        SELECT *
        FROM read_parquet('{p}')
        LIMIT 10
    """).df()
    schema=con.execute(f"""
        DESCRIBE SELECT *
        FROM read_parquet('{p}')
    """).df()
    option_types=con.execute(f"""
        SELECT DISTINCT CAST(option_type AS VARCHAR) AS option_type
        FROM read_parquet('{p}')
        ORDER BY 1
    """).df()
    time_range=con.execute(f"""
        SELECT
          MIN("timestamp") AS min_ts,
          MAX("timestamp") AS max_ts,
          COUNT(*) AS row_count
        FROM read_parquet('{p}')
    """).df()
    trading_days=con.execute(f"""
        SELECT
          MIN(CAST(trading_day AS DATE)) AS min_day,
          MAX(CAST(trading_day AS DATE)) AS max_day
        FROM read_parquet('{p}')
    """).df()
    con.close()
    return {
        "sample_columns": sample.columns.tolist(),
        "sample_rows": sample.head(5).to_dict("records"),
        "schema": schema.to_dict("records"),
        "distinct_option_type": option_types.option_type.tolist() if "option_type" in option_types.columns else [],
        "time_range": time_range.to_dict("records"),
        "trading_day_range": trading_days.to_dict("records"),
    }

def probe_file(path: Path, trade_date):
    con=duckdb.connect()
    con.execute("SET TimeZone='Asia/Kolkata'")
    p=str(path).replace("'", "''")
    rows=con.execute(f"""
        SELECT
          "timestamp" AS ts,
          CAST(trading_day AS DATE) AS trade_date,
          CAST(strike AS DOUBLE) AS strike,
          CAST(option_type AS VARCHAR) AS option_type,
          CAST(open AS DOUBLE) AS open_px,
          CAST("close" AS DOUBLE) AS close_px,
          CAST(volume AS DOUBLE) AS volume,
          CAST(open_interest AS DOUBLE) AS oi
        FROM read_parquet('{p}')
        WHERE CAST(trading_day AS DATE)=DATE '{trade_date}'
          AND CAST("timestamp" AS TIME) IN (
            TIME '14:30:00', TIME '14:31:00',
            TIME '14:45:00', TIME '14:46:00',
            TIME '15:00:00', TIME '15:01:00'
          )
          AND "close" > 0
        ORDER BY "timestamp", strike
        LIMIT 80
    """).df()
    con.close()
    return {
        "trade_date": str(trade_date),
        "row_count": int(len(rows)),
        "option_types": sorted(rows.option_type.dropna().unique().tolist()) if not rows.empty else [],
        "signal_rows_by_time": rows.groupby(rows.ts.astype(str).str[11:19]).size().to_dict() if not rows.empty else {},
        "strike_count": int(rows.strike.nunique()) if not rows.empty else 0,
        "strike_min": float(rows.strike.min()) if not rows.empty else None,
        "strike_max": float(rows.strike.max()) if not rows.empty else None,
        "sample_rows": rows.head(40).to_dict("records"),
    }

def main(root: Path, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    files=expiry_files(root)
    if not files:
        raise RuntimeError("No exact-expiry NIFTY option files found")
    first_date,first_path=files[0]
    last_date,last_path=files[-1]
    result={
        "file_count": len(files),
        "first_expiry": str(first_date),
        "last_expiry": str(last_date),
        "first_file": str(first_path),
        "last_file": str(last_path),
        "first_file_inspection": inspect_file(first_path),
        "first_file_probe": probe_file(first_path, first_date),
    }
    (out/"phase17a_diagnostic.json").write_text(json.dumps(result,indent=2,default=str))
    (out/"phase17a_diagnostic.txt").write_text(json.dumps(result,indent=2,default=str))
    print(json.dumps(result,indent=2,default=str))

if __name__=="__main__":
    import sys
    main(Path(sys.argv[1]),Path(sys.argv[2]))
