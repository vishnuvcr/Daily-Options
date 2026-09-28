import pandas as pd
from research.phase37_global_shock_opening_dislocation import state_from_signs, summarize

def test_state_mapping():
    assert state_from_signs(1.0,0.7) == "CONVERGENT"
    assert state_from_signs(1.0,-0.7) == "DIVERGENT"
    assert state_from_signs(-1.0,-0.7) == "CONVERGENT"
    assert state_from_signs(1.0,0.0) is None

def test_summary_four_cells():
    t=pd.DataFrame([{'state':'CONVERGENT','horizon':'H10_30','day':'2026-01-05','net_pnl':10,'slippage_cost':1,'transaction_costs':2,'raw_gross':13}])
    s=summarize(t)
    assert len(s)==4
    assert set(s.state)=={'CONVERGENT','DIVERGENT'}
    assert set(s.horizon)=={'H10_30','H15_10'}
