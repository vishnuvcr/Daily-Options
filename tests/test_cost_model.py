from research.cost_model import OptionCostModel

def test_cost_is_positive():
    m = OptionCostModel()
    assert m.round_trip_cost(100, 110, 1, 65) > 0

def test_profitable_trade_net_less_than_gross():
    m = OptionCostModel()
    gross = (110 - 100) * 65
    net = m.net_pnl(100, 110, 1, 65)
    assert net < gross

def test_loss_trade_remains_loss():
    m = OptionCostModel()
    assert m.net_pnl(100, 90, 1, 65) < 0
