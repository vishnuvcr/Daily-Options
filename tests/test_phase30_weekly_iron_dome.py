from datetime import date
import pandas as pd

from research.phase30_weekly_iron_dome import (
    cell_id,
    lot_size,
    max_loss_budget,
    nearest_strike,
)


def test_cell_count_and_ids():
    ids = {
        cell_id(e, t, a)
        for e in (-4, -3, -2)
        for t in ("WING_60", "RISK_60")
        for a in ("RECENTER_BOTH", "ONE_STRIKE_INSIDE")
    }
    assert len(ids) == 12


def test_historical_nifty_lot_schedule():
    assert lot_size(date(2025, 12, 30)) == 75
    assert lot_size(date(2026, 1, 6)) == 65


def test_nearest_strike_uses_50_point_grid():
    assert nearest_strike(23812.0) == 23800
    assert nearest_strike(23838.0) == 23850


def test_max_loss_budget_is_positive():
    positions = [
        type("P", (), {"side": "SHORT", "strike": 23800, "option_type": "CE", "qty": 65, "entry_price": 120.0}),
        type("P", (), {"side": "SHORT", "strike": 23800, "option_type": "PE", "qty": 65, "entry_price": 130.0}),
        type("P", (), {"side": "LONG", "strike": 24000, "option_type": "CE", "qty": 65, "entry_price": 40.0}),
        type("P", (), {"side": "LONG", "strike": 23600, "option_type": "PE", "qty": 65, "entry_price": 35.0}),
    ]
    assert max_loss_budget(positions, date(2026, 5, 5), 0.0) > 0
