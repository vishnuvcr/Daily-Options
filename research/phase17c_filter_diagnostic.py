from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
from research.phase17_nifty_exact_expiry_premium_skew import (
    load_spot, load_option_quotes, build_setups, filter_setups, variant_grid
)

def run(root: Path, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    spot=load_spot(root)
    variants=variant_grid()
    quotes=load_option_quotes(root, spot[["trade_date","ts","close"]].drop_duplicates())
    setups=build_setups(spot, quotes)

    counts=[]
    if not setups.empty:
        for v in variants:
            m=(
                setups.side.eq(v["side"])
                & setups.width.eq(v["width"])
                & setups.ts.dt.strftime("%H:%M:%S").eq(v["entry_time"])
            )
            base=int(m.sum())
            stages=[
                ("skew", m & (setups.skew.ge(v["skew"]) if v["side"]=="PUT" else setups.skew.le(-v["skew"]))),
                ("vol", m & (setups.skew.ge(v["skew"]) if v["side"]=="PUT" else setups.skew.le(-v["skew"])) &
                 (setups.vol_imb.ge(0) if v["side"]=="PUT" else setups.vol_imb.le(0))),
                ("oi", m & (setups.skew.ge(v["skew"]) if v["side"]=="PUT" else setups.skew.le(-v["skew"])) &
                 (setups.vol_imb.ge(0) if v["side"]=="PUT" else setups.vol_imb.le(0)) &
                 (setups.oi_imb.ge(0) if v["side"]=="PUT" else setups.oi_imb.le(0))),
                ("direction", m & (setups.skew.ge(v["skew"]) if v["side"]=="PUT" else setups.skew.le(-v["skew"])) &
                 (setups.vol_imb.ge(0) if v["side"]=="PUT" else setups.vol_imb.le(0)) &
                 (setups.oi_imb.ge(0) if v["side"]=="PUT" else setups.oi_imb.le(0)) &
                 (setups.spot_ret10.ge(0) if v["side"]=="PUT" else setups.spot_ret10.le(0))),
                ("rv", m & (setups.skew.ge(v["skew"]) if v["side"]=="PUT" else setups.skew.le(-v["skew"])) &
                 (setups.vol_imb.ge(0) if v["side"]=="PUT" else setups.vol_imb.le(0)) &
                 (setups.oi_imb.ge(0) if v["side"]=="PUT" else setups.oi_imb.le(0)) &
                 (setups.spot_ret10.ge(0) if v["side"]=="PUT" else setups.spot_ret10.le(0)) &
                 setups.rv_ratio.ge(v["rv"])),
                ("jump", m & (setups.skew.ge(v["skew"]) if v["side"]=="PUT" else setups.skew.le(-v["skew"])) &
                 (setups.vol_imb.ge(0) if v["side"]=="PUT" else setups.vol_imb.le(0)) &
                 (setups.oi_imb.ge(0) if v["side"]=="PUT" else setups.oi_imb.le(0)) &
                 (setups.spot_ret10.ge(0) if v["side"]=="PUT" else setups.spot_ret10.le(0)) &
                 setups.rv_ratio.ge(v["rv"]) &
                 setups.spot_ret10.abs().le(v["jump"])),
            ]
            row={"variant_id":f'{v["entry_time"]}|sk{v["skew"]}|j{v["jump"]}|rv{v["rv"]}|w{v["width"]}|h{v["hold"]}|stop{v["stop"]}|{v["side"]}',
                 "base":base}
            for name,mask in stages:
                row[name]=int(mask.sum())
            counts.append(row)
    cdf=pd.DataFrame(counts)
    cdf.to_csv(out/"phase17c_filter_diagnostics.csv",index=False)

    delay_stats={}
    if not setups.empty and "entry_delay_min" in setups:
        delay_stats={
            "entry_delay_n":int(setups.entry_delay_min.notna().sum()),
            "entry_delay_mean":float(setups.entry_delay_min.mean()),
            "entry_delay_p50":float(setups.entry_delay_min.quantile(.5)),
            "entry_delay_p90":float(setups.entry_delay_min.quantile(.9)),
            "entry_delay_max":float(setups.entry_delay_min.max()),
        }

    summary={
        "spot_rows":int(len(spot)),
        "quote_rows":int(len(quotes)),
        "setup_rows":int(len(setups)),
        "filtered_rows":int(len(filter_setups(setups,variants))),
        "variants":int(len(variants)),
        "positive_credit_setups":int(len(setups)),
        "best_variant_after_all_filters":cdf.sort_values("jump",ascending=False).head(10).to_dict("records") if not cdf.empty else [],
        "max_after_skew":int(cdf["skew"].max()) if not cdf.empty else 0,
        "max_after_vol":int(cdf["vol"].max()) if not cdf.empty else 0,
        "max_after_oi":int(cdf["oi"].max()) if not cdf.empty else 0,
        "max_after_direction":int(cdf["direction"].max()) if not cdf.empty else 0,
        "max_after_rv":int(cdf["rv"].max()) if not cdf.empty else 0,
        "max_after_jump":int(cdf["jump"].max()) if not cdf.empty else 0,
        **delay_stats,
    }
    (out/"phase17c_filter_diagnostic.json").write_text(json.dumps(summary,indent=2,default=str))
    print(json.dumps(summary,indent=2,default=str))
    return summary

if __name__=="__main__":
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--data",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    run(a.data,a.out)
