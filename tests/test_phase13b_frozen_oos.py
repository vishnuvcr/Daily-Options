from research.phase13b_frozen_oos import SIGNAL_TIME, Z_THRESHOLD, RV_PERCENTILE, HOLD_MINUTES

def test_frozen_rule_constants():
    assert SIGNAL_TIME == '14:45:00'
    assert Z_THRESHOLD == 1.5
    assert RV_PERCENTILE == 80.0
    assert HOLD_MINUTES == 10
# frozen-oos trigger checkpoint 2026-09-24
