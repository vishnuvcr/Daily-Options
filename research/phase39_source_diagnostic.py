from __future__ import annotations
import json
from pathlib import Path
import duckdb
import pandas as pd

ROOT = Path("data/cache/phase39_trademarkk")
OUT = Path("reports/phase39/diagnostics/source_snapshot_diagnostic.json")

def qdf(con, sql):
    return con.execute(sql).df()

def main():
    con = duckdb.connect()
    con.execute("SET TimeZone='Asia/Kolkata'")
    idx = qdf(con, f"""
        SELECT CAST(trading_day AS DATE) AS trade_date,
               CAST(timestamp AS TIMESTAMP) AS ts,
               CAST(close AS DOUBLE) AS close_px
        FROM read_parquet('{ROOT / "index" / "NIFTY.parquet"}', union_by_name=true)
        WHERE CAST(trading_day AS DATE) BETWEEN DATE '2021-07-01' AND DATE '2021-07-15'
          AND strftime(CAST(timestamp AS TIMESTAMP), '%H:%M:%S')='09:30:00'
        ORDER BY trade_date
    """)
    option_files = sorted((ROOT / "options" / "NIFTY").glob("*.parquet"))
    exps = [pd.Timestamp(p.stem).date() for p in option_files]
    rows = []
    for r in idx.itertuples(index=False):
        d = pd.Timestamp(r.trade_date).date()
        future = [e for e in exps if e > d]
        if not future:
            continue
        expiry = future[0]
        p = ROOT / "options" / "NIFTY" / f"{expiry}.parquet"
        if not p.exists():
            continue
        atm = round(float(r.close_px) / 50.0) * 50.0
        # Show both exact ATM and nearest surrounding strikes; timestamps are authoritative.
        ps = str(p).replace("'", "''")
        d0 = str(d)
        sql = f"""
            WITH src AS (
                SELECT
                    CAST(timestamp AS TIMESTAMP) AS ts,
                    CAST(timestamp AS DATE) AS ts_date,
                    CAST(trading_day AS DATE) AS trading_day,
                    UPPER(CAST(option_type AS VARCHAR)) AS option_type,
                    CAST(strike AS DOUBLE) AS strike,
                    CAST(close AS DOUBLE) AS close_px
                FROM read_parquet('{ps}', union_by_name=true)
                WHERE CAST(timestamp AS DATE)=DATE '{d0}'
                  AND strftime(CAST(timestamp AS TIMESTAMP),'%H:%M:%S') BETWEEN '09:00:00' AND '09:30:00'
                  AND UPPER(CAST(option_type AS VARCHAR)) IN ('CE','PE')
                  AND close>0
                  AND ABS(CAST(strike AS DOUBLE)-{atm}) <= 100
            )
            SELECT * FROM src
            ORDER BY ts DESC, strike, option_type
            LIMIT 40
        """
        z = qdf(con, sql)
        rows.append({
            "trade_date": str(d),
            "spot_0930": float(r.close_px),
            "atm_strike_python_round": float(atm),
            "expiry": str(expiry),
            "row_count": int(len(z)),
            "rows": z.to_dict("records"),
        })
    con.close()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rows, default=str, indent=2))
    print(json.dumps(rows, default=str, indent=2)[:20000])

if __name__ == "__main__":
    main()
