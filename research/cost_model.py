from dataclasses import dataclass

@dataclass(frozen=True)
class OptionCostModel:
    brokerage_per_order: float = 20.0
    exchange_rate: float = 0.0003503
    sebi_rate: float = 0.000001
    stt_sell_rate: float = 0.0015
    stamp_buy_rate: float = 0.00003
    gst_rate: float = 0.18

    def round_trip_cost(self, buy_premium: float, sell_premium: float, qty: int, lot_size: int,
                        slippage_points: float = 0.20) -> float:
        buy_value = buy_premium * qty * lot_size
        sell_value = sell_premium * qty * lot_size
        brokerage = 2.0 * self.brokerage_per_order
        exchange = (buy_value + sell_value) * self.exchange_rate
        sebi = (buy_value + sell_value) * self.sebi_rate
        stt = sell_value * self.stt_sell_rate
        stamp = buy_value * self.stamp_buy_rate
        gst = self.gst_rate * (brokerage + exchange + sebi)
        slippage = slippage_points * 2.0 * qty * lot_size
        return brokerage + exchange + sebi + stt + stamp + gst + slippage

    def net_pnl(self, buy_premium: float, sell_premium: float, qty: int, lot_size: int,
                slippage_points: float = 0.20) -> float:
        gross = (sell_premium - buy_premium) * qty * lot_size
        return gross - self.round_trip_cost(
            buy_premium, sell_premium, qty, lot_size, slippage_points
        )
