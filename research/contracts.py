from __future__ import annotations

from datetime import date, datetime

import pandas as pd


def nifty_lot_size(session_date: date | datetime | str | pd.Timestamp) -> int:
    """NIFTY lot size for the 2025-2026 public sample and current regime.

    NSE changed NIFTY from 75 to 65 for contracts introduced after the
    December 2025 transition. The exact first revised weekly expiry was
    January 6, 2026; December 2025 contracts retain the old 75-lot basis.
    """
    d = pd.Timestamp(session_date).date()
    return 75 if d <= date(2025, 12, 30) else 65
