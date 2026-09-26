import datetime as dt
from pathlib import Path
import numpy as np
import pandas as pd

from research.phase31_9_vix_rv_gap_opening import (
    REGIMES, DIRECTIONS, HORIZONS, NULL_SEEDS,
    session_panel, data_gate, build_signals, attach_expiry
)

def toy_idx():
    dates=pd.date_range("2026-01-05",periods=26,freq="D")
    rows=[]
    for d in dates:
        rows.append({"ts":d+pd.Timedelta(hours=9,minutes=30),"date":d.normalize(),"time":"09:30:00","open_px":25000.0,"close_px":25000.0})
        rows.append({"ts":d+pd.Timedelta(hours=15,minutes=30),"date":d.normalize(),"time":"15:30:00","open_px":25000.0,"close_px":25000.0+d.day})
    return pd.DataFrame(rows)

def test_frozen_grid_and_null_seeds():
    assert len(REGIMES)*len(DIRECTIONS)*len(HORIZONS)==12
    assert NULL_SEEDS==(101,202,303,404,505)

def test_session_panel_uses_strict_prior_vix_and_rv20():
    idx=toy_idx()
    vix=pd.DataFrame({
        "date":pd.date_range("2026-01-01",periods=26,freq="D"),
        "open":[12.0]*26,"high":[13.0]*26,"low":[11.0]*26,"close":[12.0+i*0.01 for i in range(26)]
    })
    p=session_panel(idx,vix)
    assert {"vix_feature_date","rv_feature_date","prev_close","gap_ret","ratio","regime"}.issubset(p.columns)
    ready=p[p.all_prior & p.ratio.notna()]
    assert not ready.empty
    assert (ready.vix_feature_date < ready.date).all()
    assert (ready.rv_feature_date < ready.date).all()
    assert (ready.prev_close.notna()).all()

def test_null_permutation_is_on_feature_eligible_panel():
    idx=toy_idx()
    vix=pd.DataFrame({"date":pd.date_range("2026-01-01",periods=26,freq="D"),"open":12.0,"high":13.0,"low":11.0,"close":np.linspace(12,14,26)})
    p=session_panel(idx,vix)
    t=build_signals(p,null_seed=None)
    n=build_signals(p,null_seed=101)
    assert len(t)>0 and len(n)>0
    assert set(zip(t["date"],t["regime"])) != set(zip(n["date"],n["regime"]))

def test_gate_rejects_prior_barrier_violation():
    panel=pd.DataFrame({
        "date":pd.to_datetime(["2026-01-05","2026-01-06","2026-01-08"]),
        "all_prior":[True,False,True],
        "ratio":[1.0,1.0,1.0],
        "gap_ret":[0.01,-0.01,0.02],
        "vix_feature_date":pd.to_datetime(["2026-01-04","2026-01-06","2026-01-07"]),
        "rv_feature_date":pd.to_datetime(["2026-01-04","2026-01-04","2026-01-07"]),
    })
    g=data_gate(panel,Path("."))
    assert g["status"]=="FAIL"
    assert g["prior_barrier_violations"]>0

def test_attach_expiry_normalizes_timestamp_date():
    panel=pd.DataFrame({"date":pd.to_datetime(["2026-01-05 00:00:00","2026-01-06 00:00:00"]),"open_px":[25000.0,25020.0]})
    expiry={dt.date(2026,1,6):"x",dt.date(2026,1,8):"y"}
    out=attach_expiry(panel,expiry)
    assert out["expiry"].tolist()==[dt.date(2026,1,6),dt.date(2026,1,6)]

def test_price_and_signal_engine_contracts_are_explicit():
    src=Path("research/phase31_9_vix_rv_gap_opening.py").read_text(encoding="utf-8")
    assert "09:31:00" in src
    assert "10:30:00" in src and "15:10:00" in src
    assert "allow_exact_matches=False" in src
    assert "lot_size" in src and "charge" in src
