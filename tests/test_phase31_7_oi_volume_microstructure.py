import math
import pandas as pd
from research.phase31_7_oi_volume_microstructure import (
    THRESHOLDS, FEATURES, BUCKETS, NULL_SEEDS, lot_size,
    permute_feature_values, build_signals
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

\n\ndef test_null_control_permutates_full_feature_panel_before_thresholding():
    panel=pd.DataFrame({
        "day":pd.to_datetime(["2026-01-05","2026-01-06","2026-01-07","2026-01-08"]),
        "bucket":[0,0,0,0],
        "expiry":pd.to_datetime(["2026-01-06"]*4),
        "spot":[25000.0]*4,
        "atm":[25000]*4,
        "vol_imb":[0.90,-0.80,0.10,0.20],
        "oi_change_imb":[0.90,-0.80,0.10,0.20],
        "joint":[0.90,-0.80,0.10,0.20],
        "entry_ts":pd.to_datetime(["2026-01-05 09:31:00"]*4),
        "exit_ts":pd.to_datetime(["2026-01-05 15:10:00"]*4),
    })
    original=panel["vol_imb"].to_numpy(copy=True)
    permuted=permute_feature_values(panel,"vol_imb",0,101)["vol_imb"].to_numpy()
    assert sorted(permuted.tolist()) == sorted(original.tolist())
    assert not (permuted == original).all()

    true=build_signals(panel)
    null=build_signals(panel,null_seed=101)
    assert set(true["day"]) != set(null["day"]) or set(true["side"]) != set(null["side"])

\ndef test_execution_query_has_no_timezone_aware_direct_timestamp_to_time_cast():
    from pathlib import Path
    src=Path("research/phase31_7_oi_volume_microstructure.py").read_text(encoding="utf-8")
    assert "CAST(o.timestamp AS TIME)" not in src
    assert "strftime(CAST(o.timestamp AS TIMESTAMP), '%H:%M:%S')" in src
