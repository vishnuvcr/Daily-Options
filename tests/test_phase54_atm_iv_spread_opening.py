def test_spread_regime_boundaries():
    def b(x,q33,q67):
        return "LOW_SPREAD" if x<q33 else ("MID_SPREAD" if x<q67 else "HIGH_SPREAD")
    assert b(-1.0,0.0,1.0)=="LOW_SPREAD"
    assert b(0.0,0.0,1.0)=="MID_SPREAD"
    assert b(1.0,0.0,1.0)=="HIGH_SPREAD"

def test_spread_sign():
    assert 0.18-0.12 > 0
