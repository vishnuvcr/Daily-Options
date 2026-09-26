from datetime import date

from research.phase30_4_bear_put_contract_feasibility import lot_size

def test_historical_nifty_lot_schedule():
    assert lot_size(date(2025, 12, 30)) == 75
    assert lot_size(date(2026, 1, 6)) == 65
