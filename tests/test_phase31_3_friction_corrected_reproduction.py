from pathlib import Path
import importlib.util

p=Path("research/phase31_3_friction_corrected_reproduction.py")
spec=importlib.util.spec_from_file_location("r",p)
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

def test_strategy_and_cost_identity_source():
    s=p.read_text()
    assert 'execution_gross-transaction_costs' in s
    assert 'total_friction' in s
    assert 'slippage_cost' in s

def test_lot_schedule():
    assert m.lot_size("2024-04-25")==50
    assert m.lot_size("2024-04-26")==25
    assert m.lot_size("2024-11-21")==75
    assert m.lot_size("2026-01-06")==65
