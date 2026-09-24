from research.phase16_iv_skew_tail_credit import variant_grid

def test_grid_count():
    assert len(variant_grid("WEEK")) == 288

def test_grid_sides_and_widths():
    g=variant_grid("WEEK")
    assert {x["side"] for x in g} == {"PUT","CALL"}
    assert {x["width"] for x in g} == {1,2}
