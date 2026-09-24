import inspect
from datetime import date
from research.phase24_falcon_spread import lot_size, variant_grid, simulate_setup

def test_variant_count_is_frozen():
    assert len(variant_grid()) == 270

def test_historical_nifty_lot_sizes():
    assert lot_size(date(2021, 7, 1)) == 50
    assert lot_size(date(2024, 4, 26)) == 25
    assert lot_size(date(2024, 11, 21)) == 75
    assert lot_size(date(2026, 1, 6)) == 65

def test_ratio_quantities_are_five_to_three():
    src = inspect.getsource(simulate_setup)
    assert '"qty":5' in src
    assert '"qty":3' in src

def test_monday_one_strike_wings():
    src = inspect.getsource(simulate_setup)
    assert 'ce_w = ce[ce > setup["short_ce_strike"]]' in src
    assert 'pe_w = pe[pe < setup["short_pe_strike"]]' in src

def test_current_expiry_calendar_geometry_is_documented_in_simulator():
    from research.phase24_falcon_spread import build_setup
    src = inspect.getsource(build_setup)
    assert 'entry = expiry - 4 sessions' in src
    assert 'adjustment = expiry - 2 sessions' in src
    assert 'exit = expiry - 1 session' in src

def test_costs_include_brokerage_and_stt_and_gst():
    from research.phase24_falcon_spread import cost
    src = inspect.getsource(cost)
    assert '40.0' in src
    assert '0.0015' in src
    assert '0.18' in src

def test_source_primary_premium_is_in_frozen_grid():
    v = variant_grid()
    assert any(x.target_premium == 25.0 for x in v)
    assert any(x.far_mode == 'DIAGONAL_PREMIUM' for x in v)


def test_series_loader_uses_timestamp_range_not_trading_day_filter():
    from research.phase24_falcon_spread import series
    src = inspect.getsource(series)
    assert "CAST(trading_day AS DATE)" not in src
    assert "BETWEEN TIMESTAMP" in src



def test_mark_panel_uses_backward_asof_only():
    from research.phase24_falcon_spread import mark_panel
    import pandas as pd
    a = pd.DataFrame({'ts': pd.to_datetime(['2025-01-01 09:30:00','2025-01-01 09:32:00']), 'close_px':[1.0,3.0]})
    b = pd.DataFrame({'ts': pd.to_datetime(['2025-01-01 09:31:00']), 'close_px':[2.0]})
    out = mark_panel({'a':a,'b':b}, tolerance_minutes=1)
    assert out['b'].tolist() == [2.0]


def test_adjustment_date_is_explicit_in_setup():
    from research.phase24_falcon_spread import build_setup
    src = inspect.getsource(build_setup)
    assert '"adjust_date": adjust_date' in src
    assert '"exit_date": exit_date' in src


def test_no_legacy_friday_variable_in_simulator():
    src = inspect.getsource(simulate_setup)
    assert "{friday}" not in src
