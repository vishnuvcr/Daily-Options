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

def test_wednesday_timeout_and_no_thursday_holding():
    src = inspect.getsource(simulate_setup)
    assert 'pd.Timedelta(days=2)' in src
    assert '15:15:00' in src

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
