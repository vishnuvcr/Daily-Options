import json
import os
from pathlib import Path

if os.environ.get("GITHUB_ACTIONS") == "true":
    try:
        from research.phase21_regime_switch_gamma_vega_v1 import load_spot, regime_table, load_phase21_quotes
        root=Path("data/cache/phase19_trademarkk")
        groot=Path("data/cache/phase21_global")
        if (root/"index"/"NIFTY.parquet").exists():
            spot=load_spot(root)
            reg=regime_table(root,groot)
            quotes=load_phase21_quotes(root,spot)
            d={
                "spot_rows":len(spot),
                "spot_days":int(spot.trade_date.nunique()) if len(spot) else 0,
                "spot_date_type":str(type(spot.trade_date.iloc[0])) if len(spot) else None,
                "reg_rows":len(reg),
                "reg_date_type":str(type(reg.trade_date.iloc[0])) if len(reg) else None,
                "expansion_days":int(reg.expansion.sum()) if len(reg) else 0,
                "quote_rows":len(quotes),
                "quote_days":int(quotes.trade_date.nunique()) if len(quotes) else 0,
                "quote_expiries":int(quotes.expiry.nunique()) if len(quotes) else 0,
                "quote_date_type":str(type(quotes.trade_date.iloc[0])) if len(quotes) else None,
                "quote_expiry_type":str(type(quotes.expiry.iloc[0])) if len(quotes) else None,
            }
            print("P21_SITE_DIAG="+json.dumps(d,default=str))
    except Exception as exc:
        print("P21_SITE_DIAG_ERROR="+repr(exc))
