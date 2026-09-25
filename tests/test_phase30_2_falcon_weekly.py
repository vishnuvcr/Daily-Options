from research.phase30_2_falcon_weekly import variant_grid, lot_size
from datetime import date

def test_variant_grid_is_frozen_270():
    assert len(variant_grid()) == 270

def test_current_lot_schedule():
    assert lot_size(date(2025,12,30)) == 75
    assert lot_size(date(2026,1,6)) == 65
