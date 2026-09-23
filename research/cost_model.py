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

    def vertical_debit_spread_net_pnl(self, long_entry: float, short_entry: float, long_exit: float, short_exit: float, lot_size: int, qty: int = 1, slippage_points: float = 0.20) -> float:
        """Net P&L for a long vertical: buy long + sell short, then reverse at exit."""
        multiplier = qty * lot_size
        gross = ((long_exit - long_entry) + (short_entry - short_exit)) * multiplier
        turnover = (long_entry + short_entry + long_exit + short_exit) * multiplier
        brokerage = 4.0 * self.brokerage_per_order
        exchange = turnover * self.exchange_rate
        sebi = turnover * self.sebi_rate
        stt = (short_entry + long_exit) * multiplier * self.stt_sell_rate
        stamp = (long_entry + short_exit) * multiplier * self.stamp_buy_rate
        gst = self.gst_rate * (brokerage + exchange + sebi)
        slippage = 4.0 * slippage_points * multiplier
        return gross - (brokerage + exchange + sebi + stt + stamp + gst + slippage)

    def ironfly_net_pnl(
        self,
        ce_short_entry: float,
        pe_short_entry: float,
        ce_long_entry: float,
        pe_long_entry: float,
        ce_short_exit: float,
        pe_short_exit: float,
        ce_long_exit: float,
        pe_long_exit: float,
        lot_size: int,
        qty: int = 1,
        slippage_points: float = 0.20,
    ) -> float:
        """Net P&L for a four-leg short iron fly, opened and closed intraday."""
        multiplier = qty * lot_size
        entry_credit = ce_short_entry + pe_short_entry - ce_long_entry - pe_long_entry
        exit_mark = ce_short_exit + pe_short_exit - ce_long_exit - pe_long_exit
        gross = (entry_credit - exit_mark) * multiplier

        turnover = (
            ce_short_entry + pe_short_entry + ce_long_entry + pe_long_entry
            + ce_short_exit + pe_short_exit + ce_long_exit + pe_long_exit
        ) * multiplier
        brokerage = 8.0 * self.brokerage_per_order
        exchange = turnover * self.exchange_rate
        sebi = turnover * self.sebi_rate
        stt_sell_value = (
            ce_short_entry + pe_short_entry + ce_long_exit + pe_long_exit
        ) * multiplier
        stamp_buy_value = (
            ce_long_entry + pe_long_entry + ce_short_exit + pe_short_exit
        ) * multiplier
        stt = stt_sell_value * self.stt_sell_rate
        stamp = stamp_buy_value * self.stamp_buy_rate
        gst = self.gst_rate * (brokerage + exchange + sebi)
        slippage = 8.0 * slippage_points * multiplier
        return gross - (brokerage + exchange + sebi + stt + stamp + gst + slippage)

    def short_straddle_net_pnl(self, call_entry: float, put_entry: float, call_exit: float, put_exit: float, lot_size: int, qty: int = 1, slippage_points: float = 0.20) -> float:
        """Net P&L for short call + short put, opened then closed."""
        multiplier = qty * lot_size
        gross = ((call_entry - call_exit) + (put_entry - put_exit)) * multiplier
        turnover = (call_entry + put_entry + call_exit + put_exit) * multiplier
        brokerage = 4.0 * self.brokerage_per_order
        exchange = turnover * self.exchange_rate
        sebi = turnover * self.sebi_rate
        stt = (call_entry + put_entry) * multiplier * self.stt_sell_rate
        stamp = (call_exit + put_exit) * multiplier * self.stamp_buy_rate
        gst = self.gst_rate * (brokerage + exchange + sebi)
        slippage = 4.0 * slippage_points * multiplier
        return gross - (brokerage + exchange + sebi + stt + stamp + gst + slippage)
