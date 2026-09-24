from research.phase10_cross_index import variant_grid, THRESHOLDS, ENTRY_TIMES, EXPIRIES


def test_phase10_variant_count():
    assert len(variant_grid()) == 128
    assert THRESHOLDS == (0.75, 1.25)
    assert ENTRY_TIMES == ("09:45:00", "10:00:00")
    assert EXPIRIES == ("WEEK", "MONTH")


def test_variant_keys_unique():
    keys=[v.key for v in variant_grid()]
    assert len(keys)==len(set(keys))


def test_lot_mapping():
    from research.phase10_contracts import index_option_lot_size
    assert index_option_lot_size("NIFTY","2024-05-30")==25
    assert index_option_lot_size("NIFTY","2024-12-26")==75
    assert index_option_lot_size("BANKNIFTY","2024-12-24")==30
    assert index_option_lot_size("BANKNIFTY","2025-07-31")==35
