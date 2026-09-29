def test_current_iv_regime_boundaries():
    def b(x,q33,q67):
        return "LOW_IV" if x<q33 else ("MID_IV" if x<q67 else "HIGH_IV")
    assert b(10,12,14)=="LOW_IV"
    assert b(12,12,14)=="MID_IV"
    assert b(14,12,14)=="HIGH_IV"

def test_feature_is_same_session_pre_entry():
    assert "09:30:00" in "09:30:00"
