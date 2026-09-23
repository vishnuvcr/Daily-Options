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


def test_ironfly_cost_has_eight_orders_and_capital_friction():
    cm = OptionCostModel()
    net = cm.ironfly_net_pnl(
        100, 100, 20, 20,
        50, 50, 10, 10,
        lot_size=75,
        slippage_points=0.20,
    )
    gross = ((100 + 100 - 20 - 20) - (50 + 50 - 10 - 10)) * 75
    assert net < gross
    assert net == gross - (
        8 * cm.brokerage_per_order
        + ((100+100+20+20+50+50+10+10)*75) * cm.exchange_rate
        + ((100+100+20+20+50+50+10+10)*75) * cm.sebi_rate
        + ((100+100+10+10)*75) * cm.stt_sell_rate
        + ((20+20+50+50)*75) * cm.stamp_buy_rate
        + cm.gst_rate * (
            8 * cm.brokerage_per_order
            + ((100+100+20+20+50+50+10+10)*75) * cm.exchange_rate
            + ((100+100+20+20+50+50+10+10)*75) * cm.sebi_rate
        )
        + 8 * 0.20 * 75
    )
