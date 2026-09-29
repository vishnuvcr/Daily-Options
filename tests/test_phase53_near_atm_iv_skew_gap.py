def test_near_atm_skew_states():
    def b(x,q33,q67):
        return "LOW_SKEW" if x < q33 else ("MID_SKEW" if x < q67 else "HIGH_SKEW")
    assert b(-2,-1,1)=="LOW_SKEW"
    assert b(0,-1,1)=="MID_SKEW"
    assert b(2,-1,1)=="HIGH_SKEW"

def test_near_atm_offsets():
    atm=24000
    assert atm-50==23950
    assert atm+50==24050
