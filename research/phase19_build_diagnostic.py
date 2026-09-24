from pathlib import Path
import json
import pandas as pd
from research.phase19_nifty_short_strangle_regime import load_spot, load_exact_quotes, build_setups

def main(root: Path, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    spot = load_spot(root).head(20).copy()
    q = load_exact_quotes(root, spot)
    rows=[]
    for (d,ts), sm in spot.groupby(["trade_date","ts"],sort=False):
        qq=q[(q["trade_date"]==d)&(q["ts"]>=ts)&(q["ts"]<=ts+pd.Timedelta(minutes=3))]
        sig=qq[qq["ts"]==ts]
        strikes=sorted(sig["strike"].dropna().unique().tolist())
        dayq=q[q["trade_date"]==d]
        item={
            "trade_date":str(d),"signal_ts":str(ts),
            "day_quote_rows":int(len(dayq)),
            "day_quote_min_ts":str(dayq["ts"].min()) if not dayq.empty else None,
            "day_quote_max_ts":str(dayq["ts"].max()) if not dayq.empty else None,
            "window_rows":int(len(qq)),"signal_rows":int(len(sig)),
            "strikes":int(len(strikes)),
            "option_types":sorted(sig["option_type"].dropna().astype(str).unique().tolist()),
            "first_ts":str(qq["ts"].min()) if not qq.empty else None,
            "last_ts":str(qq["ts"].max()) if not qq.empty else None,
            "offsets":[]
        }
        if strikes:
            atm=min(range(len(strikes)),key=lambda i:abs(strikes[i]-float(sm.iloc[0]["spot_close"])))
            for so in (1,2,3):
                pi=atm-so; ci=atm+so
                if pi<0 or ci>=len(strikes):
                    item["offsets"].append({"offset":so,"valid":False})
                    continue
                ps=float(strikes[pi]); cs=float(strikes[ci])
                pq=qq[(qq["option_type"]=="PE")&(qq["strike"]==ps)&(qq["ts"]>ts)]
                cq=qq[(qq["option_type"]=="CE")&(qq["strike"]==cs)&(qq["ts"]>ts)]
                common=sorted(set(pq["ts"]).intersection(set(cq["ts"])))
                item["offsets"].append({
                    "offset":so,"valid":True,"put_rows":int(len(pq)),"call_rows":int(len(cq)),
                    "first_common":str(common[0]) if common else None
                })
        rows.append(item)
    setups=build_setups(spot,q)
    result={"signals_sampled":len(spot),"quote_rows":int(len(q)),
            "build_setups_rows":int(len(setups)),"rows":rows}
    (out/"phase19_build_diagnostic.json").write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=="__main__":
    import sys
    main(Path(sys.argv[1]),Path(sys.argv[2]))
