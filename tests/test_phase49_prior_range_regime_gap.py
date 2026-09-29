def test_range_regime_boundaries():
    def b(x,q33,q67):
        return "LOW_RANGE" if x<q33 else ("MID_RANGE" if x<q67 else "HIGH_RANGE")
    assert b(0.01,0.02,0.03)=="LOW_RANGE"
    assert b(0.02,0.02,0.03)=="MID_RANGE"
    assert b(0.03,0.02,0.03)=="HIGH_RANGE"
