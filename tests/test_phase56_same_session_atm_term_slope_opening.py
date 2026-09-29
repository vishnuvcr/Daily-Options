def test_term_slope_boundaries():
    def b(x,q33,q67):
        return "LOW_TERM_SLOPE" if x<q33 else ("MID_TERM_SLOPE" if x<q67 else "HIGH_TERM_SLOPE")
    assert b(-3,-2,1)=="LOW_TERM_SLOPE"
    assert b(-2,-2,1)=="MID_TERM_SLOPE"
    assert b(1,-2,1)=="HIGH_TERM_SLOPE"

def test_term_slope_definition():
    front=19.5
    second=17.0
    assert front-second==2.5
