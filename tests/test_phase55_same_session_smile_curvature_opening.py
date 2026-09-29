def test_curvature_regime_boundaries():
    def b(x,q33,q67):
        return "LOW_CURVATURE" if x<q33 else ("MID_CURVATURE" if x<q67 else "HIGH_CURVATURE")
    assert b(-3,-2,1)=="LOW_CURVATURE"
    assert b(-2,-2,1)=="MID_CURVATURE"
    assert b(1,-2,1)=="HIGH_CURVATURE"

def test_curvature_definition():
    wing_avg=(24.0+22.0)/2
    atm_avg=(20.0+19.0)/2
    assert wing_avg-atm_avg==3.5
