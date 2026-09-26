import datetime as dt
import pandas as pd
import numpy as np

from research.phase31_8_global_overnight_transmission import (
    FEATURES, THRESHOLDS, HORIZONS, NULL_SEEDS,
    build_signals, data_gate
)

def test_frozen_grid_is_12_cells():
    assert len(FEATURES) * len(THRESHOLDS) * len(HORIZONS) == 12
    assert NULL_SEEDS == (101, 202, 303, 404, 505)

def test_null_control_shuffles_full_feature_series_before_thresholding():
    panel=pd.DataFrame({
        "date":pd.date_range("2026-01-05",periods=6,freq="D"),
        "open_px":[25000]*6,
        "close_px":[25010]*6,
        "US_LEAD":[0.9,-0.8,0.1,0.2,0.6,-0.7],
        "ASIA_LEAD":[0.9,-0.8,0.1,0.2,0.6,-0.7],
        "GLOBAL_LEAD":[0.9,-0.8,0.1,0.2,0.6,-0.7],
        "all_global_available":[True]*6,
        "all_prior":[True]*6,
    })
    true=build_signals(panel,null_seed=None)
    null=build_signals(panel,null_seed=101)
    assert len(true)>0 and len(null)>0
    assert not true["date"].equals(null["date"])

def test_gate_fails_below_95_percent_coverage():
    panel=pd.DataFrame({
        "all_global_available":[True]*94+[False]*6,
        "all_prior":[True]*100
    })
    g=data_gate(panel,__import__("pathlib").Path("."))
    assert g["status"]=="FAIL"
    assert g["complete_global_feature_coverage"]==0.94

def test_gate_requires_prior_date_barrier():
    panel=pd.DataFrame({
        "all_global_available":[True,True,True],
        "all_prior":[True,False,True]
    })
    g=data_gate(panel,__import__("pathlib").Path("."))
    assert g["status"]=="FAIL"
