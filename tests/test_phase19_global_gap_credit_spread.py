import inspect
from research.phase19_global_gap_credit_spread import variant_grid

def test_variant_count():
    assert len(variant_grid()) == 512

def test_active_day_metric_and_frozen_grid():
    src = inspect.getsource(__import__("research.phase19_global_gap_credit_spread", fromlist=["run"]))
    assert "mean_active_day_net" in src
    assert ">= 1000" in src

def test_gap_direction_maps_to_credit_side():
    src = inspect.getsource(__import__("research.phase19_global_gap_credit_spread", fromlist=["build_entries"]))
    assert 'side = "PE" if r.gap_return > 0 else "CE"' in src
    assert 'side = "CE" if r.gap_return > 0 else "PE"' in src

def test_exact_expiry_and_three_minute_window():
    src = inspect.getsource(__import__("research.phase19_global_gap_credit_spread", fromlist=["load_quotes"]))
    assert 'o."timestamp">=w.ts' in src
    assert 'o."timestamp"<=w.end_ts' in src

def test_variant_attribution_locks_hold_stop():
    src = inspect.getsource(__import__("research.phase19_global_gap_credit_spread", fromlist=["build_entries"]))
    sim = inspect.getsource(__import__("research.phase19_global_gap_credit_spread", fromlist=["simulate"]))
    assert '"hold": v.hold' in src
    assert '"stop": v.stop' in src
    assert '["trade_date","entry_ts","expiry","side","short_strike","wing_strike","hold","stop"]' in sim
