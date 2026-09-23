from datetime import date
from research.contracts import nifty_lot_size
from research.short_straddle_grid import Config

def test_nifty_lot_transition():
    assert nifty_lot_size(date(2025, 12, 30)) == 75
    assert nifty_lot_size(date(2025, 12, 31)) == 65

def test_config():
    c=Config(30,1.6,0.35,90,0.005,0.003,0.02)
    assert c.entry_minutes == 30
    assert c.stop_mult == 1.6
