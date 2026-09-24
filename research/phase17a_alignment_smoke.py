from __future__ import annotations
import json
import sys
from pathlib import Path
import pandas as pd

from research.phase17_nifty_exact_expiry_premium_skew import (
    load_spot, load_option_quotes, build_setups, filter_setups, variant_grid
)



def first_candidate_probe(spot, quotes):
    out=[]
    for _,sm in spot.head(8).iterrows():
        d=sm.trade_date
        ts=sm.ts
        q=quotes[(quotes.trade_date==d)&(quotes.ts.isin([ts,ts+pd.Timedelta(minutes=1)]))]
        sig=q[q.ts==ts]
        ent=q[q.ts==ts+pd.Timedelta(minutes=1)]
        rec={
            "trade_date":str(d),
            "ts":str(ts),
            "spot":float(sm.close),
            "signal_rows":int(len(sig)),
            "entry_rows":int(len(ent)),
            "signal_strikes":int(sig.strike.nunique()) if not sig.empty else 0,
            "entry_strikes":int(ent.strike.nunique()) if not ent.empty else 0,
            "signal_types":sorted(sig.option_type.unique().tolist()) if not sig.empty else [],
        }
        if not sig.empty and not ent.empty:
            strikes=np.sort(sig.strike.dropna().unique())
            atm_i=int(np.argmin(np.abs(strikes-float(sm.close))))
            rec["atm_strike"]=float(strikes[atm_i])
            rec["atm_distance"]=float(abs(strikes[atm_i]-float(sm.close)))
            checks=[]
            for side in ("PUT","CALL"):
                short_i=atm_i-2 if side=="PUT" else atm_i+2
                for width in (1,2):
                    wing_i=short_i-width if side=="PUT" else short_i+width
                    if short_i<0 or wing_i<0 or short_i>=len(strikes) or wing_i>=len(strikes):
                        continue
                    code="PE" if side=="PUT" else "CE"
                    ss=float(strikes[short_i]); ww=float(strikes[wing_i])
                    sq=ent[(ent.option_type==code)&(ent.strike==ss)].head(1)
                    wq=ent[(ent.option_type==code)&(ent.strike==ww)].head(1)
                    checks.append({
                        "side":side,"width":width,
                        "short_strike":ss,"wing_strike":ww,
                        "short_open":float(sq.iloc[0].open_px) if not sq.empty else None,
                        "wing_open":float(wq.iloc[0].open_px) if not wq.empty else None,
                        "credit":float(sq.iloc[0].open_px-wq.iloc[0].open_px) if not sq.empty and not wq.empty else None
                    })
            rec["checks"]=checks
        out.append(rec)
    return out

def main(root: Path, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    spot=load_spot(root)
    quotes=load_option_quotes(root, spot)
    setups=build_setups(spot, quotes)
    variants=variant_grid()
    filtered=filter_setups(setups, variants)

    result={
        "spot_rows": int(len(spot)),
        "quote_rows": int(len(quotes)),
        "quote_trade_days": int(quotes.trade_date.nunique()) if not quotes.empty else 0,
        "quote_signal_timestamps": int(quotes.ts.nunique()) if not quotes.empty else 0,
        "option_types": sorted(quotes.option_type.dropna().unique().tolist()) if not quotes.empty else [],
        "setup_rows": int(len(setups)),
        "setup_days": int(setups.trade_date.nunique()) if not setups.empty else 0,
        "setup_sides": sorted(setups.side.unique().tolist()) if not setups.empty else [],
        "credit_median": float(setups.entry_credit.median()) if not setups.empty else None,
        "filtered_rows": int(len(filtered)),
        "filtered_variants": int(filtered.variant_id.nunique()) if not filtered.empty else 0,
        "filtered_sides": sorted(filtered.side.unique().tolist()) if not filtered.empty else [],
        "sample_setups": setups.head(20).to_dict("records"),
        "sample_filtered": filtered.head(20).to_dict("records"),
        "first_candidate_probe": first_candidate_probe(spot, quotes),
    }
    (out/"phase17a_alignment_smoke.json").write_text(json.dumps(result,indent=2,default=str))
    print(json.dumps(result,indent=2,default=str))

if __name__=="__main__":
    main(Path(sys.argv[1]),Path(sys.argv[2]))
