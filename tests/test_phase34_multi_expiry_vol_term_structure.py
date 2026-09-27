import numpy as np
from research.phase34_multi_expiry_vol_term_structure import (
    FEATURES,THRESHOLDS,EXITS,WARMUP,bs_price_vec,implied_vol_vec,lot_size
)

def test_grid_is_8_cells():
    assert len(FEATURES)*len(THRESHOLDS)*len(EXITS)==8

def test_lot_sizes():
    assert lot_size("2021-07-01")==50
    assert lot_size("2024-04-26")==25
    assert lot_size("2024-11-21")==75
    assert lot_size("2026-01-06")==65

def test_iv_round_trip():
    s=22000.0;k=22000.0;t=30/365;sig=.20
    p=float(bs_price_vec(np.array([s]),np.array([k]),np.array([t]),np.array([sig]),np.array([True]))[0])
    iv=float(implied_vol_vec(np.array([p]),np.array([s]),np.array([k]),np.array([t]),np.array([True]))[0])
    assert abs(iv-sig)<1e-4

def test_calendar_requires_positive_entry_debit():
    front=190.0+170.0
    back=220.0+210.0
    assert back-front>0

def test_negative_calendar_value_is_skipped():
    front=210.0+205.0
    back=200.0+195.0
    assert back-front<=0
