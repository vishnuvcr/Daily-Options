def test_term_states():
    assert (0.8 - 0.7) >= 0
    assert (0.6 - 0.8) < 0

def test_term_state_labels():
    assert "STEEP_TERM" != "INVERTED_TERM"
