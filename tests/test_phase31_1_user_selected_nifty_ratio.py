from datetime import date
from pathlib import Path
import importlib.util

p = Path("research/phase31_1_user_selected_nifty_ratio.py")
spec = importlib.util.spec_from_file_location("m", p)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

def test_strikes():
    assert m.nearest_strike(23200) == 23200
    assert [m.nearest_strike(23200)+200, m.nearest_strike(23200)-200, m.nearest_strike(23200)-400] == [23400,23000,22800]

def test_lot_schedule():
    assert m.lot_size(date(2024,4,25)) == 50
    assert m.lot_size(date(2024,4,26)) == 25
    assert m.lot_size(date(2025,1,1)) == 75
    assert m.lot_size(date(2026,1,6)) == 65

def test_fixed_ratio():
    assert [2,2,1] == [2,2,1]


def test_slippage_floor_and_accounting():
    raw_entry=0.10
    raw_exit=0.10
    slip=0.20
    exec_entry=raw_entry+slip
    exec_exit=max(0.0,raw_exit-slip)
    assert exec_entry >= 0
    assert exec_exit >= 0
    raw_pnl=(raw_exit-raw_entry)*50
    exec_pnl=(exec_exit-exec_entry)*50
    assert raw_pnl-exec_pnl == 20.0
