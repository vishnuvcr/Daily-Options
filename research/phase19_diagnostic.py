from pathlib import Path
import json
import pandas as pd
from research.phase19_nifty_short_strangle_regime import load_spot, load_exact_quotes, expiry_files, expiry_for_day

def main(root: Path, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    spot=load_spot(root).head(20).copy()
    q=load_exact_quotes(root, spot)
    rows=[]
    for (d,ts),sm in spot.groupby(["trade_date","ts"],sort=False):
        qq=q[(q["trade_date"]==d)&(q["ts"]>=ts)&(q["ts"]<=ts+pd.Timedelta(minutes=3))]
        sig=qq[qq["ts"]==ts]
        strikes=sorted(sig["strike"].dropna().unique().tolist())
        atm=int(min(range(len(strikes)), key=lambda i: abs(strikes[i]-float(sm.iloc[0]["spot_close"])))) if strikes else None
        rec={"trade_date":str(d),"ts":str(ts),"quote_window_rows":int(len(qq)),
             "signal_rows":int(len(sig)),"signal_strikes":int(len(strikes)),
             "option_types":sorted(sig["option_type"].dropna().unique().tolist()),
             "atm_strike":float(strikes[atm]) if atm is not None else None,
             "offsets":[]}
        if atm is not None:
            for so in (1,2,3):
                pi=atm-so; ci=atm+so
                if pi<0 or ci>=len(strikes):
                    rec["offsets"].append({"offset":so,"valid_strikes":False}); continue
                ps=float(strikes[pi]); cs=float(strikes[ci])
                pq=qq[(qq["option_type"]=="PE")&(qq["strike"]==ps)&(qq["ts"]>ts)]
                cq=qq[(qq["option_type"]=="CE")&(qq["strike"]==cs)&(qq["ts"]>ts)]
                common=sorted(set(pq["ts"]).intersection(set(cq["ts"])))
                rec["offsets"].append({"offset":so,"valid_strikes":True,
                    "put_points":int(len(pq)),"call_points":int(len(cq)),
                    "first_common":str(common[0]) if common else None})
        rows.append(rec)
    summary={"signals_sampled":len(spot),"rows":rows}
    (out/"phase19_diagnostic.json").write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))

if __name__=="__main__":
    import sys
    main(Path(sys.argv[1]),Path(sys.argv[2]))
