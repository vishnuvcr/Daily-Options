def test_curvature_regime_boundaries():
    def b(x,q33,q67):
        return "LOW_CURVATURE" if x<q33 else ("MID_CURVATURE" if x<q67 else "HIGH_CURVATURE")
    assert b(-1.0,0.0,1.0)=="LOW_CURVATURE"
    assert b(0.0,0.0,1.0)=="MID_CURVATURE"
    assert b(1.0,0.0,1.0)=="HIGH_CURVATURE"

def test_curvature_formula():
    wing_avg=(0.24+0.22)/2
    atm=0.18
    assert round(wing_avg-atm,6)==0.05
