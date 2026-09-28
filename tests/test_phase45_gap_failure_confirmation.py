def test_confirmation_states():
    def state(gap, early):
        if abs(gap)<0.005: return 'NO_CONFIRMATION'
        if (gap>0 and early>=0) or (gap<0 and early<=0): return 'GAP_CONTINUATION'
        return 'GAP_FAILURE'
    assert state(0.006,0.001)=='GAP_CONTINUATION'
    assert state(0.006,-0.001)=='GAP_FAILURE'
    assert state(-0.006,-0.001)=='GAP_CONTINUATION'
    assert state(-0.006,0.001)=='GAP_FAILURE'
    assert state(0.004,0.001)=='NO_CONFIRMATION'
