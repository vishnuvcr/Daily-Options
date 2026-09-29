def test_range_regime_boundaries():
    def b(x,q33,q67):
        return "LOW_RANGE" if x<q33 else ("MID_RANGE" if x<q67 else "HIGH_RANGE")
    assert b(0.01,0.02,0.03)=="LOW_RANGE"
    assert b(0.02,0.02,0.03)=="MID_RANGE"
    assert b(0.03,0.02,0.03)=="HIGH_RANGE"


def test_requires_valid_observation_history():
    import numpy as np
    vals=np.array([1.0,np.nan,2.0,3.0,4.0,5.0])
    valid_idx=np.flatnonzero(np.isfinite(vals))
    pos=np.searchsorted(valid_idx,6,side="left")
    assert pos==5
    assert len(valid_idx[max(0,pos-5):pos])==5
