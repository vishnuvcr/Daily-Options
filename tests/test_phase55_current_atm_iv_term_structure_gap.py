def test_term_states():
    def b(x):
        return "STEEP_TERM" if x >= 0 else "INVERTED_TERM"
    assert b(0)=="STEEP_TERM"
    assert b(1.2)=="STEEP_TERM"
    assert b(-0.1)=="INVERTED_TERM"
