import pandas as pd
from research.regime_adaptive_directional import features

def test_feature_engine():
    ts=pd.date_range("2026-01-05 09:15",periods=80,freq="min")
    base=pd.Series(range(80),dtype=float)
    x=pd.DataFrame({
        "timestamp":ts,
        "open":100+base*0.1,
        "high":100.2+base*0.1,
        "low":99.8+base*0.1,
        "close":100+base*0.1,
        "volume":100+base,
    })
    y=features(x)
    assert y["vwap"].notna().any()
    assert y["ema50"].notna().any()
    assert y["rsi"].notna().any()
