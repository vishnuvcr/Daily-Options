
import inspect
from datetime import date
from research.phase24_falcon_spread_rissin import lot_size, variant_grid, cost, simulate_setup

def test_variant_count_is_frozen():
    assert len(variant_grid()) == 270

def test_current_timing_sequence_is_expiry_relative():
    from research.phase24_falcon_spread_rissin import expiry_setups
    src = inspect.getsource(expiry_setups)
    assert "prior[-4]" in src
    assert "prior[-3]" in src
    assert "prior[-1]" in src

def test_ratio_is_five_to_three():
    src = inspect.getsource(simulate_setup)
    assert '"qty": 5' in src
    assert '"qty": 3' in src

def test_lot_sizes():
    assert lot_size(date(2024, 11, 20)) == 25
    assert lot_size(date(2024, 11, 21)) == 75
    assert lot_size(date(2026, 1, 6)) == 65

def test_cost_model_is_date_aware():
    src = inspect.getsource(cost)
    assert "0.0015" in src
    assert "0.001" in src
    assert "0.000355299" in src
    assert "2026, 4, 1" in src
    assert "2026, 3, 1" in src

def test_no_future_merge():
    from research.phase24_falcon_spread_rissin import mark_panel
    src = inspect.getsource(mark_panel)
    assert 'direction="backward"' in src
    assert 'tolerance=pd.Timedelta(minutes=tolerance_minutes)' in src
