import pandas as pd
from research.baseline_tournament import add_features

def test_features_build():
    x=pd.DataFrame({
        "timestamp":pd.date_range("2026-01-01 09:15",periods=4,freq="min"),
        "open":[100,101,102,101],"high":[101,102,103,102],
        "low":[99,100,101,100],"close":[100.5,101.5,102.5,101.5],
        "volume":[100,200,150,250]
    })
    y=add_features(x)
    assert y["vwap"].notna().all()
    assert y["ema8"].notna().all()
    assert y["ema24"].notna().all()
