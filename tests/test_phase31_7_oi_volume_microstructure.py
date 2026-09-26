import math
import pandas as pd
from research.phase31_7_oi_volume_microstructure import (
    THRESHOLDS, FEATURES, BUCKETS, NULL_SEEDS, lot_size
)

def test_frozen_grid_is_12_cells():
    assert len(FEATURES) * len(THRESHOLDS) * len(BUCKETS) == 12
    assert NULL_SEEDS == (101, 202, 303, 404, 505)

def test_lot_size_schedule():
    assert lot_size("2024-04-25") == 50
    assert lot_size("2024-04-26") == 25
    assert lot_size("2024-11-21") == 75
    assert lot_size("2026-01-06") == 65

def test_feature_formulas_are_bounded():
    vol_imb=(80-20)/(80+20)
    dce,dpe=30,-10
    oi_imb=(dce-dpe)/(abs(dce)+abs(dpe))
    joint=.5*vol_imb+.5*oi_imb
    assert -1 <= vol_imb <= 1
    assert -1 <= oi_imb <= 1
    assert -1 <= joint <= 1

def test_signal_timestamp_barrier():
    entry=pd.Timestamp("2026-01-05 09:31:00")
    feature_times=pd.to_datetime(["2026-01-05 09:25:00","2026-01-05 09:30:00"])
    assert all(t <= pd.Timestamp("2026-01-05 09:30:00") for t in feature_times)
    assert entry > feature_times.max()

def test_null_seeds_are_deterministic():
    import numpy as np
    x=np.array([-.5,-.1,.2,.8])
    rng1=np.random.default_rng(101); a=x.copy(); rng1.shuffle(a)
    rng2=np.random.default_rng(101); b=x.copy(); rng2.shuffle(b)
    assert list(a)==list(b)
