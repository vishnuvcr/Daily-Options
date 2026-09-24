from research.phase16_iv_skew_tail_credit import variant_grid

def test_grid_count():
    assert len(variant_grid("WEEK")) == 288

def test_grid_sides_and_widths():
    g=variant_grid("WEEK")
    assert {x["side"] for x in g} == {"PUT","CALL"}
    assert {x["width"] for x in g} == {1,2}


def test_feature_query_combines_put_and_call_skew_legs(tmp_path):
    from research.phase16_iv_skew_tail_credit import feature_query
    expiry = "WEEK"
    for name in [
        "ATM+2_CE.parquet","ATM+2_PE.parquet",
        "ATM-2_CE.parquet","ATM-2_PE.parquet",
        "ATM+3_CE.parquet","ATM+3_PE.parquet",
        "ATM-3_CE.parquet","ATM-3_PE.parquet",
        "ATM+4_CE.parquet","ATM+4_PE.parquet",
        "ATM-4_CE.parquet","ATM-4_PE.parquet",
    ]:
        (tmp_path / expiry / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / expiry / name).write_bytes(b"")
    q = feature_query(tmp_path, expiry)
    assert "GROUP BY datetime, trade_date, expiry_type" in q
    assert "put_iv" in q and "call_iv" in q


def test_feature_query_keeps_dense_lookback_before_entry_filter(tmp_path):
    from research.phase16_iv_skew_tail_credit import feature_query
    for name in [
        "ATM+2_CE.parquet","ATM+2_PE.parquet","ATM-2_CE.parquet","ATM-2_PE.parquet",
        "ATM+3_CE.parquet","ATM+3_PE.parquet","ATM-3_CE.parquet","ATM-3_PE.parquet",
        "ATM+4_CE.parquet","ATM+4_PE.parquet","ATM-4_CE.parquet","ATM-4_PE.parquet",
    ]:
        p = tmp_path / "WEEK" / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"")
    q = feature_query(tmp_path, "WEEK")
    assert "BETWEEN '09:30:00' AND '10:30:00'" in q
    assert "LAG(spot,15)" in q
    assert "IN ('09:45:00','10:00:00','10:15:00')" in q
