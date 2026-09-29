def test_same_session_iv_states():
    def b(iv,q33,q67):
        return "LOW_IV" if iv < q33 else ("MID_IV" if iv < q67 else "HIGH_IV")
    assert b(10,15,20)=="LOW_IV"
    assert b(17,15,20)=="MID_IV"
    assert b(25,15,20)=="HIGH_IV"
