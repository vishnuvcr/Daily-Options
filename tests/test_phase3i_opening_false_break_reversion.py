from research.contracts import nifty_lot_size
from research.phase3i_opening_false_break_reversion import (
    BREAK_PCTS,
    HOLDS,
    OR_MINUTES,
    REENTRY_PCTS,
    WIDTHS,
    parameter_grid,
)


def test_phase3i_grid_size():
    grid = parameter_grid()
    assert len(grid) == 144
    assert {v.or_minutes for v in grid} == {5, 15, 30}
    assert {v.break_pct for v in grid} == {0.0005, 0.001}
    assert {v.reentry_pct for v in grid} == {0.0002, 0.0005}
    assert {v.expiry_type for v in grid} == {"WEEK", "MONTH"}
    assert {v.width_steps for v in grid} == {1, 2}
    assert {v.hold_minutes for v in grid} == {15, 30, 60}


def test_phase3i_parameter_sets_are_fixed():
    assert OR_MINUTES == (5, 15, 30)
    assert BREAK_PCTS == (0.0005, 0.0010)
    assert REENTRY_PCTS == (0.0002, 0.0005)
    assert WIDTHS == (1, 2)
    assert HOLDS == (15, 30, 60)


def test_lot_size_transition():
    assert nifty_lot_size("2025-12-30") == 75
    assert nifty_lot_size("2026-01-06") == 65
