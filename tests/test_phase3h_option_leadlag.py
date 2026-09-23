from research.phase3h_option_leadlag import grid

def test_phase3h_grid_is_bounded():
    g=grid()
    assert len(g)==96
    assert {x["lookback"] for x in g}=={1,3}
    assert {x["persist"] for x in g}=={1,2}
    assert {x["threshold"] for x in g}=={0.001,0.002}
    assert {x["expiry_type"] for x in g}=={"WEEK","MONTH"}
    assert {x["width_steps"] for x in g}=={1,2}
    assert {x["hold_minutes"] for x in g}=={15,30,60}
