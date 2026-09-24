from research.phase16_iv_skew_tail_credit import variant_grid

def test_grid_count():
    assert len(variant_grid("WEEK")) == 288

def test_grid_sides_and_widths():
    g=variant_grid("WEEK")
    assert {x["side"] for x in g} == {"PUT","CALL"}
    assert {x["width"] for x in g} == {1,2}


def test_feature_query_combines_put_and_call_skew_legs():
    from research.phase16_iv_skew_tail_credit import feature_query
    q = feature_query(__import__("pathlib").Path("/tmp"), "WEEK")
    assert "GROUP BY datetime,trade_date,expiry_type" in q
    assert "put_iv" in q and "call_iv" in q
