def test_opening_location_states():
    def b(open_px,hi,lo):
        return "ABOVE_RANGE" if open_px>hi else ("BELOW_RANGE" if open_px<lo else "INSIDE_RANGE")
    assert b(105,100,95)=="ABOVE_RANGE"
    assert b(94,100,95)=="BELOW_RANGE"
    assert b(97,100,95)=="INSIDE_RANGE"
