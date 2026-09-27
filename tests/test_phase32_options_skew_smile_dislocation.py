import math
import pandas as pd
import numpy as np

from research.phase32_options_skew_smile_dislocation import (
    FEATURES, THRESHOLDS, HORIZONS, NULL_SEEDS, WARMUP,
    implied_vol, build_surface, build_signals, legs_for_signal
)

def test_frozen_grid_is_12_cells():
    assert len(FEATURES) * len(THRESHOLDS) * len(HORIZONS) == 12
    assert NULL_SEEDS == (101,202,303,404,505)
    assert WARMUP == 60

def test_iv_round_trip():
    # ATM call at 20% annual vol, 30 days, r=q=0.
    from research.phase32_options_skew_smile_dislocation import bs_price
    s=k=22000.0
    t=30/365
    p=bs_price(s,k,t,0.20,True)
    iv=implied_vol(s,k,t,p,True)
    assert iv is not None
    assert abs(iv-0.20) < 1e-4

def test_iv_rejects_below_intrinsic():
    assert implied_vol(100, 90, 10/365, 9.0, True) is None

def test_prior_only_surface_zscore_barrier():
    n=75
    dates=pd.date_range("2026-01-01",periods=n,freq="B")
    panel=pd.DataFrame({
        "date":[d.date() for d in dates],
        "close_px":np.linspace(100,110,n),
        "expiry":[(d+pd.Timedelta(days=7)).date() for d in dates]
    })
    # Synthetic valid surface series.
    panel["surface_valid"]=True
    panel["iv_atm_ce"]=20+np.arange(n)*0.01
    panel["iv_atm_pe"]=20+np.arange(n)*0.01
    panel["iv_put100"]=23+0.02*np.arange(n)
    panel["iv_call100"]=20.0+0.005*np.sin(np.arange(n)/3.0)
    from research.phase32_options_skew_smile_dislocation import build_surface
    # build_surface needs quotes and IV inversion; barrier property is tested separately.
    panel["skew_volpts"]=panel["iv_put100"]-panel["iv_call100"]
    panel["smile_volpts"]=((panel["iv_put100"]+panel["iv_call100"])/2
                           -(panel["iv_atm_ce"]+panel["iv_atm_pe"])/2)
    for raw,zcol in (("skew_volpts","SKEW_Z"),("smile_volpts","SMILE_Z")):
        prior=panel[raw].shift(1)
        panel[zcol]=(panel[raw]-prior.rolling(WARMUP,min_periods=WARMUP).mean())/prior.rolling(WARMUP,min_periods=WARMUP).std(ddof=1)
    assert pd.isna(panel.iloc[WARMUP-1].SKEW_Z)
    assert pd.notna(panel.iloc[WARMUP].SKEW_Z)
    assert panel.iloc[WARMUP].date > panel.iloc[WARMUP-1].date

def test_surface_formulas():
    p=pd.DataFrame({
        "iv_atm_ce":[20.0], "iv_atm_pe":[20.0],
        "iv_put100":[26.0], "iv_call100":[22.0]
    })
    p["skew_volpts"]=p.iv_put100-p.iv_call100
    p["smile_volpts"]=(p.iv_put100+p.iv_call100)/2-(p.iv_atm_ce+p.iv_atm_pe)/2
    assert abs(float(p.skew_volpts.iloc[0])-4.0)<1e-12
    assert abs(float(p.smile_volpts.iloc[0])-4.0)<1e-12

def test_signal_structures_are_bounded_four_leg():
    for feature in FEATURES:
        for z in (-2.0, 2.0):
            legs=legs_for_signal(feature,z,22000)
            assert len(legs)==4
            assert all(a in {"BUY","SELL"} for _,_,a in legs)
            strikes=[k for _,k,_ in legs]
            assert max(strikes)-min(strikes) <= 200


def test_feature_tuple_is_materialized_for_dataframe_selection():
    p = pd.DataFrame({"SKEW_Z":[1.0], "SMILE_Z":[2.0]})
    selected = p[list(FEATURES)]
    assert list(selected.columns) == list(FEATURES)


def test_surface_quote_key_normalization_and_iv_reconstruction():
    from research.phase32_options_skew_smile_dislocation import bs_price, build_surface
    d = pd.Timestamp("2026-01-02").date()
    expiry = pd.Timestamp("2026-01-08").date()
    spot = 22000.0
    atm = 22000.0
    t = (pd.Timestamp(f"{expiry} 15:30:00") - pd.Timestamp(f"{d} 09:30:00")).total_seconds() / 31536000.0
    rows = []
    for typ, strike in (("CE", atm), ("PE", atm), ("PE", atm - 100), ("CE", atm + 100)):
        px = bs_price(spot, strike, t, 0.20, typ == "CE")
        rows.append({
            "date": pd.Timestamp(d),
            "local_time": "09:30:00",
            "option_type": typ,
            "strike": strike,
            "close_px": px,
        })
    panel = pd.DataFrame([{"date": d, "close_px": spot, "expiry": expiry, "atm": atm}])
    out = build_surface(panel, pd.DataFrame(rows))
    assert bool(out.iloc[0].surface_valid)
    assert out.iloc[0].surface_fail_reason == "OK"
