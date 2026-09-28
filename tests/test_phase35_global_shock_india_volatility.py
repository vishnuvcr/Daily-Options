import pandas as pd
from research.phase35_global_shock_india_volatility import summarize

def test_frozen_four_cells():
    t=pd.DataFrame([
      {'state':'LOW_VOL_STATE','horizon':'H10_30','day':'2026-01-05','net_pnl':10,'slippage_cost':1,'transaction_costs':2,'raw_gross':13},
      {'state':'HIGH_VOL_STATE','horizon':'H15_10','day':'2026-01-06','net_pnl':-5,'slippage_cost':1,'transaction_costs':2,'raw_gross':-2}])
    s=summarize(t)
    assert len(s)==4
    assert set(s.state)=={'LOW_VOL_STATE','HIGH_VOL_STATE'}
    assert set(s.horizon)=={'H10_30','H15_10'}

def test_promotion_gate_constants():
    p=open('docs/phase35_plan.md',encoding='utf-8').read()
    assert 'IV_RV_Z' in p and 'GLOBAL_LEAD' in p and '₹5,000' in p
