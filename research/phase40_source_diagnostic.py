from pathlib import Path
import json
import duckdb
import pandas as pd

ROOT=Path("data/cache/phase40_trademarkk")
OUT=Path("reports/phase40/diagnostics/representative_source_diagnostic.json")

def main():
    con=duckdb.connect()
    con.execute("SET TimeZone='Asia/Kolkata'")
    idx=con.execute(f"""
        SELECT CAST(timestamp AS DATE) AS trade_date, CAST(timestamp AS TIMESTAMP) AS ts,
               CAST(close AS DOUBLE) AS close_px, CAST(open AS DOUBLE) AS open_px
        FROM read_parquet('{ROOT/"index"/"NIFTY.parquet"}', union_by_name=true)
        WHERE CAST(timestamp AS DATE) BETWEEN DATE '2021-07-01' AND DATE '2021-07-15'
          AND strftime(CAST(timestamp AS TIMESTAMP),'%H:%M:%S') IN ('09:15:00','15:10:00')
        ORDER BY trade_date, ts
    """).df()
    exps=[]
    for p in sorted((ROOT/"options"/"NIFTY").glob("*.parquet")):
        try: exps.append(pd.Timestamp(p.stem).date())
        except: pass
    result=[]
    for d,g in idx.groupby("trade_date"):
        d = pd.Timestamp(d).date()
        future=[e for e in exps if e>d]
        if not future: continue
        expiry=future[0]
        prior_close=float(g.loc[g["ts"].dt.strftime("%H:%M:%S")=="15:10:00","close_px"].iloc[0])
        atm=(int(prior_close/50+0.5))*50
        p=ROOT/"options"/"NIFTY"/f"{expiry}.parquet"
        ps=str(p).replace("'","''")
        z=con.execute(f"""
            SELECT CAST(timestamp AS TIMESTAMP) AS ts,
                   CAST(timestamp AS DATE) AS ts_date,
                   UPPER(CAST(option_type AS VARCHAR)) AS option_type,
                   CAST(strike AS DOUBLE) AS strike,
                   CAST(close AS DOUBLE) AS close_px
            FROM read_parquet('{ps}', union_by_name=true)
            WHERE CAST(timestamp AS DATE)=DATE '{d}'
              AND strftime(CAST(timestamp AS TIMESTAMP),'%H:%M:%S') <= '15:10:00'
              AND CAST(strike AS DOUBLE) IN ({atm-50},{atm},{atm+50})
              AND UPPER(CAST(option_type AS VARCHAR)) IN ('CE','PE')
              AND close>0
            ORDER BY ts DESC, strike, option_type
            LIMIT 40
        """).df()
        result.append({"trade_date":str(d),"prior_close":prior_close,"atm":atm,"expiry":str(expiry),"rows":z.to_dict("records")})
    con.close()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,default=str,indent=2))
    print(json.dumps(result,default=str,indent=2)[:16000])

if __name__=="__main__":
    main()
