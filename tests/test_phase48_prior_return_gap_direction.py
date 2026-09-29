def test_prior_return_states():
    def b(x):
        if x == 0:
            return None
        return "PRIOR_UP" if x > 0 else "PRIOR_DOWN"
    assert b(0.01)=="PRIOR_UP"
    assert b(-0.01)=="PRIOR_DOWN"
    assert b(0) is None
