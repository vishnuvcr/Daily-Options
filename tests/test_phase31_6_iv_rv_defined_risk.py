import math
from research.phase31_6_iv_rv_defined_risk import bs_call, implied_vol_straddle, yz_vol, lot_size

def test_black_scholes_round_trip():
    s,k,t=22000.0,22000.0,7/365
    call=bs_call(s,k,t,0.0,0.20)
    target=call-s+k
    iv=implied_vol_straddle(s,k,t,call+target)
    assert iv is not None
    assert abs(iv-0.20)<1e-4

def test_yz_requires_prior_window():
    import pandas as pd
    d=pd.date_range("2026-01-01",periods=19,freq="B")
    g=pd.DataFrame({"open":100.0,"high":101.0,"low":99.0,"close":100.5},index=d)
    assert yz_vol(g) is None

def test_defined_grid_is_finite():
    from research.phase31_6_iv_rv_defined_risk import THRESHOLDS, EXPIRY_BUCKETS, WINGS
    assert len(THRESHOLDS)*2*len(EXPIRY_BUCKETS)==12
    assert WINGS==(200,)


def test_historical_lot_sizes_are_frozen():
    assert lot_size("2024-04-25") == 50
    assert lot_size("2024-04-26") == 25
    assert lot_size("2024-11-21") == 75
    assert lot_size("2026-01-06") == 65
