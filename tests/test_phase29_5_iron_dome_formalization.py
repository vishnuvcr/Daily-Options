from datetime import date
from research.phase29_5_iron_dome_formalization import build_matrix, lot_size, next_tuesday


def test_matrix_has_exactly_12_frozen_cells():
    cells = build_matrix()
    assert len(cells) == 12
    assert len({c["cell_id"] for c in cells}) == 12
    assert {c["entry_offset_trading_sessions"] for c in cells} == {-4, -3, -2}
    assert {c["trigger"] for c in cells} == {"WING_60", "RISK_60"}
    assert {c["adjustment"] for c in cells} == {"RECENTER_BOTH", "ONE_STRIKE_INSIDE"}


def test_current_iron_dome_video_dates_are_tuesday_expiry_regime():
    assert next_tuesday(date(2026, 4, 30)) == date(2026, 5, 5)
    assert next_tuesday(date(2026, 5, 2)) == date(2026, 5, 5)


def test_historical_nifty_lot_schedule():
    assert lot_size(date(2025, 12, 30)) == 75
    assert lot_size(date(2026, 1, 6)) == 65


def test_weekly_target_gate_is_fixed_for_equity_income():
    from research.phase29_5_iron_dome_formalization import (
        WEEKLY_NET_TARGET,
        POSITIVE_WEEK_RATE_TARGET,
        EXECUTED_WEEK_COVERAGE_TARGET,
    )
    assert WEEKLY_NET_TARGET == 5000
    assert POSITIVE_WEEK_RATE_TARGET == 0.70
    assert EXECUTED_WEEK_COVERAGE_TARGET == 0.80
