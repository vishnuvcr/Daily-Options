from research.contracts import nifty_lot_size
from research.phase3g_oi_confirmed_breakout import parameter_grid


def test_phase3g_grid_size():
    grid = parameter_grid()
    assert len(grid) == 128
    assert {v.lookback for v in grid} == {15, 30}
    assert {v.oi_window for v in grid} == {3, 5}
    assert {v.oi_threshold for v in grid} == {0.01, 0.02}
    assert {v.expiry_type for v in grid} == {"WEEK", "MONTH"}
    assert {v.width_steps for v in grid} == {1, 2}
    assert {v.hold_minutes for v in grid} == {60, 90}


def test_lot_size_transition():
    assert nifty_lot_size("2025-12-30") == 75
    assert nifty_lot_size("2026-01-06") == 65
