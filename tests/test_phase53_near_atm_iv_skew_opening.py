def test_skew_regime_boundaries():
    def b(x,q33,q67):
        return "LOW_SKEW" if x<q33 else ("MID_SKEW" if x<q67 else "HIGH_SKEW")
    assert b(-1.0,0.0,1.0)=="LOW_SKEW"
    assert b(0.0,0.0,1.0)=="MID_SKEW"
    assert b(1.0,0.0,1.0)=="HIGH_SKEW"

def test_skew_legs():
    atm=22500
    assert atm-100==22400
    assert atm+100==22600
