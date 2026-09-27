from research.phase35_global_shock_options_structure import FEATURES,THRESHOLDS,STRUCTURES,HORIZONS,NULL_SEEDS,enrich,build_signals
import pandas as pd
def test_frozen_grid():
    assert len(FEATURES)*len(THRESHOLDS)*len(STRUCTURES)*len(HORIZONS)==16
    assert NULL_SEEDS==(101,202,303,404,505)
def test_enrich():
    x=pd.DataFrame({"GLOBAL_LEAD":[-2,.5],"US_LEAD":[1,-1],"ASIA_LEAD":[-1,.5]})
    y=enrich(x)
    assert list(y.GLOBAL_ABS)==[2,.5]
    assert list(y.US_ASIA_DISPERSION)==[2,1.5]
def test_null_shuffle_changes_feature_series():
    x=pd.DataFrame({"date":pd.date_range("2026-01-01",periods=4),"GLOBAL_ABS":[1,2,3,4],"US_ASIA_DISPERSION":[2,3,4,5]})
    x["open_px"]=100; x["close_px"]=100; x["all_prior"]=True
    s=build_signals(x,null_seed=101)
    assert set(s.threshold.unique())=={1.0,1.5}
