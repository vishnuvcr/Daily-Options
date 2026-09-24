from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
import numpy as np
from research.phase18_nifty_iron_condor_regime import load_spot, load_exact_quotes, variant_grid, START_DATE, END_DATE, SHORT_OFFSETS, WING_WIDTHS

def run(root: Path, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    spot=load_spot(root)
    quotes=load_exact_quotes(root,spot)
    stats={"signals":len(spot),"quote_rows":len(quotes)}
    if spot.empty or quotes.empty:
        (out/"phase18_setup_diagnostic.json").write_text(json.dumps(stats,indent=2))
        return stats

    eligible_days=0
    all_four=0
    common_ts=0
    positive_credit=0
    per_offset={}
    sample=[]

    for (d,ts),sm in spot.groupby(["trade_date","ts"],sort=False):
        q=quotes[(quotes.trade_date==d)&(quotes.ts>=ts)&(quotes.ts<=ts+pd.Timedelta(minutes=3))]
        sig=q[q.ts==ts]
        if sig.empty: continue
        strikes=np.sort(sig.strike.dropna().unique())
        if len(strikes)<9: continue
        eligible_days += 1
        atm=int(np.argmin(np.abs(strikes-float(sm.iloc[0].spot_close if "spot_close" in sm else sm.iloc[0].close))))
        for so in SHORT_OFFSETS:
            pi=atm-so; ci=atm+so
            if pi<0 or ci>=len(strikes): continue
            for ww in WING_WIDTHS:
                pwi=pi-ww; cwi=ci+ww
                if pwi<0 or cwi>=len(strikes): continue
                put_short=float(strikes[pi]); call_short=float(strikes[ci])
                put_wing=float(strikes[pwi]); call_wing=float(strikes[cwi])
                legs=[("PE",put_short),("PE",put_wing),("CE",call_short),("CE",call_wing)]
                leg_sets=[]
                ok=True
                for code,strike in legs:
                    z=q[(q.option_type==code)&(q.strike==strike)&(q.ts>ts)][["ts","open_px"]]
                    if z.empty: ok=False; break
                    leg_sets.append(set(z.ts))
                key=f"so{so}_ww{ww}"
                x=per_offset.setdefault(key,{"attempts":0,"all_legs":0,"common":0,"positive":0})
                x["attempts"]+=1
                if not ok: continue
                all_four += 1; x["all_legs"] += 1
                common=set.intersection(*leg_sets)
                if not common: continue
                common_ts += 1; x["common"] += 1
                entry_ts=min(common)
                vals=[]
                for code,strike in legs:
                    z=q[(q.option_type==code)&(q.strike==strike)&(q.ts==entry_ts)].head(1)
                    vals.append(float(z.iloc[0].open_px))
                credit=vals[0]-vals[1]+vals[2]-vals[3]
                if credit>0:
                    positive_credit += 1; x["positive"] += 1
                    if len(sample)<20:
                        sample.append({"date":str(d),"signal_ts":str(ts),"entry_ts":str(entry_ts),"so":so,"ww":ww,"credit":credit,"legs":vals})
    stats.update({"eligible_signal_rows":eligible_days,"all_four_legs":all_four,"common_timestamp_setups":common_ts,"positive_credit_setups":positive_credit,"per_structure":per_offset,"sample_positive":sample})
    (out/"phase18_setup_diagnostic.json").write_text(json.dumps(stats,indent=2,default=str))
    print(json.dumps(stats,indent=2,default=str))
    return stats

if __name__=="__main__":
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--data",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    run(a.data,a.out)
