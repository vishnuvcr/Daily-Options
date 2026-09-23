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


def test_four_leg_defined_structure_cost_model():
    cm = OptionCostModel()
    gross = ((55 - 10 - 20 + 10) - (50 - 20 - 25 + 15)) * 65
    net = cm.four_leg_defined_net_pnl(
        50, 20, 25, 15,
        55, 10, 20, 10,
        lot_size=65,
        leg_signs=(1, -1, -1, 1),
        slippage_points=0.20,
    )
    assert net < gross
    assert net == cm.four_leg_defined_net_pnl(
        50, 20, 25, 15,
        55, 10, 20, 10,
        lot_size=65,
        leg_signs=(1, -1, -1, 1),
        slippage_points=0.20,
    )
