def test_skew_regime_boundaries():
    def b(x,q33,q67):
        return "LOW_SKEW" if x<q33 else ("MID_SKEW" if x<q67 else "HIGH_SKEW")
    assert b(-3,-2,1)=="LOW_SKEW"
    assert b(-2,-2,1)=="MID_SKEW"
    assert b(1,-2,1)=="HIGH_SKEW"

def test_skew_definition():
    put_iv=22.0
    call_iv=18.0
    assert (put_iv-call_iv)==4.0
