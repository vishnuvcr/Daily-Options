import numpy as np
import pandas as pd

from research.phase41_gamma_concentration_opening_gap import (
    CORE_WIDTH, TOTAL_WIDTH, gamma, implied_vol, lot_size, prior_only_z,
    round_strike, bs_price, build_signals, required_legs if False else round_strike
)


def test_iv_roundtrip():
    spot=22500.0; strike=22500.0; t=20/365; sigma=.22
    px=bs_price(spot,strike,t,sigma,True)
    got=implied_vol(px,spot,strike,t,True)
    assert np.isfinite(got)
    assert abs(got-sigma)<1e-6


def test_gamma_positive():
    g=gamma(22500,22500,20/365,.2)
    assert np.isfinite(g) and g>0


def test_half_up_rounding():
    assert round_strike(22525)==22550
    assert round_strike(22524)==22500


def test_prior_only_z_uses_only_previous_valid_observations():
    s=pd.Series([1+0.01*i for i in range(65)])
    _,_,z=prior_only_z(s,60)
    assert pd.isna(z.iloc[59])
    assert pd.notna(z.iloc[60])


def test_lot_schedule():
    assert lot_size(pd.Timestamp("2024-04-25").date())==50
    assert lot_size(pd.Timestamp("2024-04-26").date())==25
    assert lot_size(pd.Timestamp("2024-11-21").date())==75
    assert lot_size(pd.Timestamp("2026-01-06").date())==65


def test_signal_matrix_and_gap_direction():
    dates=pd.date_range("2026-01-01",periods=65,freq="B").date
    panel=pd.DataFrame({
        "trade_date":dates,
        "prior_day":dates,
        "prior_spot":[22500.0]*65,
        "opening_gap":[0.01]*65,
        "gamma_concentration":[0.5]*65,
        "gamma_concentration_z":[np.nan]*60+[1.0,-1.0,1.0,-1.0,0.0],
        "feature_eligible":[False]*60+[True]*5,
        "atm":[22500.0]*65,
        "expiry":[pd.Timestamp("2026-02-03").date()]*65,
    })
    s=build_signals(panel)
    assert set(s.state)=={"HIGH_GAMMA_CONCENTRATION","LOW_GAMMA_CONCENTRATION"}
    assert set(s.mapping)=={"FOLLOW_GAP","FADE_GAP"}
    assert set(s.exit_time)=={"10:30:00","15:10:00"}
    assert len(s)==16
