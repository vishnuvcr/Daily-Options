from pathlib import Path
import json
import duckdb

ROOT=Path("data/cache/phase39_trademarkk")
OUT=Path("reports/phase39/diagnostics/execution_quote_diagnostic.json")

def main():
    con=duckdb.connect()
    con.execute("SET TimeZone='Asia/Kolkata'")
    expiry="2021-09-30"
    trade_date="2021-09-29"
    strikes=(17600,17800)
    p=ROOT/"options"/"NIFTY"/f"{expiry}.parquet"
    ps=str(p).replace("'","''")
    q=f"""
      SELECT
        CAST(timestamp AS TIMESTAMP) AS ts,
        CAST(timestamp AS DATE) AS ts_date,
        CAST(trading_day AS DATE) AS trading_day,
        UPPER(CAST(option_type AS VARCHAR)) AS option_type,
        CAST(strike AS DOUBLE) AS strike,
        CAST(open AS DOUBLE) AS open_px,
        CAST(close AS DOUBLE) AS close_px
      FROM read_parquet('{ps}', union_by_name=true)
      WHERE CAST(timestamp AS DATE)=DATE '{trade_date}'
        AND strftime(CAST(timestamp AS TIMESTAMP),'%H:%M:%S') IN ('09:31:00','10:30:00','15:10:00')
        AND CAST(strike AS DOUBLE) IN (17600,17800)
        AND UPPER(CAST(option_type AS VARCHAR))='PE'
      ORDER BY ts, strike
    """
    rows=con.execute(q).df().to_dict("records")
    con.close()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(rows,default=str,indent=2))
    print(json.dumps(rows,default=str,indent=2)[:12000])

if __name__=="__main__":
    main()
