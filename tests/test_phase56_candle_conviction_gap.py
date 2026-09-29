def test_body_ratio_state_boundaries():
    def b(x,q33,q67):
        return "LOW_CONVICTION" if x<q33 else ("MID_CONVICTION" if x<q67 else "HIGH_CONVICTION")
    assert b(0.10,0.20,0.60)=="LOW_CONVICTION"
    assert b(0.20,0.20,0.60)=="MID_CONVICTION"
    assert b(0.60,0.20,0.60)=="HIGH_CONVICTION"

def test_body_ratio_formula():
    prior_open=100.0
    prior_high=110.0
    prior_low=90.0
    prior_close=106.0
    assert abs((abs(prior_close-prior_open)/(prior_high-prior_low))-0.30)<1e-12
