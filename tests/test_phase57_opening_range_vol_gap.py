def test_opening_range_state_boundaries():
    def b(x,q33,q67):
        return "LOW_OPEN_RANGE" if x<q33 else ("MID_OPEN_RANGE" if x<q67 else "HIGH_OPEN_RANGE")
    assert b(0.10,0.20,0.60)=="LOW_OPEN_RANGE"
    assert b(0.20,0.20,0.60)=="MID_OPEN_RANGE"
    assert b(0.60,0.20,0.60)=="HIGH_OPEN_RANGE"

def test_opening_range_window():
    assert "09:15:00" < "09:29:00"
    assert "09:30:00" > "09:29:00"
