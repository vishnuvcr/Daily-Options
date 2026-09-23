from research.phase3h_option_leadlag_clean import *
import pandas as pd

def _raw_sql_fixed(root):
    g=(root/"**"/"*.parquet").as_posix()
    return f"""SELECT datetime,CAST(date AS DATE) trade_date,expiry_type,option_type,CAST(strike_price AS DOUBLE) strike_price,CAST(close AS DOUBLE) px FROM read_parquet('{g}',union_by_name=true) WHERE close>0 AND STRFTIME(datetime+INTERVAL '5 hours 30 minutes','%H:%M:%S') BETWEEN '09:20:00' AND '14:45:00'"""

def main():
    import argparse,json,duckdb,numpy as np
    from pathlib import Path
    ap=argparse.ArgumentParser();ap.add_argument("--data",type=Path,required=True);ap.add_argument("--out",type=Path,default=Path("reports/phase3h"));a=ap.parse_args()
    con=duckdb.connect();f=con.execute(lead_sql(a.data)).df();raw=con.execute(_raw_sql_fixed(a.data)).df();con.close()
    f["datetime"]=pd.to_datetime(f["datetime"]);raw=raw.rename(columns={"px":"close"});raw["datetime"]=pd.to_datetime(raw["datetime"])
    sig=signals(f);ent=make_entries(sig,raw);p=paths(ent,raw);a.out.mkdir(parents=True,exist_ok=True);p.to_csv(a.out/"paths.csv",index=False)
    result={"features":len(f),"signals":len(sig),"entries":len(ent),"paths":len(p),"variants":len(GRID)}
    for s in (.20,.40):
        t=add_cost(p,s);r=a.out/f"s{str(s).replace('.','_')}";r.mkdir(exist_ok=True);b,pre=summarize(t,int(f.trade_date.nunique()));b.to_csv(r/"leaderboard.csv",index=False);wf,wfs=walk_forward(t);wf.to_csv(r/"walk_forward.csv",index=False);result[str(s)]={"preliminary":pre,"walk_forward":wfs}
    (a.out/"summary.json").write_text(json.dumps(result,indent=2,default=str));print(json.dumps(result,indent=2,default=str))

if __name__=="__main__":main()
