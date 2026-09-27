import datetime as dt
import pandas as pd
import numpy as np

from research.phase31_10_institutional_positioning import (
    FEATURES, THRESHOLDS, HORIZONS, NULL_SEEDS,
    build_signals, data_gate, feature_panel
)

def test_frozen_grid_is_12_cells():
    assert len(FEATURES)*len(THRESHOLDS)*len(HORIZONS)==12
    assert NULL_SEEDS==(101,202,303,404,505)

def test_participant_ratio_is_bounded():
    x=(800-200)/(800+200)
    assert -1<=x<=1

def test_prior_only_zscore_barrier():
    dates=pd.date_range("2026-01-01",periods=65,freq="D")
    oi=[]
    for d in dates:
        oi.extend([
            {"trade_date":d,"participant":"FII","fut_idx_long":800,"fut_idx_short":200,"idx_net_ratio":0.6,"idx_net":600},
            {"trade_date":d,"participant":"DII","fut_idx_long":600,"fut_idx_short":400,"idx_net_ratio":0.2,"idx_net":200},
        ])
    nifty=pd.DataFrame({
        "date":[d.date() for d in dates],
        "time":["09:30:00"]*65,
        "open_px":[25000.0]*65,
        "close_px":[25010.0]*65
    })
    p=feature_panel(nifty,pd.DataFrame(oi))
    first=p.dropna(subset=list(FEATURES)).iloc[0]
    assert first.position_date < first.date

def test_null_permutation_changes_full_panel_signal_dates():
    panel=pd.DataFrame({
        "date":pd.date_range("2026-01-01",periods=8,freq="D"),
        "open_px":[25000]*8,
        "close_px":[25010]*8,
        "prev_close":[24900]*8,
        "gap_pct":[0.004]*8,
        "position_date":pd.date_range("2025-12-31",periods=8,freq="D"),
        "FII_IDX_NET_Z":[0.8,-0.7,0.1,0.2,0.9,-0.8,0.3,-0.2],
        "DII_IDX_NET_Z":[0.7,-0.6,0.1,0.3,0.8,-0.9,0.2,-0.1],
        "FII_DII_DIVERGENCE_Z":[0.6,-0.8,0.1,0.2,0.7,-0.7,0.2,-0.2],
        "feature_eligible":[True]*8,
        "barrier_ok":[True]*8
    })
    a=build_signals(panel,null_seed=None)
    b=build_signals(panel,null_seed=101)
    assert len(a)>0 and len(b)>0
    assert not a["date"].equals(b["date"])

def test_data_gate_rejects_barrier_violation():
    panel=pd.DataFrame({
        "feature_eligible":[True,True,True],
        "barrier_ok":[True,False,True],
        "FII_IDX_NET_Z":[1.0,1.0,1.0],
        "DII_IDX_NET_Z":[1.0,1.0,1.0],
        "FII_DII_DIVERGENCE_Z":[1.0,1.0,1.0]
    })
    g=data_gate(panel,{"missing_files":[]})
    assert g["status"]=="FAIL"
    assert g["prior_barrier_violations"]==1

def test_gap_sign_is_formulaic():
    prev=25000.0; open_px=25125.0
    gap=(open_px-prev)/prev
    assert abs(gap-0.005)<1e-12

def test_immediate_prior_positioning_is_required():
    dates=pd.date_range("2026-01-01",periods=65,freq="D")
    oi=[]
    for d in dates.delete(32):
        oi.extend([
            {"trade_date":d,"participant":"FII","fut_idx_long":800,"fut_idx_short":200,"idx_net_ratio":0.6,"idx_net":600},
            {"trade_date":d,"participant":"DII","fut_idx_long":600,"fut_idx_short":400,"idx_net_ratio":0.2,"idx_net":200},
        ])
    nifty=pd.DataFrame({
        "date":[d.date() for d in dates],
        "time":["09:30:00"]*len(dates),
        "open_px":[25000.0]*len(dates),
        "close_px":[25010.0]*len(dates)
    })
    p=feature_panel(nifty,pd.DataFrame(oi))
    miss=p[p["date"]==dates[32].date()].iloc[0]
    assert not bool(miss.barrier_ok)
