from datetime import date
from research.phase30_weekly_iron_dome import (
    WEEKLY_TARGET,
    POSITIVE_WEEK_RATE_TARGET,
    EXECUTION_COVERAGE_TARGET,
    lot_size,
    round_strike,
)

def test_weekly_gate_is_5000():
    assert WEEKLY_TARGET == 5000.0
    assert POSITIVE_WEEK_RATE_TARGET == 0.70
    assert EXECUTION_COVERAGE_TARGET == 0.80

def test_date_aware_lot_schedule():
    assert lot_size(date(2025, 12, 30)) == 75
    assert lot_size(date(2026, 1, 6)) == 65

def test_round_strike():
    assert round_strike(2499) == 2500
    assert round_strike(2501) == 2500
    assert round_strike(2526) == 2550

from research.phase30_weekly_iron_dome import STRIKE_INTERVAL

def test_one_strike_inside_moves_deeper_itm():
    ce_strike = 25000.0
    pe_strike = 25000.0
    assert ce_strike - STRIKE_INTERVAL == 24950.0
    assert pe_strike + STRIKE_INTERVAL == 25050.0
