import pandas as pd
from research.phase36_global_shock_breadth import breadth_state, summarize

def test_breadth_state():
    assert breadth_state([1,1,1,1,-1,-1]) == "BROAD_SHOCK"
    assert breadth_state([1,1,1,-1,-1,-1]) == "SPLIT_SHOCK"
    assert breadth_state([-1,-1,-1,-1,1,1]) == "BROAD_SHOCK"

def test_summary_has_four_cells():
    t=pd.DataFrame([{'state':'BROAD_SHOCK','horizon':'H10_30','day':'2026-01-05','net_pnl':10,'slippage_cost':1,'transaction_costs':2,'raw_gross':13}])
    s=summarize(t)
    assert len(s)==4
    assert set(s.state)=={'BROAD_SHOCK','SPLIT_SHOCK'}
    assert set(s.horizon)=={'H10_30','H15_10'}
