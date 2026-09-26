import datetime as dt
import pandas as pd
import numpy as np

from research.phase31_8_global_overnight_transmission import (
    FEATURES, THRESHOLDS, HORIZONS, NULL_SEEDS,
    build_signals, data_gate, build_panel
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


def test_build_panel_uses_datetime_merge_keys_and_strict_prior_dates():
    dates = pd.date_range("2026-01-05", periods=4, freq="D")
    nifty = pd.DataFrame({
        "date": dates,
        "time": ["09:30:00"] * 4,
        "open_px": [25000, 25010, 25020, 25030],
        "close_px": [25005, 25015, 25025, 25035],
    })
    global_data = {
        "GSPC": pd.DataFrame({"date": dates - pd.Timedelta(days=1), "z": [1.0, 1.1, 1.2, 1.3], "ret": [0, 0, 0, 0]}),
        "IXIC": pd.DataFrame({"date": dates - pd.Timedelta(days=1), "z": [1.0, 1.1, 1.2, 1.3], "ret": [0, 0, 0, 0]}),
        "N225": pd.DataFrame({"date": dates - pd.Timedelta(days=1), "z": [1.0, 1.1, 1.2, 1.3], "ret": [0, 0, 0, 0]}),
        "HSI": pd.DataFrame({"date": dates - pd.Timedelta(days=1), "z": [1.0, 1.1, 1.2, 1.3], "ret": [0, 0, 0, 0]}),
        "GDAXI": pd.DataFrame({"date": dates - pd.Timedelta(days=1), "z": [1.0, 1.1, 1.2, 1.3], "ret": [0, 0, 0, 0]}),
        "KS11": pd.DataFrame({"date": dates - pd.Timedelta(days=1), "z": [1.0, 1.1, 1.2, 1.3], "ret": [0, 0, 0, 0]}),
    }
    panel = build_panel(global_data, nifty)
    assert pd.api.types.is_datetime64_any_dtype(panel["date"])
    assert panel["all_global_available"].all()
    assert panel["all_prior"].all()
    assert (panel["prior_date_GSPC"] < panel["date"]).all()


def test_main_passes_raw_nifty_index_to_build_panel():
    from pathlib import Path
    src=Path("research/phase31_8_global_overnight_transmission.py").read_text(encoding="utf-8")
    assert "panel=build_panel(g,idx)" in src
    assert 'panel=build_panel(g,sessions)' not in src
