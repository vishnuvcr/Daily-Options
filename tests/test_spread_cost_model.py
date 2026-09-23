from research.cost_model import OptionCostModel

def test_vertical_cost_is_lower_than_gross_profit():
    m = OptionCostModel()
    gross = ((15 - 10) + (5 - 2)) * 65
    net = m.vertical_debit_spread_net_pnl(10, 5, 15, 2, 65)
    assert net < gross
