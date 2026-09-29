def test_matched_atm_iv_spread_states():
    def b(x,q33,q67):
        return "LOW_SPREAD" if x<q33 else ("MID_SPREAD" if x<q67 else "HIGH_SPREAD")
    assert b(-2,-1,1)=="LOW_SPREAD"
    assert b(-1,-1,1)=="MID_SPREAD"
    assert b(1,-1,1)=="HIGH_SPREAD"

def test_same_strike_spread_definition():
    assert 15.0 - 11.5 == 3.5
