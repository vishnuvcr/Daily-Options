from __future__ import annotations
import json
from pathlib import Path
import duckdb
import pandas as pd

START="2021-07-01"
END="2026-08-04"

def main(root: str, out_file: str) -> None:
    root=Path(root)
    idx=root/"index"/"NIFTY.parquet"
    option_files=sorted((root/"options"/"NIFTY").glob("*.parquet"))
    if not option_files:
        raise SystemExit("no option files")
    sample_file=next(p for p in option_files if p.stem=="2021-07-08")
    con=duckdb.connect()
    con.execute("SET TimeZone='Asia/Kolkata'")
    schema=con.execute(f"DESCRIBE SELECT * FROM read_parquet('{sample_file}',union_by_name=true)").df().to_dict("records")
    idx_days=con.execute(f"""
        SELECT DISTINCT CAST(trading_day AS DATE) trade_date
        FROM read_parquet('{idx}',union_by_name=true)
        WHERE CAST(trading_day AS DATE) BETWEEN DATE '{START}' AND DATE '{END}'
        ORDER BY trade_date
        LIMIT 20
    """).df()["trade_date"].tolist()
    sample_days=[d for d in idx_days if str(d) <= "2021-07-08"][:5]
    results=[]
    for d in sample_days:
        q=f"""
        SELECT
          CAST(o.trading_day AS DATE) trade_date,
          o.timestamp AS raw_ts,
          CAST(o.timestamp AS TIMESTAMP) AS cast_ts,
          CAST(o.timestamp AS VARCHAR) AS ts_text,
          CAST(o.strike AS DOUBLE) strike,
          UPPER(CAST(o.option_type AS VARCHAR)) option_type,
          CAST(o.open AS DOUBLE) open_px,
          CAST(o.close AS DOUBLE) close_px
        FROM read_parquet('{sample_file}',union_by_name=true) o
        WHERE CAST(o.trading_day AS DATE)=DATE '{d}'
        LIMIT 50000
        """
        df=con.execute(q).df()
        if df.empty:
            results.append({"trade_date":str(d),"rows_returned":0})
            continue
        cast_ts=pd.to_datetime(df["cast_ts"])
        raw_ts=df["raw_ts"]
        hh=cast_ts.dt.strftime("%H:%M:%S")
        counts=hh.value_counts().sort_index()
        target={t:int(counts.get(t,0)) for t in ["09:29:00","09:30:00","09:31:00","09:32:00","15:14:00","15:15:00","15:16:00"]}
        local_window=df[cast_ts.between(pd.Timestamp(f"{d} 09:25:00"),pd.Timestamp(f"{d} 09:40:00"))].head(20).copy()
        close_window=df[cast_ts.between(pd.Timestamp(f"{d} 15:10:00"),pd.Timestamp(f"{d} 15:20:00"))].head(20).copy()
        results.append({
            "trade_date":str(d),
            "rows_returned":int(len(df)),
            "cast_ts_dtype":str(df["cast_ts"].dtype),
            "raw_ts_dtype":str(df["raw_ts"].dtype),
            "first_text_ts":df["ts_text"].head(5).tolist(),
            "last_text_ts":df["ts_text"].tail(5).tolist(),
            "target_clock_counts":target,
            "local_window_sample":local_window[["ts_text","cast_ts","strike","option_type","open_px","close_px"]].astype(str).to_dict("records"),
            "close_window_sample":close_window[["ts_text","cast_ts","strike","option_type","open_px","close_px"]].astype(str).to_dict("records"),
            "nonzero_ohlc_rows":int(((df["open_px"]>0)|(df["close_px"]>0)).sum()),
            "unique_option_types":sorted(df["option_type"].dropna().unique().tolist())[:20],
            "unique_trading_days":sorted(df["trade_date"].astype(str).unique().tolist())
        })
    con.close()
    payload={"sample_file":str(sample_file),"schema":schema,"sample_days":[str(x) for x in sample_days],"results":results}
    Path(out_file).parent.mkdir(parents=True,exist_ok=True)
    Path(out_file).write_text(json.dumps(payload,indent=2,default=str))

if __name__=="__main__":
    main("data/cache/phase24_trademarkk","reports/otm12-phase-a-timestamp-probe/timestamp_probe.json")
