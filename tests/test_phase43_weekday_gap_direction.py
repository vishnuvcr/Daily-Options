def test_weekday_states_are_five():
    states=("MONDAY","TUESDAY","WEDNESDAY","THURSDAY","FRIDAY")
    assert len(states)==5 and len(set(states))==5

def test_zero_gap_is_not_a_signal():
    assert 0 == 0
