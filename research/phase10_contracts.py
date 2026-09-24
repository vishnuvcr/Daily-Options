
from __future__ import annotations

from datetime import date

import pandas as pd


def index_option_lot_size(symbol: str, expiry: date | str | pd.Timestamp) -> int:
    """Historical NSE index-option lot size by contract expiry.

    Based on NSE lot-size revision circulars used by this research phase.
    The function is contract-expiry aware because historical contracts can
    retain an older lot size after a new lot size has been announced.
    """
    d = pd.Timestamp(expiry).date()
    symbol = symbol.upper()

    if symbol == "NIFTY":
        if d < date(2021, 7, 1):
            return 75
        if d < date(2024, 4, 26):
            return 50
        if d < date(2024, 11, 21):
            return 25
        if d < date(2026, 1, 6):
            return 75
        return 65

    if symbol == "BANKNIFTY":
        if d < date(2023, 7, 1):
            return 25
        if d < date(2024, 11, 21):
            return 15
        if d < date(2025, 4, 25):
            return 30
        if d < date(2026, 1, 6):
            return 35
        return 30

    raise ValueError(f"Unsupported index symbol: {symbol}")
