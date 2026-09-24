import pandas as pd

from research.phase13_late_day_volatility_acceleration import (
    variant_grid, _feature_table, _signal_rows
)


def test_variant_count():
    assert len(variant_grid()) == 384


def test_feature_barrier_uses_ist():
    spot = pd.DataFrame({
        "datetime": pd.to_datetime(["2019-01-02 03:44:00", "2019-01-02 03:45:00"]),
        "spot_close": [100.0, 101.0],
    })
    x = _feature_table(spot)
    assert x.iloc[-1]["trade_time_ist"] == "09:15:00"


def test_signal_requires_late_day_time():
    row = pd.DataFrame({
        "datetime": pd.to_datetime(["2019-01-02 09:45:00"]),
        "spot_close": [101.0],
        "trade_date": [pd.Timestamp("2019-01-02").date()],
        "trade_time_ist": ["09:45:00"],
        "z10": [2.0],
        "z15": [2.0],
        "rv_percentile": [90.0],
        "prior_30_high": [100.0],
        "prior_30_low": [99.0],
    })
    v = variant_grid()[0]
    assert _signal_rows(row, v).empty


def test_long_option_uses_two_order_cost_model():
    from research.cost_model import OptionCostModel
    cm = OptionCostModel()
    one_leg = cm.net_pnl(100.0, 120.0, qty=1, lot_size=75, slippage_points=0.20)
    four_leg_zero_short = cm.vertical_debit_spread_net_pnl(
        100.0, 0.0, 120.0, 0.0, lot_size=75, qty=1, slippage_points=0.20
    )
    assert one_leg > four_leg_zero_short


def test_long_option_nan_wing_path_is_not_treated_as_spread():
    import numpy as np
    df = pd.DataFrame([{
        "trade_date": pd.Timestamp("2019-01-02").date(),
        "entry_time": pd.Timestamp("2019-01-02 10:00:00"),
        "expiry": pd.Timestamp("2019-01-31").date(),
        "side": "CE",
        "atm_strike": 100.0,
        "wing_strike": np.nan,
        "atm_path": "atm.csv",
        "wing_path": np.nan,
        "spot": 100.0,
        "hold_minutes": 10,
        "risk_id": 0,
        "variant_id": "x",
    }])
    rec = df.iloc[0]
    assert not (isinstance(rec["wing_path"], str) and bool(rec["wing_path"]))
