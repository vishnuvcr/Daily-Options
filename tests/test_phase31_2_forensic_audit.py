from pathlib import Path
import importlib.util

p=Path("research/phase31_2_forensic_audit.py")
spec=importlib.util.spec_from_file_location("audit",p)
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

def test_lot_schedule_is_date_aware():
    assert m.lot_size("2024-04-25")==50
    assert m.lot_size("2024-04-26")==25
    assert m.lot_size("2024-11-21")==75
    assert m.lot_size("2026-01-06")==65

def test_strike_structure():
    atm=m.nearest_strike(23140.5)
    assert atm==23150
    assert (atm+200,atm-200,atm-400)==(23350,22950,22750)

def test_source_schema_check_detects_known_phase31_1_mismatch():
    x=m.parse_source_mismatch()
    assert x["source_sha256"]
    assert x["aggregates_nonexistent_costs_column"] is True
    assert x["aggregates_transaction_costs"] is False

def test_sample_selection_is_deterministic():
    import pandas as pd
    x=pd.DataFrame({"trade_date":["2021-07-01","2021-07-02","2022-01-01","2023-01-01","2024-01-01","2025-01-01","2026-01-01"]})
    a=m.stratified_sample(x,5)
    b=m.stratified_sample(x,5)
    assert a.trade_date.tolist()==b.trade_date.tolist()
