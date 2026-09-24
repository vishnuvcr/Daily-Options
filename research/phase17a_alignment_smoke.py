from __future__ import annotations
import json
import sys
from pathlib import Path
import pandas as pd

from research.phase17_nifty_exact_expiry_premium_skew import (
    load_spot, load_option_quotes, build_setups, filter_setups, variant_grid
)

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
    }
    (out/"phase17a_alignment_smoke.json").write_text(json.dumps(result,indent=2,default=str))
    print(json.dumps(result,indent=2,default=str))

if __name__=="__main__":
    main(Path(sys.argv[1]),Path(sys.argv[2]))
