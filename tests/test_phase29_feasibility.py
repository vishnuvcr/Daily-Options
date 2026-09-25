from research.phase29_feasibility import classify

def test_index_option_families_are_preliminarily_feasible():
    source,status,reason,has_1m=classify("iron_fly")
    assert source == "index_1m"
    assert status == "PRELIMINARY_FEASIBLE"
    assert has_1m is True

def test_stock_option_family_is_data_limited():
    source,status,reason,has_1m=classify("covered_call")
    assert source == "stock_options"
    assert status == "DATA_LIMITED"
    assert has_1m is False

def test_no_family_is_backtest_allowed_here():
    assert classify("unresolved")[1] == "UNRESOLVED"