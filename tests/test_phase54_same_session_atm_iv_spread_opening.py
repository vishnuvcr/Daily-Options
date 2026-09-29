def test_spread_regime_boundaries():
    def b(x,q33,q67):
        return "LOW_SPREAD" if x<q33 else ("MID_SPREAD" if x<q67 else "HIGH_SPREAD")
    assert b(-3,-2,1)=="LOW_SPREAD"
    assert b(-2,-2,1)=="MID_SPREAD"
    assert b(1,-2,1)=="HIGH_SPREAD"

def test_matched_atm_spread_definition():
    ce_iv=18.0
    pe_iv=22.0
    assert (ce_iv-pe_iv)==-4.0
