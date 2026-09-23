from research.contracts import nifty_lot_size
from research.phase3h_option_lead_lag import (
    HOLDS,
    LOOKBACKS,
    PRESSURE_THRESHOLDS,
    WIDTHS,
    parameter_grid,
)


def test_phase3h_grid_size():
    grid = parameter_grid()
    assert len(grid) == 108
    assert {v.lookback for v in grid} == {1, 3, 5}
    assert {v.pressure_threshold for v in grid} == {0.01, 0.02, 0.03}
    assert {v.expiry_type for v in grid} == {"WEEK", "MONTH"}
    assert {v.width_steps for v in grid} == {1, 2}
    assert {v.hold_minutes for v in grid} == {5, 10, 15}


def test_phase3h_information_barrier_shape():
    v = parameter_grid()[0]
    assert v.lookback in LOOKBACKS
    assert v.pressure_threshold in PRESSURE_THRESHOLDS
    assert v.width_steps in WIDTHS
    assert v.hold_minutes in HOLDS


def test_lot_size_transition():
    assert nifty_lot_size("2025-12-30") == 75
    assert nifty_lot_size("2026-01-06") == 65
