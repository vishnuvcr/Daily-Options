#!/usr/bin/env python3
from pathlib import Path
import json
import duckdb, pandas as pd

def main():
    root=Path("data/cache/phase31_trademarkk")
    features=Path("reports/phase31_7/gate/features.csv")
    out=Path("reports/phase31_7/gate/execution_probe.csv")
    f=pd.read_csv(features,parse_dates=["entry_ts","exit_ts"])
    if f.empty:
        pd.DataFrame().to_csv(out,index=False)
        return
    sample=f.sort_values(["day","bucket"]).head(5)
    con=duckdb.connect()
    con.execute("SET TimeZone='Asia/Kolkata'")
    rows=[]
    for r in sample.itertuples(index=False):
        path=root/"options"/"NIFTY"/f"{pd.Timestamp(r.expiry).date()}.parquet"
        p=str(path).replace("'","''")
        q=f"""
        SELECT
          CAST(timestamp AS TIMESTAMP) ts,
          CAST(CAST(timestamp AS TIMESTAMP) AS DATE) norm_date,
          strftime(CAST(timestamp AS TIMESTAMP),'%H:%M:%S') local_time,
          CAST(trading_day AS DATE) trading_day,
          CAST(strike AS DOUBLE) strike,
          UPPER(CAST(option_type AS VARCHAR)) option_type,
          CAST(open AS DOUBLE) open_px,
          CAST(close AS DOUBLE) close_px
        FROM read_parquet('{p}')
        WHERE CAST(CAST(timestamp AS TIMESTAMP) AS DATE)=DATE '{pd.Timestamp(r.day).date()}'
          AND CAST(strike AS DOUBLE) IN ({float(r.atm)},{float(r.atm)+200.0},{float(r.atm)-200.0})
          AND UPPER(CAST(option_type AS VARCHAR)) IN ('CE','PE')
          AND CAST(CAST(timestamp AS TIMESTAMP) AS TIME) BETWEEN TIME '09:20:00' AND TIME '15:15:00'
          AND (strftime(CAST(timestamp AS TIMESTAMP),'%H:%M:%S') IN ('09:25:00','09:30:00','09:31:00','15:10:00')
               OR strftime(CAST(timestamp AS TIMESTAMP),'%H:%M:%S') LIKE '09:3%')
        ORDER BY ts,strike,option_type
        """
        z=con.execute(q).df()
        if not z.empty:
            z["feature_day"]=str(pd.Timestamp(r.day).date())
            z["bucket"]=int(r.bucket)
            z["expiry"]=str(pd.Timestamp(r.expiry).date())
            z["atm"]=int(r.atm)
            rows.append(z)
    con.close()
    pd.concat(rows,ignore_index=True).to_csv(out,index=False) if rows else pd.DataFrame().to_csv(out,index=False)
    print(json.dumps({"sample_rows":int(sum(len(x) for x in rows)),"sample_days":int(len(sample))}))

if __name__=="__main__":
    main()
