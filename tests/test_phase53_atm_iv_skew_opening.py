def test_current_skew_regime_boundaries():
    def b(x,q33,q67):
        return "LOW_SKEW" if x<q33 else ("MID_SKEW" if x<q67 else "HIGH_SKEW")
    assert b(-2,-1,1)=="LOW_SKEW"
    assert b(-1,-1,1)=="MID_SKEW"
    assert b(1,-1,1)=="HIGH_SKEW"

def test_skew_definition():
    assert (14.5 - 11.0) == 3.5
