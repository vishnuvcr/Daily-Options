from research.phase15_vrp_jump_brake_short_vol import variant_grid

def test_grid_count():
    assert len(variant_grid()) == 288

def test_grid_dimensions():
    g=variant_grid()
    assert {x['vrp_threshold'] for x in g}=={0.0,2.0,4.0}
    assert {x['jump_max'] for x in g}=={0.0025,0.0040}
    assert {x['structure'] for x in g}=={'STRADDLE','IRONFLY'}
    assert {x['expiry_type'] for x in g}=={'WEEK','MONTH'}
